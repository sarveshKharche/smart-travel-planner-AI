"""
Smart Travel Planner AI - Agent State Definition

This module defines the core state structure used by the LangGraph
supervisor-worker pattern for travel planning orchestration.
"""

from typing import TypedDict, Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for agent decisions"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentRole(Enum):
    """Available agent roles in the system"""
    SUPERVISOR = "supervisor"
    QUERY_PARSER = "query_parser"
    ITINERARY = "itinerary"
    CRITIQUE = "critique"


class AgentState(TypedDict, total=False):
    """
    Core state structure shared across all agents in the LangGraph workflow.
    
    This state is passed between agents and maintains the complete context
    of the travel planning process, including audit trails and metrics.
    """
    
    # Input and parsing
    user_query: str
    parsed_constraints: Dict[str, Any]  # dates, budget, preferences, travelers
    
    # External data
    search_results: Dict[str, Any]  # raw flight/activity/weather data
    
    # Itinerary generation
    itinerary_versions: List[Dict[str, Any]]  # audit trail of generated drafts
    current_itinerary: Optional[Dict[str, Any]]  # latest version
    
    # Quality metrics
    confidence_metrics: Dict[str, float]  # budget_score, feasibility_score, etc.
    confidence_level: Optional[ConfidenceLevel]
    
    # Execution tracking
    execution_trace: List[str]  # logs from each agent
    current_agent: Optional[AgentRole]
    retry_count: int
    
    # Metadata
    session_id: str
    created_at: datetime
    updated_at: datetime
    
    # Final output
    final_itinerary: Optional[Dict[str, Any]]
    is_complete: bool
    needs_clarification: bool
    clarification_questions: List[str]
    
    # Additional fields for agent communication
    improvement_hints: List[str]


class ParsedConstraints(TypedDict):
    """Structure for parsed user constraints"""
    
    # Travel details
    origin: Optional[str]
    destinations: List[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration_days: Optional[int]
    
    # Budget and travelers
    total_budget: Optional[float]
    budget_currency: str
    traveler_count: int
    traveler_types: List[str]  # solo, couple, family, friends
    
    # Preferences
    travel_style: List[str]  # adventure, relaxation, culture, food, etc.
    accommodation_type: List[str]  # hotel, hostel, airbnb, camping
    transportation_modes: List[str]  # flight, car, train, bus
    activity_preferences: List[str]
    dietary_restrictions: List[str]
    accessibility_needs: List[str]
    
    # Constraints
    must_have: List[str]
    must_avoid: List[str]
    flexibility: Dict[str, str]  # dates, budget, destinations


class ItineraryDay(TypedDict):
    """Structure for a single day in the itinerary"""
    
    day_number: int
    date: datetime
    location: str
    weather_forecast: Dict[str, Any]
    
    activities: List[Dict[str, Any]]
    meals: List[Dict[str, Any]]
    transportation: List[Dict[str, Any]]
    accommodation: Optional[Dict[str, Any]]
    
    estimated_cost: float
    notes: List[str]


class Itinerary(TypedDict):
    """Complete itinerary structure"""
    
    # Overview
    title: str
    description: str
    total_cost: float
    currency: str
    confidence_score: float
    
    # Trip details
    origin: str
    destinations: List[str]
    start_date: datetime
    end_date: datetime
    duration_days: int
    traveler_count: int
    
    # Daily breakdown
    days: List[ItineraryDay]
    
    # Summary information
    highlights: List[str]
    total_flights: List[Dict[str, Any]]
    accommodations_summary: List[Dict[str, Any]]
    budget_breakdown: Dict[str, float]
    
    # Metadata
    generated_at: datetime
    version: int
    agent_feedback: Dict[str, Any]


class ConfidenceMetrics(TypedDict):
    """Metrics used to evaluate itinerary quality"""
    
    budget_score: float  # How well does it fit the budget?
    feasibility_score: float  # Is the timeline realistic?
    preference_match_score: float  # Does it match user preferences?
    completeness_score: float  # Are all necessary details included?
    novelty_score: float  # How interesting/unique is the plan?
    
    overall_score: float
    confidence_level: ConfidenceLevel
    
    # Detailed breakdown
    budget_analysis: Dict[str, Any]
    timeline_analysis: Dict[str, Any]
    preference_analysis: Dict[str, Any]
    missing_elements: List[str]
    risk_factors: List[str]
