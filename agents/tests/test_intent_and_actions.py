import asyncio

from django.test import SimpleTestCase

from agents.services.action_applier import ActionApplier
from agents.services.intent_classifier import IntentClassifier


class IntentClassifierTests(SimpleTestCase):
    def setUp(self):
        self.classifier = IntentClassifier()

    def test_keyword_classifies_habit_coach(self):
        result = asyncio.run(
            self.classifier.classify_intent(
                "Help me build a daily habit streak and keep consistency"
            )
        )
        self.assertEqual(result['primary_agent'], 'habit_coach_agent')
        self.assertGreaterEqual(result['confidence'], 0.35)

    def test_unknown_primary_agent_falls_back(self):
        normalized = self.classifier._normalize_result({
            'primary_agent': 'unknown_agent',
            'confidence': 0.9,
            'reasoning': 'bad model output',
        })
        self.assertEqual(normalized['primary_agent'], self.classifier.DEFAULT_FALLBACK_AGENT)
        self.assertIn('fallback_applied', normalized)


class ActionApplierTests(SimpleTestCase):
    def setUp(self):
        self.applier = ActionApplier()

    def test_extract_actions_from_fenced_json(self):
        text = """
        Here is your plan.
        ```json
        {
          "actions": [
            {"action": "create_task", "data": {"title": "Plan week", "priority": "high"}},
            {"action": "create_habit", "data": {"name": "Morning Walk", "frequency": "daily"}}
          ]
        }
        ```
        """

        actions = self.applier.extract_actions(text)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]['action'], 'create_task')
        self.assertEqual(actions[1]['action'], 'create_habit')

    def test_extract_actions_empty_without_json_contract(self):
        actions = self.applier.extract_actions("Just a normal conversational response.")
        self.assertEqual(actions, [])
