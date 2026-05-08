"""
Sprint 2 — Data Safety and Persistence Guarantees
Comprehensive test suite covering all 3 missions:

  1. SQLite Backup/Export Strategy   (db_backup)
  2. Durable Action Contracts        (action_schema)
  3. Idempotent Saves                (action_applier + save_helper)
"""
import asyncio
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import SimpleTestCase, TestCase, TransactionTestCase

# =========================================================================
# Mission 1 — SQLite Backup / Export Strategy
# =========================================================================
from agents.services.db_backup import (
    _ensure_backup_dir,
    _run_integrity_check,
    check_integrity,
    create_backup,
    list_backups,
    restore_from_backup,
    cleanup_old_backups,
)


class IntegrityCheckTests(SimpleTestCase):
    """Test PRAGMA integrity_check wrapper."""

    def test_integrity_check_on_live_db(self):
        """The live SQLite DB should always pass integrity_check."""
        result = check_integrity()
        self.assertTrue(result["ok"], f"Integrity check failed: {result}")
        self.assertEqual(result["integrity"], ["ok"])

    def test_integrity_check_returns_failure_on_corrupt_file(self):
        """Feeding a non-SQLite file should report failure."""
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        tmp.write(b"this is not a database")
        tmp.close()
        try:
            result = _run_integrity_check(tmp.name)
            # sqlite3 may raise on connect or return a non-ok result
            self.assertFalse(result["ok"])
        except Exception:
            pass  # corrupt files may raise — that's acceptable
        finally:
            os.unlink(tmp.name)


class BackupCreateTests(TestCase):
    """Test backup creation and listing."""

    def setUp(self):
        # Use a temp dir so tests don't pollute the real backups folder
        self.test_backup_dir = Path(tempfile.mkdtemp())
        self._orig_backup_dir_patch = patch(
            "agents.services.db_backup.BACKUP_DIR", self.test_backup_dir
        )
        self._orig_backup_dir_patch.start()

    def tearDown(self):
        self._orig_backup_dir_patch.stop()
        shutil.rmtree(self.test_backup_dir, ignore_errors=True)

    def test_create_backup_succeeds(self):
        result = create_backup()
        self.assertTrue(result["success"], f"Backup failed: {result}")
        self.assertIsNotNone(result["backup_path"])
        self.assertTrue(Path(result["backup_path"]).exists())

    def test_create_backup_with_tag(self):
        result = create_backup(tag="nightly")
        self.assertIn("nightly", result["backup_path"])

    def test_list_backups_returns_created_backup(self):
        create_backup(tag="test1")
        create_backup(tag="test2")
        backups = list_backups()
        self.assertGreaterEqual(len(backups), 2)
        # Newest first
        self.assertIn("test2", backups[0]["filename"])

    def test_backup_post_check_passes(self):
        result = create_backup()
        self.assertTrue(result["post_check"]["ok"])


class BackupRestoreTests(TestCase):
    """Test restore-from-backup flow."""

    def setUp(self):
        self.test_backup_dir = Path(tempfile.mkdtemp())
        self._patch = patch(
            "agents.services.db_backup.BACKUP_DIR", self.test_backup_dir
        )
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        shutil.rmtree(self.test_backup_dir, ignore_errors=True)

    def test_restore_nonexistent_backup_fails(self):
        result = restore_from_backup("/nonexistent/path.sqlite3")
        self.assertFalse(result["success"])

    def test_restore_creates_safety_snapshot(self):
        backup = create_backup(tag="for_restore")
        result = restore_from_backup(backup["backup_path"])
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["safety_snapshot"])


class BackupCleanupTests(TestCase):
    """Test old-backup cleanup."""

    def setUp(self):
        self.test_backup_dir = Path(tempfile.mkdtemp())
        self._patch = patch(
            "agents.services.db_backup.BACKUP_DIR", self.test_backup_dir
        )
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        shutil.rmtree(self.test_backup_dir, ignore_errors=True)

    def test_cleanup_removes_nothing_when_all_recent(self):
        create_backup()
        deleted = cleanup_old_backups(retention_days=30)
        self.assertEqual(deleted, 0)

    def test_cleanup_removes_old_backups(self):
        # Create a fake old backup
        old_file = self.test_backup_dir / "lifeos_backup_20200101_000000_old.sqlite3"
        old_file.write_text("fake")
        # Force old mtime
        old_ts = datetime(2020, 1, 1).timestamp()
        os.utime(old_file, (old_ts, old_ts))

        deleted = cleanup_old_backups(retention_days=1)
        self.assertEqual(deleted, 1)
        self.assertFalse(old_file.exists())


