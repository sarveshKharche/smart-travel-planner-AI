"""
Itinerary Agent

Fetches external data and builds rich, detailed day-by-day itineraries.
Integrates flight data, weather forecasts, and local recommendations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..models.state import (
    AgentState, AgentRole, Itinerary, ItineraryDay, 
    ParsedConstraints
)
from ..services.external_apis import ExternalAPIService
from ..services.mock_external_apis import mock_external_api_service
from .base_agent import BaseAgent


class ItineraryAgent(BaseAgent):
    """
    Agent responsible for creating detailed travel itineraries.
    
    Combines:
    - Flight search and booking options
    - Weather forecasts for all destinations
    - Local points of interest and recommendations
    - Day-by-day activity planning
    - Cost estimation and budget tracking
    """
    
    def __init__(self):
        super().__init__(AgentRole.ITINERARY)
    
    async def process(self, state: AgentState) -> AgentState:
        """Create a detailed itinerary based on parsed constraints"""
        
        self.log_execution(state, "Starting itinerary generation")
        
        try:
            constraints = state.get("parsed_constraints", {})
            
            # Try to fetch external data, fallback to mock if needed
            try:
                async with ExternalAPIService() as api_service:
                    search_results = await self._gather_travel_data(constraints, api_service)
            except Exception as e:
                self.log_execution(state, f"External API failed, using mock data: {str(e)}")
                search_results = await self._gather_travel_data_mock(constraints)
            
            state["search_results"] = search_results
            
            # Generate itinerary
            itinerary = await self._build_itinerary(constraints, search_results)
            
            # Add to versions list for audit trail
            if "itinerary_versions" not in state:
                state["itinerary_versions"] = []
            
            version_number = len(state["itinerary_versions"]) + 1
            itinerary["version"] = version_number
            
            state["itinerary_versions"].append(itinerary)
            state["current_itinerary"] = itinerary
            state["current_agent"] = AgentRole.ITINERARY
            
            self.log_execution(
                state, 
                f"Generated itinerary v{version_number} with {len(itinerary.get('days', []))} days, "
                f"estimated cost: ${itinerary.get('total_cost', 0):.2f}"
            )
            
            return state
            
        except Exception as e:
            self.log_execution(state, f"Error generating itinerary: {str(e)}")
            raise
    
    async def _gather_travel_data(
        self, 
        constraints: Dict[str, Any], 
        api_service: ExternalAPIService
    ) -> Dict[str, Any]:
        """Gather all external data needed for itinerary building"""
        
        search_results = {
            "flights": [],
            "weather": {},
            "points_of_interest": {},
            "accommodations": []
        }
        
        # Get destinations and dates
        destinations = constraints.get("destinations", [])
        start_date = constraints.get("start_date")
        end_date = constraints.get("end_date")
        duration = constraints.get("duration_days", 3)
        
        if not start_date:
            start_date = datetime.now() + timedelta(days=30)  # Default to next month
        
        if not end_date:
            end_date = start_date + timedelta(days=duration)
        
        # Search flights
        origin = constraints.get("origin", "New York")
        traveler_count = constraints.get("traveler_count", 1)
        
        for destination in destinations:
            try:
                flights = await api_service.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=start_date,
                    return_date=end_date,
                    adults=traveler_count
                )
                search_results["flights"].extend(flights)
            except Exception as e:
                print(f"Flight search error for {destination}: {e}")
        
        # Get weather forecasts
        for destination in destinations:
            try:
                weather_data = await api_service.get_weather_forecast(
                    location=destination,
                    start_date=start_date,
                    days=(end_date - start_date).days + 1
                )
                search_results["weather"][destination] = weather_data
            except Exception as e:
                print(f"Weather search error for {destination}: {e}")
        
        # Get points of interest
        activity_preferences = constraints.get("activity_preferences", ["sightseeing"])
        
        for destination in destinations:
            search_results["points_of_interest"][destination] = {}
            
            for activity in activity_preferences[:3]:  # Limit API calls
                try:
                    pois = await api_service.search_points_of_interest(
                        location=destination,
                        category=activity,
                        limit=5
                    )
                    search_results["points_of_interest"][destination][activity] = pois
                except Exception as e:
                    print(f"POI search error for {destination}/{activity}: {e}")
        
        return search_results
    
    async def _build_itinerary(
        self, 
        constraints: Dict[str, Any], 
        search_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the complete itinerary from constraints and external data"""
        
        # Extract basic information
        destinations = constraints.get("destinations", ["Unknown"])
        start_date = constraints.get("start_date", datetime.now())
        end_date = constraints.get("end_date")
        duration = constraints.get("duration_days", 3)
        budget = constraints.get("total_budget", 1000.0)
        traveler_count = constraints.get("traveler_count", 1)
        
        if not end_date:
            end_date = start_date + timedelta(days=duration)
        
        # Build daily itinerary
        days = []
        current_date = start_date
        total_cost = 0.0
        
        # Distribute destinations across days
        primary_destination = destinations[0]
        
        for day_num in range(duration):
            day_date = current_date + timedelta(days=day_num)
            
            # Get weather for this day
            weather_forecast = self._get_weather_for_date(
                search_results.get("weather", {}),
                primary_destination,
                day_date
            )
            
            # Plan activities for this day
            activities = self._plan_daily_activities(
                day_num,
                primary_destination,
                constraints,
                search_results,
                weather_forecast
            )
            
            # Plan meals
            meals = self._plan_daily_meals(
                primary_destination,
                constraints,
                search_results
            )
            
            # Plan transportation
            transportation = self._plan_daily_transportation(
                day_num,
                duration,
                search_results,
                primary_destination
            )
            
            # Calculate daily cost
            daily_cost = self._calculate_daily_cost(
                activities,
                meals,
                transportation,
                day_num,
                duration,
                budget
            )
            
            total_cost += daily_cost
            
            # Create day object
            day = {
                "day_number": day_num + 1,
                "date": day_date,
                "location": primary_destination,
                "weather_forecast": weather_forecast,
                "activities": activities,
                "meals": meals,
                "transportation": transportation,
                "estimated_cost": daily_cost,
                "notes": []
            }
            
            days.append(day)
        
        # Add accommodation
        accommodation_cost = self._calculate_accommodation_cost(
            duration,
            budget,
            total_cost,
            constraints
        )
        total_cost += accommodation_cost
        
        # Build complete itinerary
        itinerary = {
            "title": self._generate_itinerary_title(destinations, duration),
            "description": self._generate_itinerary_description(constraints),
            "total_cost": total_cost,
            "currency": constraints.get("budget_currency", "USD"),
            "confidence_score": 0.8,  # Will be calculated by critique agent
            "origin": constraints.get("origin", "Unknown"),
            "destinations": destinations,
            "start_date": start_date,
            "end_date": end_date,
            "duration_days": duration,
            "traveler_count": traveler_count,
            "days": days,
            "highlights": self._generate_highlights(days, search_results),
            "total_flights": search_results.get("flights", [])[:2],  # Best 2 options
            "accommodations_summary": self._generate_accommodation_summary(
                primary_destination,
                duration,
                accommodation_cost,
                constraints
            ),
            "budget_breakdown": self._generate_budget_breakdown(
                total_cost,
                accommodation_cost,
                search_results.get("flights", [])
            ),
            "generated_at": datetime.now(),
            "version": 1,
            "agent_feedback": {}
        }
        
        return itinerary
    
    def _get_weather_for_date(
        self,
        weather_data: Dict[str, List],
        destination: str,
        date: datetime
    ) -> Dict[str, Any]:
        """Get weather forecast for a specific date and destination"""
        
        if destination not in weather_data:
            return {
                "temperature_high": 75.0,
                "temperature_low": 65.0,
                "description": "Partly cloudy",
                "precipitation_chance": 20
            }
        
        weather_list = weather_data[destination]
        target_date = date.date()
        
        for weather in weather_list:
            if weather.date.date() == target_date:
                return {
                    "temperature_high": weather.temperature_high,
                    "temperature_low": weather.temperature_low,
                    "description": weather.description,
                    "precipitation_chance": weather.precipitation_chance,
                    "humidity": weather.humidity,
                    "wind_speed": weather.wind_speed
                }
        
        # Default weather if not found
        return {
            "temperature_high": 75.0,
            "temperature_low": 65.0,
            "description": "Partly cloudy",
            "precipitation_chance": 20,
            "humidity": 60,
            "wind_speed": 10.0
        }
    
    def _plan_daily_activities(
        self,
        day_num: int,
        destination: str,
        constraints: Dict[str, Any],
        search_results: Dict[str, Any],
        weather: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan activities for a single day"""
        
        activities = []
        pois = search_results.get("points_of_interest", {}).get(destination, {})
        activity_prefs = constraints.get("activity_preferences", ["sightseeing"])
        
        # Morning activity
        morning_activity = {
            "time": "9:00 AM",
            "name": "Morning Exploration",
            "type": "sightseeing",
            "location": destination,
            "duration": "2-3 hours",
            "cost": 15.0,
            "description": f"Start your day exploring {destination}",
            "weather_dependent": False
        }
        
        if "sightseeing" in pois and pois["sightseeing"]:
            poi = pois["sightseeing"][0]
            morning_activity.update({
                "name": poi.name,
                "description": poi.description or f"Visit {poi.name}",
                "cost": 15.0
            })
        
        activities.append(morning_activity)
        
        # Afternoon activity
        afternoon_activity = {
            "time": "2:00 PM",
            "name": "Afternoon Adventure",
            "type": activity_prefs[0] if activity_prefs else "sightseeing",
            "location": destination,
            "duration": "3-4 hours",
            "cost": 25.0,
            "description": f"Enjoy {activity_prefs[0] if activity_prefs else 'sightseeing'} in {destination}",
            "weather_dependent": True
        }
        
        if activity_prefs and activity_prefs[0] in pois and pois[activity_prefs[0]]:
            poi = pois[activity_prefs[0]][0]
            afternoon_activity.update({
                "name": poi.name,
                "description": poi.description or f"Experience {poi.name}",
                "cost": 25.0
            })
        
        activities.append(afternoon_activity)
        
        return activities
    
    def _plan_daily_meals(
        self,
        destination: str,
        constraints: Dict[str, Any],
        search_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan meals for a single day"""
        
        meals = []
        restaurant_pois = search_results.get("points_of_interest", {}).get(destination, {}).get("restaurant", [])
        
        # Breakfast
        breakfast = {
            "time": "8:00 AM",
            "type": "breakfast",
            "name": "Local Café",
            "cost": 12.0,
            "description": "Start your day with a local breakfast"
        }
        
        if restaurant_pois:
            breakfast.update({
                "name": restaurant_pois[0].name if len(restaurant_pois) > 0 else "Local Café",
                "description": f"Breakfast at {restaurant_pois[0].name}" if len(restaurant_pois) > 0 else "Local breakfast spot"
            })
        
        meals.append(breakfast)
        
        # Lunch
        lunch = {
            "time": "1:00 PM",
            "type": "lunch",
            "name": "Local Restaurant",
            "cost": 18.0,
            "description": "Enjoy local cuisine for lunch"
        }
        
        if len(restaurant_pois) > 1:
            lunch.update({
                "name": restaurant_pois[1].name,
                "description": f"Lunch at {restaurant_pois[1].name}"
            })
        
        meals.append(lunch)
        
        # Dinner
        dinner = {
            "time": "7:00 PM",
            "type": "dinner",
            "name": "Dinner Restaurant",
            "cost": 28.0,
            "description": "End your day with a delicious dinner"
        }
        
        if len(restaurant_pois) > 2:
            dinner.update({
                "name": restaurant_pois[2].name,
                "description": f"Dinner at {restaurant_pois[2].name}"
            })
        
        meals.append(dinner)
        
        return meals
    
    def _plan_daily_transportation(
        self,
        day_num: int,
        total_days: int,
        search_results: Dict[str, Any],
        destination: str
    ) -> List[Dict[str, Any]]:
        """Plan transportation for a single day"""
        
        transportation = []
        
        # First day - arrival
        if day_num == 0:
            flights = search_results.get("flights", [])
            if flights:
                flight = flights[0]  # Best flight option
                transportation.append({
                    "type": "flight",
                    "name": f"Flight to {destination}",
                    "time": flight.departure_date.strftime("%I:%M %p"),
                    "duration": flight.duration,
                    "cost": flight.price,
                    "description": f"{flight.airline} flight from {flight.origin} to {flight.destination}"
                })
            
            # Airport transfer
            transportation.append({
                "type": "transfer",
                "name": "Airport Transfer",
                "time": "Upon arrival",
                "duration": "30-45 minutes",
                "cost": 25.0,
                "description": "Transfer from airport to accommodation"
            })
        
        # Last day - departure
        elif day_num == total_days - 1:
            flights = search_results.get("flights", [])
            return_flights = [f for f in flights if f.origin == destination[:3].upper()]
            
            if return_flights:
                flight = return_flights[0]
                transportation.append({
                    "type": "flight",
                    "name": f"Return Flight",
                    "time": flight.departure_date.strftime("%I:%M %p"),
                    "duration": flight.duration,
                    "cost": 0.0,  # Already counted in arrival
                    "description": f"{flight.airline} return flight to {flight.destination}"
                })
        
        # Daily local transportation
        transportation.append({
            "type": "local",
            "name": "Local Transportation",
            "time": "As needed",
            "duration": "Various",
            "cost": 15.0,
            "description": "Public transport, taxis, or walking"
        })
        
        return transportation
    
    def _calculate_daily_cost(
        self,
        activities: List[Dict[str, Any]],
        meals: List[Dict[str, Any]],
        transportation: List[Dict[str, Any]],
        day_num: int,
        total_days: int,
        total_budget: float
    ) -> float:
        """Calculate the estimated cost for a single day"""
        
        daily_cost = 0.0
        
        # Activities
        for activity in activities:
            daily_cost += activity.get("cost", 0.0)
        
        # Meals
        for meal in meals:
            daily_cost += meal.get("cost", 0.0)
        
        # Transportation
        for transport in transportation:
            daily_cost += transport.get("cost", 0.0)
        
        return daily_cost
    
    def _calculate_accommodation_cost(
        self,
        duration: int,
        total_budget: float,
        current_cost: float,
        constraints: Dict[str, Any]
    ) -> float:
        """Calculate accommodation cost based on budget and preferences"""
        
        # Estimate accommodation as 30-40% of total budget
        accommodation_budget = total_budget * 0.35
        remaining_budget = total_budget - current_cost
        
        # Use the lower of the two
        accommodation_cost = min(accommodation_budget, remaining_budget * 0.6)
        
        # Adjust based on accommodation type preference
        accom_types = constraints.get("accommodation_type", ["hotel"])
        
        if "luxury" in str(constraints.get("travel_style", [])):
            accommodation_cost *= 1.5
        elif "budget" in str(constraints.get("travel_style", [])) or "hostel" in accom_types:
            accommodation_cost *= 0.6
        
        return max(accommodation_cost, duration * 30)  # Minimum $30/night
    
    def _generate_itinerary_title(self, destinations: List[str], duration: int) -> str:
        """Generate a catchy title for the itinerary"""
        
        if len(destinations) == 1:
            return f"{duration}-Day Adventure in {destinations[0]}"
        else:
            return f"{duration}-Day Multi-City Journey: {', '.join(destinations[:2])}"
    
    def _generate_itinerary_description(self, constraints: Dict[str, Any]) -> str:
        """Generate a description for the itinerary"""
        
        traveler_count = constraints.get("traveler_count", 1)
        traveler_types = constraints.get("traveler_types", ["solo"])
        travel_style = constraints.get("travel_style", ["general"])
        
        traveler_desc = "solo traveler" if traveler_count == 1 else f"{traveler_count} travelers"
        style_desc = ", ".join(travel_style[:2])
        
        return f"A {style_desc} itinerary designed for {traveler_desc}, featuring carefully selected activities, dining, and experiences."
    
    def _generate_highlights(
        self,
        days: List[Dict[str, Any]],
        search_results: Dict[str, Any]
    ) -> List[str]:
        """Generate highlights/summary for the itinerary"""
        
        highlights = []
        
        # Extract unique activities
        activities = set()
        for day in days:
            for activity in day.get("activities", []):
                if activity.get("name") != "Morning Exploration":
                    activities.add(activity.get("name", ""))
        
        highlights.extend(list(activities)[:3])
        
        # Add flight info
        flights = search_results.get("flights", [])
        if flights:
            highlights.append(f"Round-trip flights from ${flights[0].price:.0f}")
        
        # Add weather highlight
        highlights.append("Weather forecasts included for each day")
        
        return highlights[:5]
    
    def _generate_accommodation_summary(
        self,
        destination: str,
        duration: int,
        cost: float,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate accommodation summary"""
        
        accom_types = constraints.get("accommodation_type", ["hotel"])
        accom_type = accom_types[0] if accom_types else "hotel"
        
        return [{
            "type": accom_type,
            "location": destination,
            "nights": duration - 1,
            "total_cost": cost,
            "description": f"Comfortable {accom_type} accommodation in {destination}"
        }]
    
    def _generate_budget_breakdown(
        self,
        total_cost: float,
        accommodation_cost: float,
        flights: List[Any]
    ) -> Dict[str, float]:
        """Generate budget breakdown by category"""
        
        flight_cost = flights[0].price * 2 if flights else 420.0  # Round trip
        activity_cost = total_cost - accommodation_cost - flight_cost
        meal_cost = activity_cost * 0.6  # Estimate meals as 60% of activities+misc
        activity_cost = activity_cost * 0.4
        
        return {
            "flights": flight_cost,
            "accommodation": accommodation_cost,
            "activities": activity_cost,
            "meals": meal_cost,
            "transportation": total_cost * 0.1,
            "total": total_cost
        }
    
    async def _gather_travel_data_mock(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Gather travel data using mock services when external APIs fail"""
        
        destinations = constraints.get("destinations", ["Unknown City"])
        origin = constraints.get("origin", "Unknown Origin")
        start_date = constraints.get("start_date", datetime.now())
        end_date = constraints.get("end_date", start_date + timedelta(days=3))
        
        # Generate date range
        current_date = start_date
        dates = []
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        search_results = {
            "flights": [],
            "weather": {},
            "points_of_interest": {},
            "currency_info": {},
            "visa_info": {}
        }
        
        # Get mock data for each destination
        for destination in destinations:
            # Weather data
            weather = await mock_external_api_service.get_weather_forecast(destination, dates)
            search_results["weather"][destination] = [
                {
                    "date": w.date.isoformat(),
                    "temperature_high": w.temperature_high,
                    "temperature_low": w.temperature_low,
                    "description": w.description,
                    "humidity": w.humidity,
                    "wind_speed": w.wind_speed,
                    "precipitation_chance": w.precipitation_chance
                }
                for w in weather
            ]
            
            # Points of interest
            pois = await mock_external_api_service.search_points_of_interest(
                destination, ["restaurant", "attraction", "shopping"]
            )
            search_results["points_of_interest"][destination] = [
                {
                    "id": poi.id,
                    "name": poi.name,
                    "category": poi.category,
                    "rating": poi.rating,
                    "price_level": poi.price_level,
                    "description": poi.description
                }
                for poi in pois
            ]
            
            # Currency info
            search_results["currency_info"][destination] = await mock_external_api_service.get_currency_info(destination)
            
            # Visa info
            search_results["visa_info"][destination] = await mock_external_api_service.get_visa_requirements("USA", destination)
        
        # Flight data
        if origin != "Unknown Origin" and destinations:
            flights = await mock_external_api_service.search_flights(
                origin, destinations[0], start_date, end_date if len(dates) > 1 else None
            )
            search_results["flights"] = [
                {
                    "id": flight.id,
                    "origin": flight.origin,
                    "destination": flight.destination,
                    "departure_date": flight.departure_date.isoformat(),
                    "return_date": flight.return_date.isoformat() if flight.return_date else None,
                    "price": flight.price,
                    "currency": flight.currency,
                    "airline": flight.airline,
                    "duration": flight.duration,
                    "stops": flight.stops
                }
                for flight in flights
            ]
        
        return search_results
