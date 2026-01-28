"""
Agent orchestrator for coordinating multiple AI agents in the LifeOS system.
"""
from typing import Dict, Any, Optional
from .meal_planner import meal_agent_runner


class AgentOrchestrator:
    """
    Orchestrates communication between multiple AI agents and manages sessions.
    """
    
    def __init__(self):
        self.agents = {
            'meal_planner': meal_agent_runner,
            # Other agents will be added here
            # 'productivity': productivity_agent_runner,
            # 'study_buddy': study_buddy_runner,
            # 'wellness': wellness_agent_runner,
        }
    
    async def route_message(
        self, 
        agent_type: str, 
        message: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a message to the appropriate agent.
        
        Args:
            agent_type: Type of agent to route to ('meal_planner', 'productivity', etc.)
            message: User message to send to the agent
            session_id: Optional session ID for maintaining conversation context
            context: Additional context to pass to the agent
            
        Returns:
            Response from the agent
        """
        if agent_type not in self.agents:
            return {
                'error': f'Unknown agent type: {agent_type}',
                'available_agents': list(self.agents.keys())
            }
        
        agent_runner = self.agents[agent_type]
        
        try:
            response = await agent_runner.run_agent(message, session_id=session_id)
            return {
                'success': True,
                'response': response,
                'agent_type': agent_type
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent_type': agent_type
            }
    
    def get_available_agents(self) -> list:
        """Return list of available agent types"""
        return list(self.agents.keys())


# Singleton instance
orchestrator = AgentOrchestrator()
