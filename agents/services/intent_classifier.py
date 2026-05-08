"""
Intent classifier for determining user intent and routing to appropriate agents.
Optimized: keyword-first classification, LLM only for ambiguous cases.
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

    KEYWORD_CONFIDENCE_THRESHOLD = 0.5
    DEFAULT_FALLBACK_AGENT = 'execution_agent'

    AGENT_INTENTS = {
        'execution_agent': [
            'create', 'update', 'edit', 'delete', 'add', 'make', 'do',
            'schedule', 'set up', 'book', 'sync', 'save', 'submit',
            'task', 'event', 'calendar', 'todo', 'action', 'remind',
        ],
        'insight_agent': [
            'insight', 'pattern', 'trend', 'correlate', 'analysis', 'analyze',
            'why', 'what changed', 'suggestion', 'recommend', 'optimize',
            'bottleneck', 'habit trend', 'performance drop', 'signal',
        ],
        'planning_agent': [
            'plan', 'roadmap', 'steps', 'step by step', 'time block',
            'organize', 'prioritize', 'sequence', 'timeline', 'goal', 'goal plan',
            'what should i do next', 'break it down', 'roadmap me',
        ],
        'memory_agent': [
            'remember', 'memory', 'preference', 'routine', 'habit', 'context',
            'recall', 'store', 'what do you know about me', 'profile',
            'my preferences', 'my routine', 'my habits',
        ],
        'communication_agent': [
            'email', 'send an email', 'draft an email', 'gmail', 'inbox',
            'message', 'summarize messages', 'prioritize inbox', 'reply',
            'follow up', 'newsletter', 'communication',
        ],
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
        keyword_result = self._keyword_classification(user_message)

        if keyword_result['confidence'] >= self.KEYWORD_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Intent classified via keywords: {keyword_result['primary_agent']} "
                f"(confidence: {keyword_result['confidence']:.2f})"
            )
            return keyword_result

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

        return keyword_result

    def _keyword_classification(self, user_message: str) -> Dict[str, Any]:
        user_message_lower = user_message.lower()
        scores = {}

        for agent, keywords in self.AGENT_INTENTS.items():
            score = 0
            matched_keywords = []
            for keyword in keywords:
                if keyword in user_message_lower:
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
                'primary_agent': 'execution_agent',
                'confidence': 0.2,
                'secondary_agents': [],
                'reasoning': 'No keyword matches — defaulting to execution',
                'is_multi_agent': False,
                'classification_method': 'keyword_default'
            }

        sorted_agents = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        primary = sorted_agents[0]

        max_possible = 5
        confidence = min(primary[1]['score'] / max_possible, 1.0)

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
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-3:]
            ])

        prompt = f"""Classify this message to one of these agents:
- execution_agent: Create or update tasks/events, talk to APIs, perform actions
- insight_agent: Patterns, trends, correlations, suggestions
- planning_agent: Steps, schedules, goal breakdowns, time optimization
- memory_agent: Preferences, routines, context retrieval
- communication_agent: Emails, inbox prioritization, message summaries

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
            max_tokens=200,
        )

        response_text = chat_completion.choices[0].message.content.strip()

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


intent_classifier = IntentClassifier()