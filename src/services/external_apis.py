"""
External API Services

Integrates with external APIs for travel data:
- OpenWeatherMap for weather forecasts
- Foursquare for points of interest
- Amadeus for flight and travel data
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

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
    arrival_date: datetime
    airline: str
    price: float
    currency: str
    duration: str
    stops: int


class ExternalAPIService:
    """Service for managing external API calls"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_weather_forecast(
        self, 
        location: str, 
        start_date: datetime, 
        days: int = 7
    ) -> List[WeatherData]:
        """
        Get weather forecast for a location and date range.
        
        Args:
            location: City name or coordinates
            start_date: Start date for forecast
            days: Number of days to forecast
            
        Returns:
            List of weather data for each day
        """
        if not config.OPENWEATHER_API_KEY:
            return self._mock_weather_data(location, start_date, days)
        
        try:
            # First, get coordinates for the location
            geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
            geocoding_params = {
                "q": location,
                "limit": 1,
                "appid": config.OPENWEATHER_API_KEY
            }
            
            async with self.session.get(geocoding_url, params=geocoding_params) as response:
                geo_data = await response.json()
                
                if not geo_data:
                    return self._mock_weather_data(location, start_date, days)
                
                lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
            
            # Get weather forecast
            forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                "lat": lat,
                "lon": lon,
                "appid": config.OPENWEATHER_API_KEY,
                "units": "imperial"  # Fahrenheit
            }
            
            async with self.session.get(forecast_url, params=forecast_params) as response:
                forecast_data = await response.json()
                
                return self._parse_weather_data(forecast_data, location, start_date, days)
        
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._mock_weather_data(location, start_date, days)
    
    def _parse_weather_data(
        self, 
        forecast_data: Dict, 
        location: str, 
        start_date: datetime, 
        days: int
    ) -> List[WeatherData]:
        """Parse OpenWeatherMap API response"""
        weather_list = []
        
        # Group forecasts by day
        daily_forecasts = {}
        
        for item in forecast_data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.date()
            
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = []
            daily_forecasts[date_key].append(item)
        
        # Create weather data for each day
        current_date = start_date.date()
        for i in range(days):
            target_date = current_date + timedelta(days=i)
            
            if target_date in daily_forecasts:
                day_data = daily_forecasts[target_date]
                
                # Calculate daily summary
                temps = [item["main"]["temp"] for item in day_data]
                weather_list.append(WeatherData(
                    location=location,
                    date=datetime.combine(target_date, datetime.min.time()),
                    temperature_high=max(temps),
                    temperature_low=min(temps),
                    description=day_data[0]["weather"][0]["description"],
                    humidity=day_data[0]["main"]["humidity"],
                    wind_speed=day_data[0]["wind"]["speed"],
                    precipitation_chance=0  # Not always available
                ))
        
        return weather_list
    
    def _mock_weather_data(
        self, 
        location: str, 
        start_date: datetime, 
        days: int
    ) -> List[WeatherData]:
        """Generate mock weather data when API is not available"""
        weather_list = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            weather_list.append(WeatherData(
                location=location,
                date=date,
                temperature_high=75.0,
                temperature_low=65.0,
                description="Partly cloudy",
                humidity=60,
                wind_speed=10.0,
                precipitation_chance=20
            ))
        
        return weather_list
    
    async def search_points_of_interest(
        self, 
        location: str, 
        category: str = "restaurant", 
        limit: int = 10
    ) -> List[PointOfInterest]:
        """
        Search for points of interest using Foursquare API.
        
        Args:
            location: Location to search near
            category: Category of POIs (restaurant, attraction, etc.)
            limit: Maximum number of results
            
        Returns:
            List of points of interest
        """
        if not config.FOURSQUARE_API_KEY:
            return self._mock_poi_data(location, category, limit)
        
        try:
            url = "https://api.foursquare.com/v3/places/search"
            headers = {
                "Authorization": config.FOURSQUARE_API_KEY,
                "Accept": "application/json"
            }
            params = {
                "near": location,
                "categories": self._get_foursquare_category_id(category),
                "limit": limit
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                return self._parse_poi_data(data)
        
        except Exception as e:
            print(f"Foursquare API error: {e}")
            return self._mock_poi_data(location, category, limit)
    
    def _get_foursquare_category_id(self, category: str) -> str:
        """Map category names to Foursquare category IDs"""
        category_map = {
            "restaurant": "13065",
            "attraction": "16000",
            "hotel": "19014",
            "shopping": "17000",
            "nightlife": "10000"
        }
        return category_map.get(category, "13065")  # Default to restaurant
    
    def _parse_poi_data(self, data: Dict) -> List[PointOfInterest]:
        """Parse Foursquare API response"""
        pois = []
        
        for place in data.get("results", []):
            poi = PointOfInterest(
                id=place.get("fsq_id", ""),
                name=place.get("name", ""),
                category=place.get("categories", [{}])[0].get("name", ""),
                location=place.get("location", {}),
                rating=place.get("rating"),
                price_level=place.get("price"),
                description=place.get("description"),
                photos=[]
            )
            pois.append(poi)
        
        return pois
    
    def _mock_poi_data(self, location: str, category: str, limit: int) -> List[PointOfInterest]:
        """Generate mock POI data when API is not available"""
        pois = []
        
        for i in range(min(limit, 5)):
            poi = PointOfInterest(
                id=f"mock_{i}",
                name=f"Sample {category.title()} {i+1}",
                category=category,
                location={"address": f"123 Main St, {location}"},
                rating=4.0 + (i * 0.2),
                price_level=2,
                description=f"A great {category} in {location}",
                photos=[]
            )
            pois.append(poi)
        
        return pois
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime] = None,
        adults: int = 1
    ) -> List[FlightOffer]:
        """
        Search for flight offers using Amadeus API.
        
        Args:
            origin: Origin airport code or city
            destination: Destination airport code or city
            departure_date: Departure date
            return_date: Return date (for round trip)
            adults: Number of adult passengers
            
        Returns:
            List of flight offers
        """
        if not config.AMADEUS_CLIENT_ID or not config.AMADEUS_CLIENT_SECRET:
            return self._mock_flight_data(origin, destination, departure_date, return_date)
        
        try:
            # First, get access token
            token = await self._get_amadeus_token()
            if not token:
                return self._mock_flight_data(origin, destination, departure_date, return_date)
            
            # Search for flights
            url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "originLocationCode": origin[:3].upper(),  # Convert to airport code
                "destinationLocationCode": destination[:3].upper(),
                "departureDate": departure_date.strftime("%Y-%m-%d"),
                "adults": adults
            }
            
            if return_date:
                params["returnDate"] = return_date.strftime("%Y-%m-%d")
            
            async with self.session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                return self._parse_flight_data(data)
        
        except Exception as e:
            print(f"Amadeus API error: {e}")
            return self._mock_flight_data(origin, destination, departure_date, return_date)
    
    async def _get_amadeus_token(self) -> Optional[str]:
        """Get access token for Amadeus API"""
        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": config.AMADEUS_CLIENT_ID,
                "client_secret": config.AMADEUS_CLIENT_SECRET
            }
            
            async with self.session.post(url, data=data) as response:
                token_data = await response.json()
                return token_data.get("access_token")
        
        except Exception as e:
            print(f"Amadeus token error: {e}")
            return None
    
    def _parse_flight_data(self, data: Dict) -> List[FlightOffer]:
        """Parse Amadeus API response"""
        flights = []
        
        for offer in data.get("data", []):
            itinerary = offer["itineraries"][0]  # First itinerary
            segment = itinerary["segments"][0]  # First segment
            
            flight = FlightOffer(
                id=offer["id"],
                origin=segment["departure"]["iataCode"],
                destination=segment["arrival"]["iataCode"],
                departure_date=datetime.fromisoformat(segment["departure"]["at"]),
                arrival_date=datetime.fromisoformat(segment["arrival"]["at"]),
                airline=segment["carrierCode"],
                price=float(offer["price"]["total"]),
                currency=offer["price"]["currency"],
                duration=itinerary["duration"],
                stops=len(itinerary["segments"]) - 1
            )
            flights.append(flight)
        
        return flights
    
    def _mock_flight_data(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        return_date: Optional[datetime]
    ) -> List[FlightOffer]:
        """Generate mock flight data when API is not available"""
        flights = []
        
        # Mock outbound flight
        flights.append(FlightOffer(
            id="mock_outbound",
            origin=origin[:3].upper(),
            destination=destination[:3].upper(),
            departure_date=departure_date,
            arrival_date=departure_date + timedelta(hours=3),
            airline="JetBlue",
            price=210.0,
            currency="USD",
            duration="PT3H0M",
            stops=0
        ))
        
        # Mock return flight if needed
        if return_date:
            flights.append(FlightOffer(
                id="mock_return",
                origin=destination[:3].upper(),
                destination=origin[:3].upper(),
                departure_date=return_date,
                arrival_date=return_date + timedelta(hours=3),
                airline="JetBlue",
                price=210.0,
                currency="USD",
                duration="PT3H0M",
                stops=0
            ))
        
        return flights


# Convenience function for easy access
async def get_api_service() -> ExternalAPIService:
    """Get an instance of the API service"""
    return ExternalAPIService()
