"""
Intent classifier for determining user intent and routing to appropriate agents
"""
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from django.conf import settings
from asgiref.sync import sync_to_async
import json
import logging
import os

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Classifies user intent using Gemini AI to route messages to appropriate agents
    """
    
    AGENT_INTENTS = {
        'study_agent': [
            'study',
            'learning',
            'exam preparation',
            'notes',
            'remember',
            'recall',
            'revision',
            'syllabus',
            'summarize',
            'concepts',
            'semantic search',
            'study schedule'
        ],
        'productivity_agent': [
            'task management',
            'scheduling',
            'calendar',
            'goals',
            'deadlines',
            'productivity',
            'time management',
            'project planning',
            'weekly plan',
            'todo',
            'organize work'
        ],
        'wellness_agent': [
            'exercise',
            'meditation',
            'sleep',
            'mood',
            'health',
            'fitness',
            'wellbeing',
            'mental health',
            'habits',
            'routine',
            'streak',
            'wellness tracking'
        ],
        'shopping_agent': [
            'meal planning',
            'recipe suggestions',
            'cooking',
            'food preferences',
            'diet',
            'nutrition',
            'grocery',
            'meal prep',
            'shopping list',
            'budget',
            'expenses',
            'meal budget'
        ]
    }
    
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("No Google API key found. Intent classification will use fallback.")
        else:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    async def classify_intent(
        self, 
        user_message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent and determine which agent(s) should handle the request
        
        Args:
            user_message: The user's message
            conversation_history: Optional conversation context
            
        Returns:
            Dict with primary_agent, confidence, secondary_agents, and reasoning
        """
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
        
        # Create classification prompt
        prompt = f"""Analyze the following user message and classify the intent to route to the appropriate agent.

Available agents and their capabilities:
- study_agent: Learning support, note organization, exam prep, study schedules, concept summarization, semantic search
- productivity_agent: Task management, scheduling, goal setting, calendar integration, time management, progress tracking
- wellness_agent: Exercise tracking, meditation, sleep, mood, health monitoring, habit streaks, wellness routines
- shopping_agent: Meal planning, recipes, nutrition, grocery lists, shopping budgets, expense tracking

User message: "{user_message}"

{f"Conversation context:{context}" if context else ""}

Respond ONLY with valid JSON in this exact format:
{{
    "primary_agent": "agent_name",
    "confidence": 0.95,
    "secondary_agents": ["agent_name"],
    "reasoning": "Brief explanation",
    "is_multi_agent": false
}}

Rules:
- primary_agent must be one of: study_agent, productivity_agent, wellness_agent, shopping_agent
- confidence is 0.0 to 1.0
- secondary_agents is optional array for multi-agent tasks
- is_multi_agent is true if multiple agents needed
"""
        
        try:
            # Generate content synchronously, wrapped for async context
            response = await sync_to_async(self.model.generate_content)(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
            
            result = json.loads(response_text.strip())
            
            # Validate result
            if 'primary_agent' not in result:
                raise ValueError("Missing primary_agent in response")
            
            if result['primary_agent'] not in self.AGENT_INTENTS:
                # Fallback to keyword matching
                return self._fallback_classification(user_message)
            
            logger.info(f"Intent classified: {result['primary_agent']} (confidence: {result.get('confidence', 0)})")
            return result
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            # Fallback to keyword-based classification
            return self._fallback_classification(user_message)
    
    def _fallback_classification(self, user_message: str) -> Dict[str, Any]:
        """
        Fallback keyword-based classification if AI classification fails
        """
        user_message_lower = user_message.lower()
        scores = {}
        
        for agent, keywords in self.AGENT_INTENTS.items():
            score = sum(1 for keyword in keywords if keyword in user_message_lower)
            if score > 0:
                scores[agent] = score
        
        if not scores:
            # Default to planner if no match
            return {
                'primary_agent': 'planner',
                'confidence': 0.3,
                'secondary_agents': [],
                'reasoning': 'Fallback classification - no clear intent detected',
                'is_multi_agent': False
            }
        
        primary_agent = max(scores.items(), key=lambda x: x[1])[0]
        confidence = min(scores[primary_agent] / 3.0, 1.0)  # Normalize
        
        return {
            'primary_agent': primary_agent,
            'confidence': confidence,
            'secondary_agents': [],
            'reasoning': f'Keyword-based fallback classification',
            'is_multi_agent': False
        }


# Singleton instance
intent_classifier = IntentClassifier()
