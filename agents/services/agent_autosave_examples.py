"""
Example integration showing how agents can automatically save their outputs
This demonstrates best practices for using the save_helper module
"""
from agents.services.save_helper import (
    save_meal_plan,
    save_task,
    save_study_session,
    save_wellness_activity,
    save_agent_output
)
from agents.models import AgentSession, User
import json
import re
from typing import Dict, Any, Optional


class MealPlannerWithAutoSave:
    """
    Example: Meal Planner Agent that automatically saves meal plans to database
    """
    
    async def process_meal_request(
        self,
        user_message: str,
        session: AgentSession,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Process meal planning request and automatically save to database
        """
        # Step 1: Generate meal plan (using your existing agent logic)
        response_text = await self._generate_meal_plan(user_message)
        
        # Step 2: Parse the response to extract structured data
        meal_data = self._parse_meal_plan(response_text)
        
        # Step 3: Save to database
        saved_meal = None
        if meal_data:
            saved_meal = save_meal_plan(
                data=meal_data,
                session=session,
                user=user
            )
        
        # Step 4: Return response with save status
        return {
            'success': True,
            'response': response_text,
            'saved': saved_meal is not None,
            'saved_id': saved_meal.id if saved_meal else None,
            'saved_data': {
                'meal_name': saved_meal.meal_name if saved_meal else None,
                'date': str(saved_meal.date) if saved_meal else None
            }
        }
    
    async def _generate_meal_plan(self, message: str) -> str:
        """Generate meal plan using LLM (replace with actual implementation)"""
        # Your existing agent logic here
        return "Grilled Salmon with Vegetables..."
    
    def _parse_meal_plan(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse meal plan from agent response text
        Extract structured data like meal name, ingredients, instructions
        """
        from datetime import datetime
        
        # Simple parsing logic (enhance based on your agent's output format)
        lines = text.split('\n')
        
        meal_data = {
            'date': datetime.now().date().isoformat(),
            'meal_type': 'dinner',  # Could be extracted from text
            'meal_name': lines[0] if lines else 'Unnamed Meal',
            'instructions': text,
            'ingredients': self._extract_ingredients(text),
        }
        
        return meal_data
    
    def _extract_ingredients(self, text: str) -> list:
        """Extract ingredients list from text"""
        # Simple heuristic - improve based on your needs
        ingredients = []
        for line in text.split('\n'):
            if line.strip().startswith('-') or line.strip().startswith('•'):
                ingredient = line.strip().lstrip('-•').strip()
                if ingredient:
                    ingredients.append(ingredient)
        return ingredients


class ProductivityAgentWithAutoSave:
    """
    Example: Productivity Agent that automatically saves tasks to database
    """
    
    async def process_task_request(
        self,
        user_message: str,
        session: AgentSession,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Process task creation request and save to database
        """
        # Step 1: Generate task recommendations
        response_text = await self._generate_task_plan(user_message)
        
        # Step 2: Parse tasks from response
        tasks_to_save = self._parse_tasks(response_text, user_message)
        
        # Step 3: Save all tasks
        saved_tasks = []
        for task_data in tasks_to_save:
            saved_task = save_task(
                data=task_data,
                session=session,
                user=user
            )
            if saved_task:
                saved_tasks.append(saved_task)
        
        # Step 4: Return response
        return {
            'success': True,
            'response': response_text,
            'tasks_saved': len(saved_tasks),
            'saved_task_ids': [t.id for t in saved_tasks]
        }
    
    async def _generate_task_plan(self, message: str) -> str:
        """Generate task plan using LLM"""
        return "1. Break down project into phases\n2. Set milestones..."
    
    def _parse_tasks(self, text: str, original_message: str) -> list:
        """
        Parse multiple tasks from agent response
        Returns list of task data dictionaries
        """
        tasks = []
        
        # Find numbered or bulleted lists that look like tasks
        task_pattern = r'^[\d\-•]+\s*(.+)$'
        lines = text.split('\n')
        
        for line in lines:
            match = re.match(task_pattern, line.strip())
            if match:
                task_title = match.group(1).strip()
                if len(task_title) > 10:  # Reasonable task title length
                    # Extract priority from text (simple heuristic)
                    priority = 'medium'
                    if any(word in task_title.lower() for word in ['urgent', 'asap', 'critical']):
                        priority = 'urgent'
                    elif any(word in task_title.lower() for word in ['important', 'high']):
                        priority = 'high'
                    
                    tasks.append({
                        'title': task_title,
                        'description': f"From: {original_message}",
                        'priority': priority,
                        'status': 'todo'
                    })
        
        return tasks


class StudyBuddyWithAutoSave:
    """
    Example: Study Buddy Agent that saves study sessions
    """
    
    async def process_study_request(
        self,
        user_message: str,
        session: AgentSession,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Process study request and save session
        """
        # Step 1: Generate study plan
        response_text = await self._generate_study_plan(user_message)
        
        # Step 2: Extract study session data
        study_data = self._parse_study_session(response_text, user_message)
        
        # Step 3: Save to database
        saved_session = None
        if study_data:
            saved_session = save_study_session(
                data=study_data,
                session=session,
                user=user
            )
        
        return {
            'success': True,
            'response': response_text,
            'saved': saved_session is not None,
            'session_id': saved_session.id if saved_session else None
        }
    
    async def _generate_study_plan(self, message: str) -> str:
        """Generate study plan using LLM"""
        return "Study Plan: Focus on Python fundamentals..."
    
    def _parse_study_session(self, text: str, original_message: str) -> Dict[str, Any]:
        """Parse study session data from response"""
        # Extract subject from original message
        subject = "General Study"
        common_subjects = ['math', 'science', 'history', 'python', 'javascript', 'physics']
        for subj in common_subjects:
            if subj in original_message.lower():
                subject = subj.title()
                break
        
        return {
            'subject': subject,
            'topic': original_message[:100],  # Use part of original message
            'duration': 60,  # Default duration
            'notes': text,
            'resources': []
        }


class WellnessAgentWithAutoSave:
    """
    Example: Wellness Agent that logs wellness activities
    """
    
    async def process_wellness_request(
        self,
        user_message: str,
        session: AgentSession,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Process wellness tracking request and save activity
        """
        # Step 1: Generate wellness recommendations
        response_text = await self._generate_wellness_plan(user_message)
        
        # Step 2: Parse wellness activity
        activity_data = self._parse_wellness_activity(response_text, user_message)
        
        # Step 3: Save to database
        saved_activity = None
        if activity_data:
            saved_activity = save_wellness_activity(
                data=activity_data,
                session=session,
                user=user
            )
        
        return {
            'success': True,
            'response': response_text,
            'saved': saved_activity is not None,
            'activity_id': saved_activity.id if saved_activity else None
        }
    
    async def _generate_wellness_plan(self, message: str) -> str:
        """Generate wellness plan using LLM"""
        return "30 minutes of cardio exercise recommended..."
    
    def _parse_wellness_activity(self, text: str, original_message: str) -> Dict[str, Any]:
        """Parse wellness activity from text"""
        from datetime import datetime
        
        # Determine activity type
        activity_type = 'exercise'  # Default
        if 'meditat' in original_message.lower():
            activity_type = 'meditation'
        elif 'sleep' in original_message.lower():
            activity_type = 'sleep'
        elif 'water' in original_message.lower() or 'hydrat' in original_message.lower():
            activity_type = 'hydration'
        elif 'mood' in original_message.lower() or 'feel' in original_message.lower():
            activity_type = 'mood'
        
        # Extract duration if mentioned
        duration = None
        duration_match = re.search(r'(\d+)\s*(minute|min|hour|hr)', text.lower())
        if duration_match:
            duration = int(duration_match.group(1))
            if 'hour' in duration_match.group(2) or 'hr' in duration_match.group(2):
                duration *= 60
        
        return {
            'activity_type': activity_type,
            'duration': duration,
            'notes': text,
            'recorded_at': datetime.now().isoformat(),
            'metadata': {
                'original_request': original_message
            }
        }


# Generic auto-save wrapper for any agent
class AgentWithAutoSave:
    """
    Generic wrapper that adds auto-save capabilities to any agent
    """
    
    def __init__(self, agent_type: str, base_agent):
        self.agent_type = agent_type
        self.base_agent = base_agent
    
    async def process_with_autosave(
        self,
        message: str,
        session: AgentSession,
        user: Optional[User] = None,
        auto_parse: bool = True
    ) -> Dict[str, Any]:
        """
        Process message and automatically save if structured data detected
        """
        # Get response from base agent
        response = await self.base_agent.process_message(message)
        
        result = {
            'success': True,
            'response': response,
            'saved_items': []
        }
        
        if auto_parse:
            # Try to parse and save structured data
            parsed_data = self._auto_parse(response, message)
            if parsed_data:
                saved_item = save_agent_output(
                    agent_type=self.agent_type,
                    data=parsed_data,
                    session=session,
                    user=user
                )
                if saved_item:
                    result['saved_items'].append({
                        'type': self.agent_type,
                        'id': saved_item.id
                    })
        
        return result
    
    def _auto_parse(self, response: str, original_message: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to automatically parse structured data from response
        Based on agent type
        """
        # Implement smart parsing based on agent_type
        # This is a placeholder - enhance based on your needs
        return None


# Example usage in agent runner
"""
# In your agent's process_message method:

async def process_message(self, message: str, session: AgentSession, user=None):
    # Generate response using LLM
    response_text = await self.generate_response(message)
    
    # Parse and save if applicable
    parsed_data = parse_agent_output(response_text, message)
    saved_item = save_agent_output(
        agent_type='meal_planner_agent',
        data=parsed_data,
        session=session,
        user=user
    )
    
    return {
        'response': response_text,
        'saved': saved_item is not None,
        'saved_id': saved_item.id if saved_item else None
    }
"""
