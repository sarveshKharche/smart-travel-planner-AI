"""
Query Parser Agent

Extracts structured data from natural language travel queries.
Identifies destinations, dates, budget, preferences, and constraints.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dateutil import parser as date_parser

from ..models.state import AgentState, ParsedConstraints, AgentRole
from ..config import config
from .base_agent import BaseAgent


class QueryParserAgent(BaseAgent):
    """
    Agent responsible for parsing natural language travel queries into structured data.
    
    Extracts:
    - Destinations and origin
    - Travel dates and duration
    - Budget constraints
    - Traveler information
    - Preferences and requirements
    """
    
    def __init__(self):
        super().__init__(AgentRole.QUERY_PARSER)
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s*\d{4})?\b',
        ]
        
        self.budget_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 1000 dollars
            r'budget.*?(\d{1,3}(?:,\d{3})*)',  # budget of 1000
            r'under.*?\$?(\d{1,3}(?:,\d{3})*)',  # under $1000
        ]
    
    async def process(self, state: AgentState) -> AgentState:
        """Process the user query and extract structured constraints"""
        
        self.log_execution(state, "Starting query parsing")
        
        try:
            # Parse the query using AI assistance
            parsed_data = await self._parse_with_ai(state["user_query"])
            
            # Extract specific components
            constraints = ParsedConstraints(
                origin=self._extract_origin(state["user_query"], parsed_data),
                destinations=self._extract_destinations(state["user_query"], parsed_data),
                start_date=self._extract_start_date(state["user_query"], parsed_data),
                end_date=self._extract_end_date(state["user_query"], parsed_data),
                duration_days=self._extract_duration(state["user_query"], parsed_data),
                total_budget=self._extract_budget(state["user_query"], parsed_data),
                budget_currency=self._extract_currency(state["user_query"], parsed_data),
                traveler_count=self._extract_traveler_count(state["user_query"], parsed_data),
                traveler_types=self._extract_traveler_types(state["user_query"], parsed_data),
                travel_style=self._extract_travel_style(state["user_query"], parsed_data),
                accommodation_type=self._extract_accommodation_type(state["user_query"], parsed_data),
                transportation_modes=self._extract_transportation(state["user_query"], parsed_data),
                activity_preferences=self._extract_activities(state["user_query"], parsed_data),
                dietary_restrictions=self._extract_dietary_restrictions(state["user_query"], parsed_data),
                accessibility_needs=self._extract_accessibility_needs(state["user_query"], parsed_data),
                must_have=self._extract_must_have(state["user_query"], parsed_data),
                must_avoid=self._extract_must_avoid(state["user_query"], parsed_data),
                flexibility=self._extract_flexibility(state["user_query"], parsed_data),
            )
            
            # Update state
            state["parsed_constraints"] = constraints
            state["current_agent"] = AgentRole.QUERY_PARSER
            
            self.log_execution(state, f"Successfully parsed query. Found {len(constraints['destinations'])} destinations, budget: {constraints['total_budget']}")
            
            return state
            
        except Exception as e:
            self.log_execution(state, f"Error parsing query: {str(e)}")
            raise
    
    async def _parse_with_ai(self, query: str) -> Dict[str, Any]:
        """Use AI to help parse the query"""
        
        prompt = f"""
        Parse the following travel query and extract key information in JSON format:
        
        Query: "{query}"
        
        Please extract and return JSON with these fields:
        {{
            "origin": "departure city/location",
            "destinations": ["destination1", "destination2"],
            "dates": {{
                "start": "YYYY-MM-DD or relative like 'next month'",
                "end": "YYYY-MM-DD or relative",
                "duration": "number of days if mentioned"
            }},
            "budget": {{
                "amount": number,
                "currency": "USD/EUR/etc",
                "type": "total/daily/per_person"
            }},
            "travelers": {{
                "count": number,
                "type": "solo/couple/family/friends"
            }},
            "preferences": {{
                "style": ["adventure", "relaxation", "culture", "food"],
                "accommodation": ["hotel", "hostel", "airbnb"],
                "transportation": ["flight", "car", "train"],
                "activities": ["hiking", "museums", "nightlife"]
            }},
            "requirements": {{
                "must_have": ["specific requirements"],
                "must_avoid": ["things to avoid"],
                "accessibility": ["any accessibility needs"],
                "dietary": ["dietary restrictions"]
            }}
        }}
        
        Only return valid JSON, no other text.
        """
        
        try:
            response = await self.call_bedrock(prompt)
            return json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning(f"AI parsing failed, falling back to regex: {e}")
            return {}
    
    def _extract_origin(self, query: str, ai_data: Dict) -> Optional[str]:
        """Extract origin/departure location"""
        if ai_data.get("origin"):
            return ai_data["origin"]
        
        # Look for common patterns
        patterns = [
            r'from\s+([A-Za-z\s]+?)(?:\s+to|\s+in|\s*[,.])',
            r'based\s+in\s+([A-Za-z\s]+?)(?:\s+and|\s*[,.])',
            r'departing\s+from\s+([A-Za-z\s]+?)(?:\s+to|\s*[,.])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_destinations(self, query: str, ai_data: Dict) -> List[str]:
        """Extract destination locations"""
        if ai_data.get("destinations"):
            return ai_data["destinations"]
        
        destinations = []
        
        # Look for common destination patterns
        patterns = [
            r'to\s+([A-Za-z\s]+?)(?:\s+for|\s+in|\s*[,.])',
            r'visit\s+([A-Za-z\s]+?)(?:\s+for|\s+in|\s*[,.])',
            r'trip\s+to\s+([A-Za-z\s]+?)(?:\s+for|\s+in|\s*[,.])',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            destinations.extend([match.strip() for match in matches])
        
        return list(set(destinations)) if destinations else ["Unknown"]
    
    def _extract_start_date(self, query: str, ai_data: Dict) -> Optional[datetime]:
        """Extract start date"""
        if ai_data.get("dates", {}).get("start"):
            try:
                return date_parser.parse(ai_data["dates"]["start"])
            except:
                pass
        
        # Try to find dates in query
        for pattern in self.date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                try:
                    return date_parser.parse(matches[0])
                except:
                    continue
        
        # Look for relative dates
        relative_patterns = [
            (r'next\s+week', 7),
            (r'next\s+month', 30),
            (r'in\s+(\d+)\s+days?', None),
            (r'in\s+a\s+week', 7),
            (r'in\s+a\s+month', 30),
        ]
        
        for pattern, days in relative_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if days is None:
                    days = int(match.group(1))
                return datetime.now() + timedelta(days=days)
        
        # Default: start tomorrow if no date specified
        return datetime.now() + timedelta(days=1)
    
    def _extract_end_date(self, query: str, ai_data: Dict) -> Optional[datetime]:
        """Extract end date"""
        if ai_data.get("dates", {}).get("end"):
            try:
                return date_parser.parse(ai_data["dates"]["end"])
            except:
                pass
        
        # If we have start date and duration, calculate end date
        start_date = self._extract_start_date(query, ai_data)
        duration = self._extract_duration(query, ai_data)
        
        if start_date is not None and duration is not None:
            return start_date + timedelta(days=duration)
        
        # Fallback: if no specific dates, assume a 3-day trip starting tomorrow
        if duration is not None:
            from datetime import datetime
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow + timedelta(days=duration)
        
        return None
    
    def _extract_duration(self, query: str, ai_data: Dict) -> Optional[int]:
        """Extract trip duration in days"""
        if ai_data.get("dates", {}).get("duration"):
            try:
                return int(ai_data["dates"]["duration"])
            except:
                pass
        
        patterns = [
            r'(\d+)\s*days?',
            r'(\d+)\s*nights?',
            r'(\d+)\s*day\s+trip',
            r'weekend',  # 2-3 days
            r'week',     # 7 days
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if pattern == r'weekend':
                    return 3
                elif pattern == r'week':
                    return 7
                else:
                    return int(match.group(1))
        
        return None
    
    def _extract_budget(self, query: str, ai_data: Dict) -> Optional[float]:
        """Extract budget amount"""
        if ai_data.get("budget", {}).get("amount"):
            return float(ai_data["budget"]["amount"])
        
        for pattern in self.budget_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_currency(self, query: str, ai_data: Dict) -> str:
        """Extract currency, default to USD"""
        if ai_data.get("budget", {}).get("currency"):
            return ai_data["budget"]["currency"]
        
        # Look for currency symbols or codes
        currency_patterns = [
            (r'\$', 'USD'),
            (r'€', 'EUR'),
            (r'£', 'GBP'),
            (r'\bUSD\b', 'USD'),
            (r'\bEUR\b', 'EUR'),
            (r'\bGBP\b', 'GBP'),
        ]
        
        for pattern, currency in currency_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return currency
        
        return 'USD'  # Default
    
    def _extract_traveler_count(self, query: str, ai_data: Dict) -> int:
        """Extract number of travelers"""
        if ai_data.get("travelers", {}).get("count"):
            return int(ai_data["travelers"]["count"])
        
        # Look for explicit numbers
        patterns = [
            r'(\d+)\s+people',
            r'(\d+)\s+travelers?',
            r'(\d+)\s+of\s+us',
            r'group\s+of\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Look for implicit indicators
        if re.search(r'\bwe\b|\bus\b|\bour\b', query, re.IGNORECASE):
            return 2  # Assume couple
        elif re.search(r'\bi\b|\bme\b|\bmy\b|\bsolo\b', query, re.IGNORECASE):
            return 1
        
        return 1  # Default to solo
    
    def _extract_traveler_types(self, query: str, ai_data: Dict) -> List[str]:
        """Extract traveler type"""
        if ai_data.get("travelers", {}).get("type"):
            return [ai_data["travelers"]["type"]]
        
        types = []
        
        type_patterns = [
            (r'\bsolo\b|\balone\b|\bmyself\b', 'solo'),
            (r'\bcouple\b|\bpartner\b|\bboyfriend\b|\bgirlfriend\b|\bspouse\b', 'couple'),
            (r'\bfamily\b|\bkids\b|\bchildren\b', 'family'),
            (r'\bfriends\b|\bbuddies\b|\bgroup\b', 'friends'),
        ]
        
        for pattern, travel_type in type_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                types.append(travel_type)
        
        return types if types else ['solo']
    
    def _extract_travel_style(self, query: str, ai_data: Dict) -> List[str]:
        """Extract travel style preferences"""
        if ai_data.get("preferences", {}).get("style"):
            return ai_data["preferences"]["style"]
        
        styles = []
        
        style_patterns = [
            (r'\badventure\b|\bhiking\b|\bextreme\b|\boutdoor\b', 'adventure'),
            (r'\brelax\b|\bchill\b|\bpeaceful\b|\bquiet\b', 'relaxation'),
            (r'\bculture\b|\bhistory\b|\bmuseum\b|\bart\b', 'culture'),
            (r'\bfood\b|\bculinary\b|\brestaurant\b|\beating\b', 'food'),
            (r'\bnightlife\b|\bparty\b|\bbar\b|\bclub\b', 'nightlife'),
            (r'\bbeach\b|\bsun\b|\bocean\b|\bcoast\b', 'beach'),
            (r'\bnature\b|\bpark\b|\bforest\b|\bmountain\b', 'nature'),
            (r'\bbudget\b|\bcheap\b|\baffordable\b', 'budget'),
            (r'\bluxury\b|\bupscale\b|\bfancy\b', 'luxury'),
        ]
        
        for pattern, style in style_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                styles.append(style)
        
        return styles if styles else ['general']
    
    def _extract_accommodation_type(self, query: str, ai_data: Dict) -> List[str]:
        """Extract accommodation preferences"""
        if ai_data.get("preferences", {}).get("accommodation"):
            return ai_data["preferences"]["accommodation"]
        
        accommodations = []
        
        patterns = [
            (r'\bhotel\b|\bresort\b', 'hotel'),
            (r'\bhostel\b|\bdorm\b', 'hostel'),
            (r'\bairbnb\b|\bapartment\b|\brental\b', 'airbnb'),
            (r'\bcamping\b|\bcamp\b|\btent\b', 'camping'),
            (r'\bb&b\b|\bbed\s+and\s+breakfast\b', 'bnb'),
        ]
        
        for pattern, accom_type in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                accommodations.append(accom_type)
        
        return accommodations if accommodations else ['hotel']
    
    def _extract_transportation(self, query: str, ai_data: Dict) -> List[str]:
        """Extract transportation preferences"""
        if ai_data.get("preferences", {}).get("transportation"):
            return ai_data["preferences"]["transportation"]
        
        transport = []
        
        patterns = [
            (r'\bflight\b|\bfly\b|\bplane\b|\bair\b', 'flight'),
            (r'\bcar\b|\bdrive\b|\bdriving\b|\broad\s+trip\b', 'car'),
            (r'\btrain\b|\brail\b', 'train'),
            (r'\bbus\b', 'bus'),
            (r'\bwalk\b|\bwalking\b', 'walking'),
            (r'\bbike\b|\bcycling\b', 'bike'),
        ]
        
        for pattern, transport_type in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                transport.append(transport_type)
        
        return transport if transport else ['flight']
    
    def _extract_activities(self, query: str, ai_data: Dict) -> List[str]:
        """Extract activity preferences"""
        if ai_data.get("preferences", {}).get("activities"):
            return ai_data["preferences"]["activities"]
        
        activities = []
        
        patterns = [
            (r'\bhiking\b|\bhike\b|\btrail\b', 'hiking'),
            (r'\bmuseum\b|\bgallery\b', 'museums'),
            (r'\bshopping\b|\bmarket\b', 'shopping'),
            (r'\bfood\b|\beating\b|\brestaurant\b', 'dining'),
            (r'\bnightlife\b|\bbar\b|\bclub\b', 'nightlife'),
            (r'\bsightseeing\b|\btourist\b', 'sightseeing'),
            (r'\bbeach\b|\bswimming\b', 'beach'),
            (r'\bphotography\b|\bphoto\b', 'photography'),
        ]
        
        for pattern, activity in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                activities.append(activity)
        
        return activities if activities else ['sightseeing']
    
    def _extract_dietary_restrictions(self, query: str, ai_data: Dict) -> List[str]:
        """Extract dietary restrictions"""
        if ai_data.get("requirements", {}).get("dietary"):
            return ai_data["requirements"]["dietary"]
        
        restrictions = []
        
        patterns = [
            (r'\bvegetarian\b|\bveggie\b', 'vegetarian'),
            (r'\bvegan\b', 'vegan'),
            (r'\bgluten.free\b|\bceliac\b', 'gluten-free'),
            (r'\bhalal\b', 'halal'),
            (r'\bkosher\b', 'kosher'),
            (r'\ballergy\b|\ballergic\b', 'allergies'),
        ]
        
        for pattern, restriction in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                restrictions.append(restriction)
        
        return restrictions
    
    def _extract_accessibility_needs(self, query: str, ai_data: Dict) -> List[str]:
        """Extract accessibility requirements"""
        if ai_data.get("requirements", {}).get("accessibility"):
            return ai_data["requirements"]["accessibility"]
        
        needs = []
        
        patterns = [
            (r'\bwheelchair\b|\bmobility\b', 'wheelchair-accessible'),
            (r'\bvisual\b|\bblind\b', 'visual-impairment'),
            (r'\bhearing\b|\bdeaf\b', 'hearing-impairment'),
            (r'\baccessible\b|\bdisability\b', 'general-accessibility'),
        ]
        
        for pattern, need in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                needs.append(need)
        
        return needs
    
    def _extract_must_have(self, query: str, ai_data: Dict) -> List[str]:
        """Extract must-have requirements"""
        if ai_data.get("requirements", {}).get("must_have"):
            return ai_data["requirements"]["must_have"]
        
        must_haves = []
        
        patterns = [
            r'must\s+have\s+([^.,]+)',
            r'need\s+to\s+([^.,]+)',
            r'require\s+([^.,]+)',
            r'essential\s+([^.,]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            must_haves.extend([match.strip() for match in matches])
        
        return must_haves
    
    def _extract_must_avoid(self, query: str, ai_data: Dict) -> List[str]:
        """Extract things to avoid"""
        if ai_data.get("requirements", {}).get("must_avoid"):
            return ai_data["requirements"]["must_avoid"]
        
        avoid = []
        
        patterns = [
            r'avoid\s+([^.,]+)',
            r'not\s+([^.,]+)',
            r'no\s+([^.,]+)',
            r'don\'t\s+want\s+([^.,]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            avoid.extend([match.strip() for match in matches])
        
        return avoid
    
    def _extract_flexibility(self, query: str, ai_data: Dict) -> Dict[str, str]:
        """Extract flexibility indicators"""
        flexibility = {
            "dates": "medium",
            "budget": "medium",
            "destinations": "medium"
        }
        
        if re.search(r'\bflexible\b|\bopen\b', query, re.IGNORECASE):
            flexibility["dates"] = "high"
            flexibility["destinations"] = "high"
        
        if re.search(r'\bexact\b|\bspecific\b|\bmust\b', query, re.IGNORECASE):
            flexibility["dates"] = "low"
            flexibility["budget"] = "low"
        
        return flexibility
