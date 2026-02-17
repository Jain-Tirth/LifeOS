"""
Helper module for agents to save their responses to the database
Provides a unified interface for saving different types of agent outputs
"""
from agents.models import (
    AgentSession,
    MealPlan,
    Task,
    StudySession,
    WellnessActivity,
    User
)
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class AgentSaveHelper:
    """
    Helper class for agents to save their outputs to the database
    Provides methods for each agent type and handles validation
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
        Save a meal plan from agent output
        
        Args:
            data: Dictionary containing meal plan data
            session: AgentSession object (optional)
            session_id: Session UUID string (optional, if session not provided)
            user: User object (optional)
            
        Returns:
            MealPlan object if successful, None otherwise
        """
        try:
            # Get session if session_id provided
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)
            
            # Prepare meal plan data
            meal_plan_data = {
                'date': data.get('date'),
                'meal_type': data.get('meal_type', 'dinner'),
                'meal_name': data.get('meal_name', data.get('name', 'Unnamed Meal')),
                'ingredients': data.get('ingredients'),
                'instructions': data.get('instructions', data.get('content')),
                'nutritional_info': data.get('nutritional_info'),
                'preferences': data.get('preferences'),
                'session': session,
                'user': user
            }
            
            meal_plan = MealPlan.objects.create(**meal_plan_data)
            logger.info(f"Meal plan saved successfully: {meal_plan.id}")
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
        Save a task from agent output
        
        Args:
            data: Dictionary containing task data
            session: AgentSession object (optional)
            session_id: Session UUID string (optional, if session not provided)
            user: User object (optional)
            
        Returns:
            Task object if successful, None otherwise
        """
        try:
            # Get session if session_id provided
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)
            
            # Prepare task data
            task_data = {
                'title': data.get('title', 'Unnamed Task'),
                'description': data.get('description', data.get('content')),
                'priority': data.get('priority', 'medium'),
                'status': data.get('status', 'todo'),
                'due_date': data.get('due_date'),
                'session': session,
                'user': user
            }
            
            task = Task.objects.create(**task_data)
            logger.info(f"Task saved successfully: {task.id}")
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
        Save a study session from agent output
        
        Args:
            data: Dictionary containing study session data
            session: AgentSession object (optional)
            session_id: Session UUID string (optional, if session not provided)
            user: User object (optional)
            
        Returns:
            StudySession object if successful, None otherwise
        """
        try:
            # Get session if session_id provided
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)
            
            # Prepare study session data
            study_data = {
                'subject': data.get('subject', 'General Study'),
                'topic': data.get('topic'),
                'duration': data.get('duration', 60),
                'notes': data.get('notes', data.get('content')),
                'resources': data.get('resources'),
                'session': session,
                'user': user
            }
            
            study_session = StudySession.objects.create(**study_data)
            logger.info(f"Study session saved successfully: {study_session.id}")
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
        Save a wellness activity from agent output
        
        Args:
            data: Dictionary containing wellness activity data
            session: AgentSession object (optional)
            session_id: Session UUID string (optional, if session not provided)
            user: User object (optional)
            
        Returns:
            WellnessActivity object if successful, None otherwise
        """
        try:
            # Get session if session_id provided
            if not session and session_id:
                session = AgentSaveHelper.get_session(session_id)
            
            # Prepare wellness activity data
            from datetime import datetime
            
            activity_data = {
                'activity_type': data.get('activity_type', 'exercise'),
                'duration': data.get('duration'),
                'intensity': data.get('intensity'),
                'notes': data.get('notes', data.get('content')),
                'metadata': data.get('metadata'),
                'recorded_at': data.get('recorded_at', datetime.now()),
                'session': session,
                'user': user
            }
            
            wellness_activity = WellnessActivity.objects.create(**activity_data)
            logger.info(f"Wellness activity saved successfully: {wellness_activity.id}")
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
        """
        Auto-route save based on agent type
        
        Args:
            agent_type: Type of agent (meal_planner, productivity, study, wellness)
            data: Dictionary containing output data
            session: AgentSession object (optional)
            session_id: Session UUID string (optional, if session not provided)
            user: User object (optional)
            
        Returns:
            Saved object if successful, None otherwise
        """
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
        """
        Bulk save multiple agent outputs
        
        Args:
            items: List of dicts with 'agent_type' and 'data' keys
            default_session: Default session for all items
            default_user: Default user for all items
            
        Returns:
            Dictionary with saved items and errors
        """
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
            'error_count': len(errors)
        }


# Convenience functions for direct imports
save_meal_plan = AgentSaveHelper.save_meal_plan
save_task = AgentSaveHelper.save_task
save_study_session = AgentSaveHelper.save_study_session
save_wellness_activity = AgentSaveHelper.save_wellness_activity
save_agent_output = AgentSaveHelper.save_agent_output
bulk_save_outputs = AgentSaveHelper.bulk_save_outputs
