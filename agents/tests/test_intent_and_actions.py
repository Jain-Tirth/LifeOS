import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import SimpleTestCase

from agents.services.action_applier import ActionApplier
from agents.services.intent_classifier import IntentClassifier


class IntentClassifierTests(SimpleTestCase):
    def setUp(self):
        self.classifier = IntentClassifier()

    def test_keyword_classifies_execution_agent(self):
        result = asyncio.run(
            self.classifier.classify_intent(
                "Create a task and schedule a calendar event for tomorrow"
            )
        )
        self.assertEqual(result['primary_agent'], 'execution_agent')
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
                        {"action": "create_event", "data": {"title": "Team Sync", "start_time": "2026-05-10T10:00:00Z", "end_time": "2026-05-10T10:30:00Z"}}
          ]
        }
        ```
        """

        actions = self.applier.extract_actions(text)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]['action'], 'create_task')
        self.assertEqual(actions[1]['action'], 'create_event')

    def test_extract_actions_empty_without_json_contract(self):
        actions = self.applier.extract_actions("Just a normal conversational response.")
        self.assertEqual(actions, [])

    def test_sync_email_draft_uses_authenticated_gmail_address(self):
        from agents.services import google_integration as google_mod

        email_model = MagicMock(
            body="Hi Boss,\n\nThe communication feature is finally complete.\n\nThanks!",
            to_address="pkg15006@gmail.com",
            subject="Communication Feature Complete",
            from_address="wrong@example.com",
            message_id=None,
        )

        users_resource = MagicMock()
        users_resource.getProfile.return_value.execute.return_value = {
            'emailAddress': 'pkg15006@gmail.com'
        }
        users_resource.drafts.return_value.create.return_value.execute.return_value = {
            'id': 'draft-123'
        }

        service = MagicMock()
        service.users.return_value = users_resource

        with patch.object(google_mod.google_service, 'creds', object()), \
                patch('agents.services.google_integration.build', return_value=service, create=True):
            draft_id = asyncio.run(google_mod.google_service.sync_email_draft(email_model))

        self.assertEqual(draft_id, 'draft-123')
        raw_message = base64.urlsafe_b64decode(
            users_resource.drafts.return_value.create.call_args.kwargs['body']['message']['raw']
        ).decode()
        self.assertIn('From: pkg15006@gmail.com', raw_message)
        self.assertEqual(email_model.from_address, 'pkg15006@gmail.com')