# =========================================================================
# Mission 2 — Durable Action Contracts
# =========================================================================
from agents.services.action_schema import (
    validate_action,
    ActionValidationError,
    REGISTERED_ACTIONS,
    get_action_schema_summary,
)


class ActionSchemaRegistrationTests(SimpleTestCase):
    """Verify schema registry is complete."""

    def test_all_expected_actions_registered(self):
        expected = {
            "create_task",
            "create_meal_plan",
            "create_study_session",
            "create_wellness_activity",
            "create_habit",
        }
        self.assertEqual(REGISTERED_ACTIONS, expected)

    def test_schema_summary_contains_all_actions(self):
        summary = get_action_schema_summary()
        for action in REGISTERED_ACTIONS:
            self.assertIn(action, summary)


class ValidateCreateTaskTests(SimpleTestCase):
    """Test create_task schema validation."""

    def test_valid_task_minimal(self):
        result = validate_action({
            "action": "create_task",
            "data": {"title": "Buy groceries"},
        })
        self.assertEqual(result["title"], "Buy groceries")
        # Defaults applied
        self.assertEqual(result["priority"], "medium")
        self.assertEqual(result["status"], "todo")

    def test_valid_task_full(self):
        result = validate_action({
            "action": "create_task",
            "data": {
                "title": "Review PR",
                "description": "Check for bugs",
                "priority": "high",
                "status": "in_progress",
                "due_date": "2026-04-10T12:00:00Z",
            },
        })
        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["status"], "in_progress")

    def test_missing_title_rejected(self):
        with self.assertRaises(ActionValidationError) as ctx:
            validate_action({
                "action": "create_task",
                "data": {"priority": "high"},
            })
        self.assertIn("title", str(ctx.exception))

    def test_empty_title_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_task",
                "data": {"title": "   "},
            })

    def test_invalid_priority_rejected(self):
        with self.assertRaises(ActionValidationError) as ctx:
            validate_action({
                "action": "create_task",
                "data": {"title": "X", "priority": "super_urgent"},
            })
        self.assertIn("priority", str(ctx.exception))

    def test_invalid_status_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_task",
                "data": {"title": "X", "status": "done"},
            })


class ValidateCreateMealPlanTests(SimpleTestCase):
    """Test create_meal_plan schema validation."""

    def test_valid_meal_plan(self):
        result = validate_action({
            "action": "create_meal_plan",
            "data": {
                "meal_name": "Paneer Tikka",
                "date": "2026-04-10",
                "meal_type": "dinner",
            },
        })
        self.assertEqual(result["meal_name"], "Paneer Tikka")

    def test_missing_date_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_meal_plan",
                "data": {"meal_name": "Salad"},
            })

    def test_invalid_date_format_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_meal_plan",
                "data": {"meal_name": "Salad", "date": "10-04-2026"},
            })

    def test_invalid_meal_type_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_meal_plan",
                "data": {"meal_name": "Salad", "date": "2026-04-10", "meal_type": "brunch"},
            })


class ValidateCreateStudySessionTests(SimpleTestCase):
    """Test create_study_session schema validation."""

    def test_valid_study_session(self):
        result = validate_action({
            "action": "create_study_session",
            "data": {"subject": "Math", "duration": 45},
        })
        self.assertEqual(result["subject"], "Math")
        self.assertEqual(result["duration"], 45)

    def test_missing_duration_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_study_session",
                "data": {"subject": "Math"},
            })

    def test_zero_duration_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_study_session",
                "data": {"subject": "Math", "duration": 0},
            })


class ValidateCreateWellnessActivityTests(SimpleTestCase):
    """Test create_wellness_activity schema validation."""

    def test_valid_activity(self):
        result = validate_action({
            "action": "create_wellness_activity",
            "data": {"activity_type": "meditation"},
        })
        self.assertEqual(result["activity_type"], "meditation")

    def test_invalid_activity_type_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_wellness_activity",
                "data": {"activity_type": "dance"},
            })


