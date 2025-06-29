"""
Supervisor Agent

Orchestrates the workflow between worker agents using LangGraph.
Manages the overall travel planning process and handles retries and clarifications.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..models.state import AgentState, AgentRole, ConfidenceLevel
from ..config import config
from .base_agent import BaseAgent
from .query_parser import QueryParserAgent
from .itinerary_agent import ItineraryAgent
from .critique_agent import CritiqueAgent


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates the travel planning workflow.
    
    Manages the flow between:
    1. QueryParserAgent - Parse user input
    2. ItineraryAgent - Generate travel plans
    3. CritiqueAgent - Evaluate and provide feedback
    
    Handles retries, clarifications, and final output.
    """
    
    def __init__(self):
        super().__init__(AgentRole.SUPERVISOR)
        
        # Initialize worker agents
        self.query_parser = QueryParserAgent()
        self.itinerary_agent = ItineraryAgent()
        self.critique_agent = CritiqueAgent()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=MemorySaver())
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for the travel planning process"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("parse_query", self._parse_query_node)
        workflow.add_node("generate_itinerary", self._generate_itinerary_node)
        workflow.add_node("critique_itinerary", self._critique_itinerary_node)
        workflow.add_node("handle_retry", self._handle_retry_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define the workflow edges
        workflow.set_entry_point("parse_query")
        
        # Parse query -> Generate itinerary
        workflow.add_edge("parse_query", "generate_itinerary")
        
        # Generate itinerary -> Critique itinerary
        workflow.add_edge("generate_itinerary", "critique_itinerary")
        
        # Critique itinerary -> Decision point
        workflow.add_conditional_edges(
            "critique_itinerary",
            self._decide_next_step,
            {
                "finalize": "finalize",
                "retry": "handle_retry",
                "clarification": END,  # End with clarification needed
            }
        )
        
        # Handle retry -> Generate itinerary (loop back)
        workflow.add_edge("handle_retry", "generate_itinerary")
        
        # Finalize -> End
        workflow.add_edge("finalize", END)
        
        return workflow
    
    async def process(self, state: AgentState) -> AgentState:
        """Process a travel planning request through the complete workflow"""
        
        # Initialize session if not present
        if "session_id" not in state:
            state["session_id"] = str(uuid.uuid4())
        
        if "created_at" not in state:
            state["created_at"] = datetime.now()
        
        state["updated_at"] = datetime.now()
        state["retry_count"] = state.get("retry_count", 0)
        state["is_complete"] = False
        state["needs_clarification"] = False
        
        self.log_execution(state, f"Starting travel planning workflow for session {state['session_id']}")
        
        try:
            # Run the workflow
            thread_config = {"configurable": {"thread_id": state["session_id"]}}
            
            result = await self.app.ainvoke(state, config=thread_config)
            
            # Save final state
            self.save_state(result)
            
            self.log_execution(
                result, 
                f"Workflow completed - Complete: {result.get('is_complete', False)}, "
                f"Needs clarification: {result.get('needs_clarification', False)}"
            )
            
            return result
            
        except Exception as e:
            self.log_execution(state, f"Workflow error: {str(e)}")
            raise
    
    async def _parse_query_node(self, state: AgentState) -> AgentState:
        """Node for query parsing"""
        self.log_execution(state, "Executing query parsing step")
        return await self.query_parser.process(state)
    
    async def _generate_itinerary_node(self, state: AgentState) -> AgentState:
        """Node for itinerary generation"""
        self.log_execution(state, "Executing itinerary generation step")
        return await self.itinerary_agent.process(state)
    
    async def _critique_itinerary_node(self, state: AgentState) -> AgentState:
        """Node for itinerary critique"""
        self.log_execution(state, "Executing itinerary critique step")
        return await self.critique_agent.process(state)
    
    async def _handle_retry_node(self, state: AgentState) -> AgentState:
        """Node for handling retries"""
        retry_count = state.get("retry_count", 0)
        
        self.log_execution(
            state, 
            f"Handling retry {retry_count + 1}/{config.MAX_RETRIES}"
        )
        
        # Increment retry count
        state["retry_count"] = retry_count + 1
        
        # Add feedback from critique for next iteration
        confidence_metrics = state.get("confidence_metrics", {})
        
        # Add improvement hints based on low scores
        improvement_hints = []
        
        if confidence_metrics.get("budget_score", 1.0) < 0.7:
            improvement_hints.append("Focus on budget-friendly options")
        
        if confidence_metrics.get("preference_match_score", 1.0) < 0.7:
            improvement_hints.append("Better match user preferences")
        
        if confidence_metrics.get("feasibility_score", 1.0) < 0.7:
            improvement_hints.append("Improve timeline and logistics")
        
        # Store hints for the itinerary agent to use
        state["improvement_hints"] = improvement_hints
        
        return state
    
    async def _finalize_node(self, state: AgentState) -> AgentState:
        """Node for finalizing the itinerary"""
        self.log_execution(state, "Finalizing itinerary")
        
        current_itinerary = state.get("current_itinerary")
        
        if current_itinerary:
            # Mark as final
            state["final_itinerary"] = current_itinerary
            state["is_complete"] = True
            
            # Add final metadata
            state["final_itinerary"]["finalized_at"] = datetime.now()
            state["final_itinerary"]["confidence_metrics"] = state.get("confidence_metrics", {})
        
        return state
    
    def _decide_next_step(self, state: AgentState) -> str:
        """Decision function to determine next step after critique"""
        
        confidence_level = state.get("confidence_level")
        retry_count = state.get("retry_count", 0)
        
        if confidence_level == ConfidenceLevel.HIGH:
            return "finalize"
        elif confidence_level == ConfidenceLevel.MEDIUM:
            if retry_count < config.MAX_RETRIES:
                return "retry"
            else:
                return "finalize"  # Max retries reached, finalize anyway
        else:  # LOW confidence
            return "clarification"
    
    async def handle_user_clarification(
        self, 
        session_id: str, 
        clarification_response: str
    ) -> AgentState:
        """Handle user response to clarification questions"""
        
        # Load existing state
        existing_state = self.load_state(session_id)
        
        if not existing_state:
            raise ValueError(f"No session found with ID: {session_id}")
        
        self.log_execution(
            existing_state, 
            f"Processing user clarification: {clarification_response[:100]}..."
        )
        
        # Update the user query with clarification
        original_query = existing_state.get("user_query", "")
        updated_query = f"{original_query}\n\nAdditional details: {clarification_response}"
        
        # Create new state with updated query
        new_state = AgentState(
            user_query=updated_query,
            session_id=session_id,
            created_at=existing_state.get("created_at", datetime.now()),
            updated_at=datetime.now(),
            retry_count=0,  # Reset retry count
            execution_trace=existing_state.get("execution_trace", []),
            parsed_constraints={},
            search_results={},
            itinerary_versions=existing_state.get("itinerary_versions", []),
            confidence_metrics={},
            current_agent=None,
            final_itinerary=None,
            is_complete=False,
            needs_clarification=False,
            clarification_questions=[]
        )
        
        # Process the updated request
        return await self.process(new_state)
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a session"""
        
        state = self.load_state(session_id)
        
        if not state:
            return None
        
        return {
            "session_id": session_id,
            "is_complete": state.get("is_complete", False),
            "needs_clarification": state.get("needs_clarification", False),
            "retry_count": state.get("retry_count", 0),
            "current_agent": state.get("current_agent"),
            "confidence_level": state.get("confidence_level"),
            "created_at": state.get("created_at"),
            "updated_at": state.get("updated_at"),
            "has_final_itinerary": bool(state.get("final_itinerary")),
            "clarification_questions": state.get("clarification_questions", [])
        }
    
    def get_final_itinerary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the final itinerary for a completed session"""
        
        state = self.load_state(session_id)
        
        if not state or not state.get("is_complete"):
            return None
        
        return state.get("final_itinerary")
    
    def get_execution_trace(self, session_id: str) -> List[str]:
        """Get the execution trace for debugging"""
        
        state = self.load_state(session_id)
        
        if not state:
            return []
        
        return state.get("execution_trace", [])
