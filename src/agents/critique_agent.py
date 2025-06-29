"""
Critique Agent

Evaluates itinerary quality against constraints and decides whether to finalize or retry.
Provides detailed feedback and confidence metrics.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from ..models.state import (
    AgentState, AgentRole, ConfidenceLevel, ConfidenceMetrics
)
from ..config import config
from .base_agent import BaseAgent


class CritiqueAgent(BaseAgent):
    """
    Agent responsible for evaluating itinerary quality and providing feedback.
    
    Analyzes:
    - Budget adherence and cost breakdown
    - Timeline feasibility and logistics
    - Preference matching and satisfaction
    - Completeness and missing elements
    - Overall experience quality
    """
    
    def __init__(self):
        super().__init__(AgentRole.CRITIQUE)
    
    async def process(self, state: AgentState) -> AgentState:
        """Evaluate the current itinerary and provide feedback"""
        
        self.log_execution(state, "Starting itinerary critique and evaluation")
        
        try:
            current_itinerary = state.get("current_itinerary")
            constraints = state.get("parsed_constraints", {})
            
            if not current_itinerary:
                self.log_execution(state, "No itinerary found to critique")
                return state
            
            # Perform comprehensive evaluation
            confidence_metrics = self._evaluate_itinerary(current_itinerary, constraints)
            
            # Calculate overall confidence level
            overall_confidence = self.calculate_confidence(confidence_metrics)
            confidence_level = self._determine_confidence_level(overall_confidence)
            
            # Update state with metrics
            state["confidence_metrics"] = confidence_metrics
            state["confidence_level"] = confidence_level
            state["current_agent"] = AgentRole.CRITIQUE
            
            # Determine next action
            if confidence_level == ConfidenceLevel.HIGH:
                state["is_complete"] = True
                state["final_itinerary"] = current_itinerary
                action = "FINALIZE"
            elif confidence_level == ConfidenceLevel.MEDIUM:
                retry_count = state.get("retry_count", 0)
                if retry_count < config.MAX_RETRIES:
                    state["retry_count"] = retry_count + 1
                    action = "RETRY"
                else:
                    # Finalize even with medium confidence after max retries
                    state["is_complete"] = True
                    state["final_itinerary"] = current_itinerary
                    action = "FINALIZE_WITH_WARNINGS"
            else:  # LOW confidence
                retry_count = state.get("retry_count", 0)
                if retry_count < 2:  # Allow some retries before asking for clarification
                    state["retry_count"] = retry_count + 1
                    action = "RETRY"
                else:
                    state["needs_clarification"] = True
                    state["clarification_questions"] = self._generate_clarification_questions(
                        confidence_metrics, constraints
                    )
                    action = "REQUEST_CLARIFICATION"
            
            self.log_execution(
                state,
                f"Evaluation complete - Confidence: {confidence_level.value} "
                f"(score: {overall_confidence:.2f}), Action: {action}"
            )
            
            return state
            
        except Exception as e:
            self.log_execution(state, f"Error during critique: {str(e)}")
            raise
    
    def _evaluate_itinerary(
        self, 
        itinerary: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """Perform comprehensive itinerary evaluation"""
        
        # Budget evaluation
        budget_score = self._evaluate_budget_adherence(itinerary, constraints)
        
        # Timeline and feasibility evaluation
        feasibility_score = self._evaluate_feasibility(itinerary, constraints)
        
        # Preference matching evaluation
        preference_score = self._evaluate_preference_match(itinerary, constraints)
        
        # Completeness evaluation
        completeness_score = self._evaluate_completeness(itinerary, constraints)
        
        # Experience quality evaluation
        quality_score = self._evaluate_experience_quality(itinerary, constraints)
        
        return {
            "budget_score": budget_score,
            "feasibility_score": feasibility_score,
            "preference_match_score": preference_score,
            "completeness_score": completeness_score,
            "quality_score": quality_score,
            "overall_score": self.calculate_confidence({
                "budget_score": budget_score,
                "feasibility_score": feasibility_score,
                "preference_match_score": preference_score,
                "completeness_score": completeness_score
            })
        }
    
    def _evaluate_budget_adherence(
        self, 
        itinerary: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> float:
        """Evaluate how well the itinerary adheres to budget constraints"""
        
        target_budget = constraints.get("total_budget")
        actual_cost = itinerary.get("total_cost", 0)
        
        if not target_budget:
            return 0.8  # No budget specified, assume reasonable
        
        # Calculate budget adherence
        budget_ratio = actual_cost / target_budget
        
        if budget_ratio <= 0.95:  # Under budget
            score = 1.0
        elif budget_ratio <= 1.05:  # Slightly over budget
            score = 0.9
        elif budget_ratio <= 1.15:  # Moderately over budget
            score = 0.7
        elif budget_ratio <= 1.25:  # Significantly over budget
            score = 0.4
        else:  # Way over budget
            score = 0.1
        
        # Bonus for good budget breakdown
        budget_breakdown = itinerary.get("budget_breakdown", {})
        if budget_breakdown:
            # Check if categories are reasonable
            flight_ratio = budget_breakdown.get("flights", 0) / actual_cost
            accom_ratio = budget_breakdown.get("accommodation", 0) / actual_cost
            
            if 0.3 <= flight_ratio <= 0.6 and 0.2 <= accom_ratio <= 0.5:
                score = min(1.0, score + 0.1)
        
        return score
    
    def _evaluate_feasibility(
        self, 
        itinerary: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> float:
        """Evaluate timeline feasibility and logistics"""
        
        score = 1.0
        days = itinerary.get("days", [])
        
        if not days:
            return 0.0
        
        # Check day structure
        for day in days:
            activities = day.get("activities", [])
            
            # Too many activities in one day
            if len(activities) > 4:
                score -= 0.1
            
            # Check activity timing conflicts
            activity_times = []
            for activity in activities:
                time_str = activity.get("time", "")
                if time_str:
                    activity_times.append(time_str)
            
            # Should have reasonable time spacing
            if len(activity_times) >= 2:
                score += 0.05  # Good timing planning
        
        # Check transportation logistics
        flights = itinerary.get("total_flights", [])
        if flights:
            for flight in flights:
                # Check if flight times are reasonable
                departure_time = flight.departure_date if hasattr(flight, 'departure_date') else None
                if departure_time:
                    hour = departure_time.hour
                    if 6 <= hour <= 22:  # Reasonable flight times
                        score += 0.05
                    else:
                        score -= 0.05
        
        # Duration appropriateness
        duration = itinerary.get("duration_days", 0)
        destinations = len(itinerary.get("destinations", []))
        
        if destinations > 1 and duration < destinations * 2:
            score -= 0.2  # Too rushed for multi-city
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_preference_match(
        self, 
        itinerary: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> float:
        """Evaluate how well the itinerary matches user preferences"""
        
        score = 0.5  # Start with neutral score
        
        # Travel style matching
        travel_styles = constraints.get("travel_style", [])
        activity_prefs = constraints.get("activity_preferences", [])
        
        days = itinerary.get("days", [])
        
        for day in days:
            activities = day.get("activities", [])
            
            for activity in activities:
                activity_type = activity.get("type", "")
                activity_name = activity.get("name", "").lower()
                
                # Match against preferences
                for pref in activity_prefs:
                    if pref.lower() in activity_type.lower() or pref.lower() in activity_name:
                        score += 0.1
                
                for style in travel_styles:
                    if style.lower() in activity_type.lower() or style.lower() in activity_name:
                        score += 0.1
        
        # Accommodation preference matching
        accom_prefs = constraints.get("accommodation_type", [])
        accom_summary = itinerary.get("accommodations_summary", [])
        
        for accom in accom_summary:
            accom_type = accom.get("type", "")
            if accom_type in accom_prefs:
                score += 0.15
        
        # Weather consideration
        days = itinerary.get("days", [])
        for day in days:
            weather = day.get("weather_forecast", {})
            activities = day.get("activities", [])
            
            # Check if outdoor activities are planned for good weather
            outdoor_activities = [a for a in activities if a.get("weather_dependent", False)]
            if outdoor_activities and weather.get("precipitation_chance", 0) > 70:
                score -= 0.1  # Poor weather planning
            elif outdoor_activities and weather.get("precipitation_chance", 0) < 30:
                score += 0.05  # Good weather planning
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_completeness(
        self, 
        itinerary: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> float:
        """Evaluate completeness of the itinerary"""
        
        score = 0.0
        required_elements = [
            "title", "description", "total_cost", "destinations",
            "start_date", "end_date", "days", "budget_breakdown"
        ]
        
        # Check for required elements
        for element in required_elements:
            if element in itinerary and itinerary[element]:
                score += 0.1
        
        # Check day completeness
        days = itinerary.get("days", [])
        if days:
            for day in days:
                day_elements = ["activities", "meals", "transportation"]
                day_score = 0
                
                for element in day_elements:
                    if element in day and day[element]:
                        day_score += 1
                
                score += (day_score / len(day_elements)) * 0.1
        
        # Check for weather information
        weather_coverage = 0
        for day in days:
            if day.get("weather_forecast"):
                weather_coverage += 1
        
        if days and weather_coverage / len(days) > 0.8:
            score += 0.1
        
        # Check for cost breakdown
        budget_breakdown = itinerary.get("budget_breakdown", {})
        if len(budget_breakdown) >= 4:  # Multiple cost categories
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_experience_quality(
        self, 
        itinerary: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> float:
        """Evaluate the overall experience quality"""
        
        score = 0.5  # Start neutral
        
        # Diversity of activities
        activity_types = set()
        days = itinerary.get("days", [])
        
        for day in days:
            for activity in day.get("activities", []):
                activity_types.add(activity.get("type", ""))
        
        if len(activity_types) >= 3:
            score += 0.2  # Good variety
        
        # Local experience vs tourist traps
        local_experiences = 0
        total_activities = 0
        
        for day in days:
            activities = day.get("activities", [])
            total_activities += len(activities)
            
            for activity in activities:
                description = activity.get("description", "").lower()
                if any(word in description for word in ["local", "authentic", "traditional"]):
                    local_experiences += 1
        
        if total_activities > 0:
            local_ratio = local_experiences / total_activities
            score += local_ratio * 0.2
        
        # Meal variety and quality
        unique_restaurants = set()
        for day in days:
            for meal in day.get("meals", []):
                unique_restaurants.add(meal.get("name", ""))
        
        if len(unique_restaurants) >= len(days):
            score += 0.1  # Different restaurants each day
        
        # Time for rest and flexibility
        total_days = len(days)
        if total_days >= 3:
            # Should have some downtime
            downtime_activities = 0
            for day in days:
                activities = day.get("activities", [])
                if len(activities) <= 2:  # Not overpacked
                    downtime_activities += 1
            
            if downtime_activities >= total_days * 0.3:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _determine_confidence_level(self, overall_score: float) -> ConfidenceLevel:
        """Determine confidence level based on overall score"""
        
        if overall_score >= config.CONFIDENCE_THRESHOLD_HIGH:
            return ConfidenceLevel.HIGH
        elif overall_score >= config.CONFIDENCE_THRESHOLD_MEDIUM:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_clarification_questions(
        self, 
        metrics: Dict[str, float], 
        constraints: Dict[str, Any]
    ) -> List[str]:
        """Generate clarification questions based on low confidence areas"""
        
        questions = []
        
        # Budget issues
        if metrics.get("budget_score", 1.0) < 0.6:
            budget = constraints.get("total_budget")
            if budget:
                questions.append(
                    f"Your budget of ${budget:.0f} might be tight for this trip. "
                    "Would you like to increase the budget or adjust the itinerary scope?"
                )
            else:
                questions.append(
                    "Could you provide a specific budget range for this trip? "
                    "This will help us create a more realistic itinerary."
                )
        
        # Preference matching issues
        if metrics.get("preference_match_score", 1.0) < 0.6:
            questions.append(
                "The planned activities might not fully match your interests. "
                "Could you provide more specific preferences or must-have experiences?"
            )
        
        # Feasibility issues
        if metrics.get("feasibility_score", 1.0) < 0.6:
            duration = constraints.get("duration_days", 0)
            destinations = constraints.get("destinations", [])
            
            if len(destinations) > 1 and duration < len(destinations) * 2:
                questions.append(
                    "The timeline might be rushed for visiting multiple destinations. "
                    "Would you prefer to extend the trip or focus on fewer places?"
                )
        
        # Completeness issues
        if metrics.get("completeness_score", 1.0) < 0.6:
            missing_info = []
            
            if not constraints.get("start_date"):
                missing_info.append("travel dates")
            if not constraints.get("origin"):
                missing_info.append("departure location")
            if not constraints.get("accommodation_type"):
                missing_info.append("accommodation preferences")
            
            if missing_info:
                questions.append(
                    f"Could you provide more details about: {', '.join(missing_info)}?"
                )
        
        # Default question if no specific issues identified
        if not questions:
            questions.append(
                "We need more information to create the perfect itinerary for you. "
                "Could you provide more details about your preferences or requirements?"
            )
        
        return questions[:3]  # Limit to 3 questions
