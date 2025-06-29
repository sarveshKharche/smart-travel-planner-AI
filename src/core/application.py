"""
Smart Travel Planner Application Core

Main application class that orchestrates the LangGraph supervisor-worker pattern
for intelligent travel itinerary generation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ..agents.supervisor import SupervisorAgent
from ..models.state import AgentState, AgentRole
from ..services.persistence import PersistenceService
from ..config import Config

logger = logging.getLogger(__name__)


def create_initial_state(user_query: str, session_id: str) -> AgentState:
    """Create initial AgentState from user query"""
    return AgentState(
        user_query=user_query,
        session_id=session_id,
        parsed_constraints={},
        search_results={},
        itinerary_versions=[],
        current_itinerary=None,
        confidence_metrics={},
        confidence_level=None,
        execution_trace=[],
        current_agent=AgentRole.SUPERVISOR,
        retry_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        final_itinerary=None,
        is_complete=False,
        needs_clarification=False,
        clarification_questions=[],
        improvement_hints=[]
    )


class TravelPlannerApp:
    """
    Main application class for the Smart Travel Planner AI.
    
    Coordinates the supervisor-worker agent pattern to process travel requests
    and generate comprehensive itineraries.
    """
    
    def __init__(self):
        """Initialize the travel planner application"""
        self.config = Config()
        self.supervisor = SupervisorAgent()
        self.persistence = PersistenceService()
        
        logger.info("TravelPlannerApp initialized successfully")
    
    async def process_travel_request(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a travel planning request through the agent system.
        
        Args:
            user_query: Raw user input describing travel preferences
            session_id: Optional session identifier for continuity
            
        Returns:
            Dict containing the generated itinerary and metadata
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            logger.info(f"Processing travel request for session {session_id}")
            
            # Create initial state
            state = create_initial_state(user_query, session_id)
            
            # Save initial state to DynamoDB
            await self.persistence.save_state(state)
            
            # Process through supervisor agent
            final_state = await self.supervisor.process(state)
            
            # Save final state
            await self.persistence.save_state(final_state)
            
            # Extract response data
            response = self._format_response(final_state)
            
            logger.info(f"Travel request processed successfully for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing travel request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def _format_response(self, state: AgentState) -> Dict[str, Any]:
        """
        Format the final agent state into a response for the API.
        
        Args:
            state: Final agent state after processing
            
        Returns:
            Formatted response dictionary
        """
        # Check if processing was successful
        has_itinerary = bool(state.get("itinerary_versions"))
        confidence = state.get("confidence_metrics", {})
        
        # Determine the decision based on final state
        if state.get("is_complete") and has_itinerary:
            # Successful completion
            latest_itinerary = state.get("itinerary_versions", [])[-1] if state.get("itinerary_versions") else {}
            
            return {
                "success": True,
                "session_id": state.get("session_id"),
                "itinerary": latest_itinerary,
                "confidence_metrics": confidence,
                "constraints": state.get("parsed_constraints", {}),
                "retry_count": state.get("retry_count", 0),
                "execution_trace": state.get("execution_trace", []),
                "timestamp": state.get("updated_at")
            }
        
        elif state.get("needs_clarification"):
            # Need user clarification
            return {
                "success": False,
                "session_id": state.get("session_id"),
                "clarification_needed": True,
                "message": "I need more information to create your itinerary. Please provide additional details about your travel preferences.",
                "missing_info": state.get("clarification_questions", []),
                "execution_trace": state.get("execution_trace", [])
            }
        
        else:
            # Failed to generate satisfactory itinerary
            return {
                "success": False,
                "session_id": state.get("session_id"),
                "message": "Unable to generate a satisfactory itinerary with the given constraints. Please try adjusting your requirements.",
                "retry_count": state.get("retry_count", 0),
                "execution_trace": state.get("execution_trace", [])
            }
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current state for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current agent state or None if not found
        """
        try:
            return await self.persistence.load_state(session_id)
        except Exception as e:
            logger.error(f"Error retrieving session state: {str(e)}")
            return None
    
    async def continue_session(self, session_id: str, additional_info: str) -> Dict[str, Any]:
        """
        Continue processing for a session that needed clarification.
        
        Args:
            session_id: Session identifier
            additional_info: Additional information from user
            
        Returns:
            Updated response from continued processing
        """
        try:
            # Load existing state
            state = await self.persistence.load_state(session_id)
            if not state:
                return {
                    "success": False,
                    "error": "Session not found",
                    "session_id": session_id
                }
            
            # Append additional information to user query
            if "user_query" in state:
                state["user_query"] = state["user_query"] + f" Additional info: {additional_info}"
            if "execution_trace" in state:
                state["execution_trace"] = state["execution_trace"] + [f"User provided additional info: {additional_info}"]
            state["updated_at"] = datetime.utcnow()
            
            # Reset for new processing attempt
            state["current_agent"] = AgentRole.SUPERVISOR
            state["retry_count"] = 0
            
            # Process again
            final_state = await self.supervisor.process(state)
            
            # Save and format response
            await self.persistence.save_state(final_state)
            return self._format_response(final_state)
            
        except Exception as e:
            logger.error(f"Error continuing session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the application and its dependencies.
        
        Returns:
            Health status information
        """
        try:
            # Check AWS connectivity
            aws_status = self.persistence.health_check()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "aws_dynamodb": aws_status,
                    "supervisor_agent": "ready",
                    "config": "loaded"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
