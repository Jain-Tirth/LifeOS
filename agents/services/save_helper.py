"""
Helper module for agents to save their responses to the database
Provides a unified interface for saving different types of agent outputs

Sprint 2: Idempotent saves — deterministic upserts prevent duplicate
writes from retries or stream reconnects.  `update_or_create` is used
with natural-key lookups so the same logical action is safe to call
multiple times.
"""
from agents.models import (
    AgentSession,
    MealPlan,
    Task,
    StudySession,
    WellnessActivity,
    Habit,
    User,
)
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class AgentSaveHelper:
    """
    Helper class for agents to save their outputs to the database.
    Now with idempotent upserts to prevent duplicate writes.
    """

    @staticmethod
    def get_session(session_id: str) -> Optional[AgentSession]:
        """Get AgentSession by session_id (UUID string)"""
        try:
            return AgentSession.objects.get(session_id=session_id)
        except AgentSession.DoesNotExist:
            logger.error(f"Session {session_id} not found")
            return None

    @staticmethod
    def save_meal_plan(
        data: Dict[str, Any],
        session: Optional[AgentSession] = None,
        session_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[MealPlan]:
        """
        Idempotent save — upserts on (user, meal_name, date).
        """
        try:
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)

            meal_name = data.get('meal_name', data.get('name', 'Unnamed Meal'))
            date = data.get('date')

            defaults = {
                'meal_type': data.get('meal_type', 'dinner'),
                'ingredients': data.get('ingredients'),
                'instructions': data.get('instructions', data.get('content')),
                'nutritional_info': data.get('nutritional_info'),
                'preferences': data.get('preferences'),
                'session': session,
            }

            if user and date:
                meal_plan, created = MealPlan.objects.update_or_create(
                    user=user, meal_name=meal_name, date=date,
                    defaults=defaults,
                )
            else:
                defaults['meal_name'] = meal_name
                defaults['date'] = date
                defaults['user'] = user
                meal_plan = MealPlan.objects.create(**defaults)
                created = True

            action = 'created' if created else 'updated'
            logger.info(f"Meal plan {action}: {meal_plan.id}")
            return meal_plan

        except Exception as e:
            logger.error(f"Error saving meal plan: {str(e)}")
            return None

    @staticmethod
    def save_task(
        data: Dict[str, Any],
        session: Optional[AgentSession] = None,
        session_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Task]:
        """
        Idempotent save — upserts on (user, title).

        If a task with the same title already exists for this user,
        the existing record is updated instead of creating a duplicate.
        """
        try:
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)

            title = data.get('title', 'Unnamed Task')
            defaults = {
                'description': data.get('description', data.get('content')),
                'priority': data.get('priority', 'medium'),
                'status': data.get('status', 'todo'),
                'due_date': data.get('due_date'),
                'session': session,
            }

            if user:
                task, created = Task.objects.update_or_create(
                    user=user, title=title, defaults=defaults,
                )
            else:
                defaults['title'] = title
                defaults['user'] = user
                task = Task.objects.create(**defaults)
                created = True

            action = 'created' if created else 'updated'
            logger.info(f"Task {action}: {task.id} — {title}")
            return task

        except Exception as e:
            logger.error(f"Error saving task: {str(e)}")
            return None

    @staticmethod
    def save_study_session(
        data: Dict[str, Any],
        session: Optional[AgentSession] = None,
        session_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[StudySession]:
        """
        Save a study session from agent output.
        Study sessions are append-only (not idempotent) because
        every session is inherently unique.
        """
        try:
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)

            study_data = {
                'subject': data.get('subject', 'General Study'),
                'topic': data.get('topic'),
                'duration': data.get('duration', 60),
                'notes': data.get('notes', data.get('content')),
                'resources': data.get('resources'),
                'session': session,
                'user': user,
            }

            study_session = StudySession.objects.create(**study_data)
            logger.info(f"Study session saved: {study_session.id}")
            return study_session

        except Exception as e:
            logger.error(f"Error saving study session: {str(e)}")
            return None

    @staticmethod
    def save_wellness_activity(
        data: Dict[str, Any],
        session: Optional[AgentSession] = None,
        session_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[WellnessActivity]:
        """
        Save a wellness activity from agent output.
        Activities are append-only (each recording is unique).
        """
        try:
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)

            from datetime import datetime

            activity_data = {
                'activity_type': data.get('activity_type', 'exercise'),
                'duration': data.get('duration'),
                'intensity': data.get('intensity'),
                'notes': data.get('notes', data.get('content')),
                'metadata': data.get('metadata'),
                'recorded_at': data.get('recorded_at', datetime.now()),
                'session': session,
                'user': user,
            }

            wellness_activity = WellnessActivity.objects.create(**activity_data)
            logger.info(f"Wellness activity saved: {wellness_activity.id}")
            return wellness_activity

        except Exception as e:
            logger.error(f"Error saving wellness activity: {str(e)}")
            return None

    @staticmethod
    def save_agent_output(
        agent_type: str,
        data: Dict[str, Any],
        session: Optional[AgentSession] = None,
        session_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> Optional[Any]:
        """Auto-route save based on agent type."""
        agent_type_lower = agent_type.lower()

        if 'meal' in agent_type_lower or 'planner' in agent_type_lower:
            return AgentSaveHelper.save_meal_plan(data, session, session_id, user)
        elif 'productivity' in agent_type_lower or 'task' in agent_type_lower:
            return AgentSaveHelper.save_task(data, session, session_id, user)
        elif 'study' in agent_type_lower or 'buddy' in agent_type_lower:
            return AgentSaveHelper.save_study_session(data, session, session_id, user)
        elif 'wellness' in agent_type_lower:
            return AgentSaveHelper.save_wellness_activity(data, session, session_id, user)
        else:
            logger.error(f"Unknown agent type: {agent_type}")
            return None

    @staticmethod
    def bulk_save_outputs(
        items: List[Dict[str, Any]],
        default_session: Optional[AgentSession] = None,
        default_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Bulk save multiple agent outputs."""
        saved = []
        errors = []

        for idx, item in enumerate(items):
            agent_type = item.get('agent_type')
            data = item.get('data', {})
            session = item.get('session', default_session)
            session_id = item.get('session_id')
            user = item.get('user', default_user)

            if not agent_type:
                errors.append({'index': idx, 'error': 'agent_type required'})
                continue

            try:
                result = AgentSaveHelper.save_agent_output(
                    agent_type, data, session, session_id, user
                )
                if result:
                    saved.append({'index': idx, 'object': result})
                else:
                    errors.append({'index': idx, 'error': 'Failed to save'})
            except Exception as e:
                errors.append({'index': idx, 'error': str(e)})

        return {
            'saved': saved,
            'errors': errors,
            'success_count': len(saved),
            'error_count': len(errors),
        }


# Convenience functions for direct imports
save_meal_plan = AgentSaveHelper.save_meal_plan
save_task = AgentSaveHelper.save_task
save_study_session = AgentSaveHelper.save_study_session
save_wellness_activity = AgentSaveHelper.save_wellness_activity
save_agent_output = AgentSaveHelper.save_agent_output
bulk_save_outputs = AgentSaveHelper.bulk_save_outputs