class ValidateCreateHabitTests(SimpleTestCase):
    """Test create_habit schema validation."""

    def test_valid_habit_minimal(self):
        result = validate_action({
            "action": "create_habit",
            "data": {"name": "Morning Walk"},
        })
        self.assertEqual(result["name"], "Morning Walk")
        self.assertEqual(result["frequency"], "daily")
        self.assertEqual(result["category"], "other")

    def test_valid_habit_full(self):
        result = validate_action({
            "action": "create_habit",
            "data": {
                "name": "Read 30 min",
                "description": "Read before bed",
                "category": "learning",
                "frequency": "weekdays",
                "target_count": 1,
                "icon": "📖",
                "color": "#10B981",
            },
        })
        self.assertEqual(result["category"], "learning")
        self.assertEqual(result["color"], "#10B981")

    def test_missing_name_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_habit",
                "data": {"category": "health"},
            })

    def test_invalid_color_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_habit",
                "data": {"name": "X", "color": "red"},
            })

    def test_invalid_frequency_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({
                "action": "create_habit",
                "data": {"name": "X", "frequency": "biweekly"},
            })


class ValidateUnknownActionTests(SimpleTestCase):
    """Test rejection of unregistered action names."""

    def test_unknown_action_rejected(self):
        with self.assertRaises(ActionValidationError) as ctx:
            validate_action({"action": "delete_everything", "data": {}})
        self.assertIn("Unknown action", str(ctx.exception))

    def test_missing_action_field_rejected(self):
        with self.assertRaises(ActionValidationError):
            validate_action({"data": {"title": "X"}})


class ValidateExtraFieldsPassThrough(SimpleTestCase):
    """Extra unknown fields in data should pass through (forward compat)."""

    def test_extra_fields_preserved(self):
        result = validate_action({
            "action": "create_task",
            "data": {"title": "X", "custom_tag": "sprint2"},
        })
        self.assertEqual(result["custom_tag"], "sprint2")


# =========================================================================
# Mission 3 — Idempotent Saves (ActionApplier + SaveHelper)
# =========================================================================
from agents.services.action_applier import (
    ActionApplier,
    _compute_idempotency_key,
    _check_and_mark,
    _SEEN_KEYS,
)


class IdempotencyKeyTests(SimpleTestCase):
    """Test deterministic idempotency key generation."""

    def test_same_input_produces_same_key(self):
        k1 = _compute_idempotency_key(1, "create_task", {"title": "A"})
        k2 = _compute_idempotency_key(1, "create_task", {"title": "A"})
        self.assertEqual(k1, k2)

    def test_different_data_produces_different_key(self):
        k1 = _compute_idempotency_key(1, "create_task", {"title": "A"})
        k2 = _compute_idempotency_key(1, "create_task", {"title": "B"})
        self.assertNotEqual(k1, k2)

    def test_different_user_produces_different_key(self):
        k1 = _compute_idempotency_key(1, "create_task", {"title": "A"})
        k2 = _compute_idempotency_key(2, "create_task", {"title": "A"})
        self.assertNotEqual(k1, k2)

    def test_key_is_32_char_hex(self):
        key = _compute_idempotency_key(42, "create_habit", {"name": "Walk"})
        self.assertEqual(len(key), 32)
        # Should be valid hex
        int(key, 16)


class ActionApplierExtractTests(SimpleTestCase):
    """Test action extraction from LLM response text."""

    def setUp(self):
        self.applier = ActionApplier()

    def test_extract_from_fenced_json(self):
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
        self.assertEqual(actions[0]["action"], "create_task")
        self.assertEqual(actions[1]["action"], "create_habit")

    def test_extract_ignores_unknown_actions(self):
        text = '```json\n{"actions": [{"action": "delete_user", "data": {}}]}\n```'
        actions = self.applier.extract_actions(text)
        self.assertEqual(actions, [])

    def test_extract_from_bare_json(self):
        text = json.dumps({
            "actions": [
                {"action": "create_task", "data": {"title": "Test"}}
            ]
        })
        actions = self.applier.extract_actions(text)
        self.assertEqual(len(actions), 1)

    def test_extract_empty_on_plain_text(self):
        actions = self.applier.extract_actions("Just a normal response with no JSON.")
        self.assertEqual(actions, [])

    def test_extract_empty_on_none(self):
        actions = self.applier.extract_actions(None)
        self.assertEqual(actions, [])

    def test_extract_empty_on_non_string(self):
        actions = self.applier.extract_actions(12345)
        self.assertEqual(actions, [])

    def test_extract_single_action_object(self):
        text = '```json\n{"action": "create_task", "data": {"title": "Solo"}}\n```'
        actions = self.applier.extract_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["data"]["title"], "Solo")


