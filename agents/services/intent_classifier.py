"""
Intent classifier for determining user intent and routing to appropriate agents.
Optimized: keyword-first classification, LLM only for ambiguous cases.
This halves API usage since we no longer burn an LLM call for every single message.
"""
from typing import Dict, Any, List, Optional
from groq import Groq
from django.conf import settings
import json
import logging
import os

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user intent using a two-tier approach:
    1. Fast keyword matching (zero API cost, instant)
    2. LLM classification only when keywords are ambiguous (confidence < threshold)
    """
    
    # Confidence threshold: if keyword score is above this, skip the LLM call
    KEYWORD_CONFIDENCE_THRESHOLD = 0.5
    
    # Default agent when LLM returns an unknown/hallucinated agent name
    DEFAULT_FALLBACK_AGENT = 'productivity_agent'

    AGENT_INTENTS = {
        'study_agent': [
            'study', 'learning', 'exam', 'notes', 'remember', 'recall',
            'revision', 'syllabus', 'summarize', 'concepts', 'quiz',
            'flashcard', 'homework', 'assignment', 'lecture', 'chapter',
            'textbook', 'academic', 'semester', 'gpa', 'grade',
            'study schedule', 'study plan', 'study session',
        ],
        'productivity_agent': [
            'task', 'todo', 'to-do', 'scheduling', 'calendar', 'goals',
            'deadline', 'productivity', 'time management', 'project',
            'weekly plan', 'organize', 'prioritize', 'kanban', 'sprint',
            'meeting', 'agenda', 'checklist', 'milestone', 'plan my day',
            'plan my week', 'what should i do', 'schedule',
        ],
        'wellness_agent': [
            'exercise', 'meditation', 'sleep', 'mood', 'health', 'fitness',
            'wellbeing', 'mental health', 'habits', 'routine', 'streak',
            'workout', 'yoga', 'running', 'steps', 'calories burned',
            'stress', 'anxiety', 'mindfulness', 'breathing', 'hydration',
            'water', 'weight', 'body', 'gym', 'cardio', 'stretch',
        ],
        'meal_planner_agent': [
            'meal', 'recipe', 'cooking', 'food', 'diet', 'nutrition',
            'meal prep', 'meal plan', 'breakfast', 'lunch', 'dinner',
            'snack', 'ingredient', 'grocery', 'vegan', 'vegetarian',
            'keto', 'gluten-free', 'protein', 'carb', 'calorie',
            'what should i eat', 'what to cook', 'hungry', 'cook',
        ],
        'habit_coach_agent': [
            'habit', 'streak', 'daily routine', 'build a habit', 'break a habit',
            'track habit', 'habit tracker', 'consistency', 'accountability',
            'morning routine', 'evening routine', 'bedtime routine',
            'new habit', 'stop habit', 'habit stack', 'atomic habits',
            'how many days', 'did i do', 'check in', 'log habit',
        ]
    }
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY') or getattr(settings, 'GROQ_API_KEY', None)
        if not api_key:
            logger.warning("No Groq API key found. Intent classification will use keyword-only mode.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        
        self.model = 'llama-3.3-70b-versatile'
    
    async def classify_intent(
        self, 
        user_message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Two-tier intent classification:
        1. Try keyword matching first (free, instant)
        2. Only call LLM if keyword confidence is too low
        """
        # Tier 1: Keyword classification (always runs)
        keyword_result = self._keyword_classification(user_message)
        
        # If keyword matching is confident enough, use it directly — saves an LLM call
        if keyword_result['confidence'] >= self.KEYWORD_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Intent classified via keywords: {keyword_result['primary_agent']} "
                f"(confidence: {keyword_result['confidence']:.2f})"
            )
            return keyword_result
        
        # Tier 2: LLM classification for ambiguous messages
        if self.client:
            try:
                llm_result = await self._llm_classification(user_message, conversation_history)
                logger.info(
                    f"Intent classified via LLM: {llm_result['primary_agent']} "
                    f"(confidence: {llm_result.get('confidence', 0):.2f})"
                )
                return llm_result
            except Exception as e:
                logger.error(f"LLM classification failed, using keyword fallback: {e}")
        
        # Fallback: return keyword result even if low confidence
        return keyword_result
    
    def _keyword_classification(self, user_message: str) -> Dict[str, Any]:
        """
        Enhanced keyword-based classification with weighted scoring.
        """
        user_message_lower = user_message.lower()
        scores = {}
        
        for agent, keywords in self.AGENT_INTENTS.items():
            score = 0
            matched_keywords = []
            for keyword in keywords:
                if keyword in user_message_lower:
                    # Longer keyword matches are worth more (more specific)
                    weight = len(keyword.split())
                    score += weight
                    matched_keywords.append(keyword)
            
            if score > 0:
                scores[agent] = {
                    'score': score,
                    'matched': matched_keywords
                }
        
        if not scores:
            return {
                'primary_agent': 'productivity_agent',
                'confidence': 0.2,
                'secondary_agents': [],
                'reasoning': 'No keyword matches — defaulting to productivity',
                'is_multi_agent': False,
                'classification_method': 'keyword_default'
            }
        
        # Sort by score
        sorted_agents = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        primary = sorted_agents[0]
        
        # Normalize confidence (cap at 1.0)
        max_possible = 5  # rough max for typical messages
        confidence = min(primary[1]['score'] / max_possible, 1.0)
        
        # Check for multi-agent case (two agents with similar scores)
        secondary = []
        if len(sorted_agents) > 1:
            second = sorted_agents[1]
            if second[1]['score'] >= primary[1]['score'] * 0.6:
                secondary.append(second[0])
        
        return {
            'primary_agent': primary[0],
            'confidence': confidence,
            'secondary_agents': secondary,
            'reasoning': f"Matched keywords: {', '.join(primary[1]['matched'])}",
            'is_multi_agent': len(secondary) > 0,
            'classification_method': 'keyword'
        }
    
    async def _llm_classification(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        LLM-based classification — only called for ambiguous messages.
        """
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in conversation_history[-3:]  # Reduced from 5 to 3 to save tokens
            ])
        
        prompt = f"""Classify this message to one of these agents:
- study_agent: Learning, exams, study schedules, notes
- productivity_agent: Tasks, scheduling, goals, time management
- wellness_agent: Exercise, meditation, sleep, mood, health
- meal_planner_agent: Meals, recipes, nutrition, cooking

Message: "{user_message}"
{f"Recent context: {context}" if context else ""}

Respond ONLY with JSON:
{{"primary_agent": "agent_name", "confidence": 0.95, "reasoning": "brief reason"}}"""
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an intent classifier. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
            temperature=0.1,
            max_tokens=200,  # Reduced from 500
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Clean markdown code blocks
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text.strip())
        
        if 'primary_agent' not in result:
            raise ValueError("Missing primary_agent in LLM response")
        
        result = self._normalize_result(result)
        result['classification_method'] = 'llm'
        result.setdefault('secondary_agents', [])
        result.setdefault('is_multi_agent', False)
        
        return result
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a classification result dict.

        If ``primary_agent`` is not a known agent name the value is
        replaced with ``DEFAULT_FALLBACK_AGENT`` and confidence is
        clamped to 0.3 so downstream consumers know it's a guess.
        """
        if result.get('primary_agent') not in self.AGENT_INTENTS:
            logger.warning(
                "Unknown agent '%s' in classification result — falling back to %s",
                result.get('primary_agent'),
                self.DEFAULT_FALLBACK_AGENT,
            )
            result['primary_agent'] = self.DEFAULT_FALLBACK_AGENT
            result['confidence'] = min(result.get('confidence', 0.3), 0.3)
            result['fallback_applied'] = True
        return result


# Singleton instance
intent_classifier = IntentClassifier()
