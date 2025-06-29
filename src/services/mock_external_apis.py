"""
Mock External API Services - For Development and Testing

Provides realistic mock data when external APIs are unavailable.
This ensures the system can run end-to-end even without proper API keys or network access.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random

from ..config import config


@dataclass
class WeatherData:
    """Weather forecast data"""
    location: str
    date: datetime
    temperature_high: float
    temperature_low: float
    description: str
    humidity: int
    wind_speed: float
    precipitation_chance: int


@dataclass
class PointOfInterest:
    """Point of interest data from Foursquare"""
    id: str
    name: str
    category: str
    location: Dict[str, Any]
    rating: Optional[float]
    price_level: Optional[int]
    description: Optional[str]
    photos: List[str]


@dataclass
class FlightOffer:
    """Flight offer data from Amadeus"""
    id: str
    origin: str
    destination: str
    departure_date: datetime
    return_date: Optional[datetime]
    price: float
    currency: str
    airline: str
    duration: str
    stops: int


class MockExternalAPIService:
    """
    Mock implementation of external API services.
    Returns realistic data for testing and development.
    """
    
    def __init__(self):
        self.config = config
        
        # Sample data pools
        self.weather_descriptions = [
            "Sunny", "Partly Cloudy", "Cloudy", "Light Rain", 
            "Clear", "Scattered Clouds", "Overcast"
        ]
        
        self.airlines = [
            "Delta", "American Airlines", "United", "JetBlue", 
            "Southwest", "Alaska Airlines", "Spirit"
        ]
        
        # Mock POI data by category
        self.mock_pois = {
            "restaurant": [
                "The Local Bistro", "Sunset Grill", "Corner Café", 
                "Ocean View Restaurant", "Mountain Lodge Dining"
            ],
            "attraction": [
                "City Museum", "Historic Downtown", "Waterfront Park",
                "Art Gallery", "Scenic Overlook"
            ],
            "shopping": [
                "Local Market", "Artisan Shops", "Downtown Mall",
                "Vintage Boutiques", "Craft Center"
            ]
        }
    
    async def get_weather_forecast(self, location: str, dates: List[datetime]) -> List[WeatherData]:
        """
        Get weather forecast for a location and date range.
        
        Args:
            location: City/region name
            dates: List of dates to get forecasts for
            
        Returns:
            List of weather forecasts
        """
        try:
            print(f"🌤️  Getting weather forecast for {location}")
            await asyncio.sleep(0.1)  # Simulate API delay
            
            forecasts = []
            for date in dates:
                # Generate realistic weather data
                base_temp = 75 if "beach" in location.lower() else 65
                temp_variation = random.randint(-15, 15)
                
                forecast = WeatherData(
                    location=location,
                    date=date,
                    temperature_high=base_temp + temp_variation + random.randint(5, 15),
                    temperature_low=base_temp + temp_variation - random.randint(5, 15),
                    description=random.choice(self.weather_descriptions),
                    humidity=random.randint(30, 80),
                    wind_speed=random.randint(5, 25),
                    precipitation_chance=random.randint(0, 40)
                )
                forecasts.append(forecast)
            
            return forecasts
            
        except Exception as e:
            print(f"Weather API error: {e}")
            # Return default forecast
            return [WeatherData(
                location=location,
                date=dates[0] if dates else datetime.now(),
                temperature_high=75,
                temperature_low=65,
                description="Pleasant",
                humidity=50,
                wind_speed=10,
                precipitation_chance=20
            )]
    
    async def search_points_of_interest(self, location: str, categories: Optional[List[str]] = None) -> List[PointOfInterest]:
        """
        Search for points of interest in a location.
        
        Args:
            location: City/region name
            categories: List of categories to search for
            
        Returns:
            List of points of interest
        """
        try:
            print(f"📍 Searching POIs in {location}")
            await asyncio.sleep(0.1)  # Simulate API delay
            
            if not categories:
                categories = ["restaurant", "attraction", "shopping"]
            
            pois = []
            for category in categories:
                category_pois = self.mock_pois.get(category, ["Local Spot"])
                
                for i, poi_name in enumerate(category_pois[:3]):  # Limit to 3 per category
                    poi = PointOfInterest(
                        id=f"{category}_{location}_{i}",
                        name=f"{poi_name} - {location}",
                        category=category.title(),
                        location={
                            "city": location,
                            "lat": 40.7128 + random.uniform(-1, 1),
                            "lng": -74.0060 + random.uniform(-1, 1)
                        },
                        rating=round(random.uniform(3.5, 4.8), 1),
                        price_level=random.randint(1, 4),
                        description=f"Popular {category} in {location} with great reviews",
                        photos=[f"photo_{i}.jpg"]
                    )
                    pois.append(poi)
            
            return pois
            
        except Exception as e:
            print(f"Foursquare API error: {e}")
            return []
    
    async def search_flights(self, origin: str, destination: str, departure_date: datetime, 
                           return_date: Optional[datetime] = None) -> List[FlightOffer]:
        """
        Search for flight offers.
        
        Args:
            origin: Origin city/airport code
            destination: Destination city/airport code
            departure_date: Departure date
            return_date: Return date for round trip
            
        Returns:
            List of flight offers
        """
        try:
            print(f"✈️  Searching flights {origin} → {destination}")
            await asyncio.sleep(0.2)  # Simulate API delay
            
            flights = []
            
            # Generate 2-3 flight options
            for i in range(random.randint(2, 3)):
                base_price = random.randint(200, 800)
                
                flight = FlightOffer(
                    id=f"flight_{origin}_{destination}_{i}",
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    price=base_price + random.randint(-50, 200),
                    currency="USD",
                    airline=random.choice(self.airlines),
                    duration=f"{random.randint(2, 8)}h {random.randint(0, 55)}m",
                    stops=random.randint(0, 1)
                )
                flights.append(flight)
            
            return sorted(flights, key=lambda x: x.price)
            
        except Exception as e:
            print(f"Amadeus token error: {e}")
            return []
    
    async def get_currency_info(self, country: str) -> Dict[str, Any]:
        """
        Get currency information for a country.
        
        Args:
            country: Country name
            
        Returns:
            Currency information
        """
        currency_map = {
            "japan": {"code": "JPY", "symbol": "¥", "rate": 110.0},
            "france": {"code": "EUR", "symbol": "€", "rate": 0.85},
            "thailand": {"code": "THB", "symbol": "฿", "rate": 33.0},
            "costa rica": {"code": "CRC", "symbol": "₡", "rate": 600.0},
            "portugal": {"code": "EUR", "symbol": "€", "rate": 0.85},
        }
        
        country_lower = country.lower()
        for key, value in currency_map.items():
            if key in country_lower:
                return value
        
        # Default to USD
        return {"code": "USD", "symbol": "$", "rate": 1.0}
    
    async def get_visa_requirements(self, origin_country: str, destination_country: str) -> Dict[str, Any]:
        """
        Get visa requirements for travel.
        
        Args:
            origin_country: Origin country
            destination_country: Destination country
            
        Returns:
            Visa requirement information
        """
        # Simplified visa info
        if destination_country.lower() in ["canada", "mexico"]:
            return {"required": False, "note": "Passport required"}
        elif destination_country.lower() in ["japan", "thailand", "costa rica"]:
            return {"required": False, "note": "Tourist visa on arrival, valid passport required"}
        else:
            return {"required": True, "note": "Check embassy requirements"}


# Create a mock service instance
mock_external_api_service = MockExternalAPIService()