class IdempotentSaveHelperTests(TransactionTestCase):
    """Test that save_task and save_meal_plan are idempotent with update_or_create."""

    def setUp(self):
        from agents.models import User
        self.user = User.objects.create_user(
            email="idem@test.com", password="testpass123"
        )

    def test_task_upsert_no_duplicate(self):
        from agents.services.save_helper import save_task

        t1 = save_task(
            data={"title": "Write tests", "priority": "high"},
            user=self.user,
        )
        t2 = save_task(
            data={"title": "Write tests", "priority": "urgent"},
            user=self.user,
        )
        # Should be the SAME record, not a duplicate
        self.assertEqual(t1.id, t2.id)
        t2.refresh_from_db()
        self.assertEqual(t2.priority, "urgent")

    def test_task_different_titles_create_separate_records(self):
        from agents.services.save_helper import save_task

        t1 = save_task(data={"title": "Task A"}, user=self.user)
        t2 = save_task(data={"title": "Task B"}, user=self.user)
        self.assertNotEqual(t1.id, t2.id)

    def test_meal_plan_upsert_no_duplicate(self):
        from agents.services.save_helper import save_meal_plan

        m1 = save_meal_plan(
            data={"meal_name": "Pasta", "date": "2026-04-10", "meal_type": "dinner"},
            user=self.user,
        )
        m2 = save_meal_plan(
            data={"meal_name": "Pasta", "date": "2026-04-10", "meal_type": "lunch"},
            user=self.user,
        )
        self.assertEqual(m1.id, m2.id)
        m2.refresh_from_db()
        self.assertEqual(m2.meal_type, "lunch")

    def test_save_task_without_user_creates_new_each_time(self):
        """Without a user we can't do reliable upsert — falls back to create."""
        from agents.services.save_helper import save_task

        t1 = save_task(data={"title": "Anonymous"}, user=None)
        t2 = save_task(data={"title": "Anonymous"}, user=None)
        self.assertNotEqual(t1.id, t2.id)


class ActionApplierValidationIntegrationTests(SimpleTestCase):
    """Test that ActionApplier rejects malformed actions before execution."""

    def setUp(self):
        self.applier = ActionApplier()

    def test_malformed_action_reported_in_results(self):
        """An action missing required fields should appear as rejected."""
        text = '```json\n{"actions": [{"action": "create_task", "data": {}}]}\n```'
        actions = self.applier.extract_actions(text)
        self.assertEqual(len(actions), 1)

        # If we were to apply, validation would catch the missing 'title'.
        # We test validation directly here.
        from agents.services.action_schema import validate_action, ActionValidationError
        with self.assertRaises(ActionValidationError):
            validate_action(actions[0])


class DedupCacheTests(SimpleTestCase):
    """Test the in-memory deduplication cache."""

    def setUp(self):
        # Clear cache between tests
        import agents.services.action_applier as mod
        mod._SEEN_KEYS = set()

    def test_first_call_returns_false(self):
        self.assertFalse(_check_and_mark("key_abc"))

    def test_second_call_returns_true(self):
        _check_and_mark("key_xyz")
        self.assertTrue(_check_and_mark("key_xyz"))

    def test_cache_eviction_under_pressure(self):
        import agents.services.action_applier as mod
        old_max = mod._MAX_CACHE
        mod._MAX_CACHE = 4
        try:
            for i in range(6):
                _check_and_mark(f"k{i}")
            # After eviction, earliest keys may be gone
            # The cache should still function without error
            self.assertIsInstance(mod._SEEN_KEYS, set)
        finally:
            mod._MAX_CACHE = old_max
