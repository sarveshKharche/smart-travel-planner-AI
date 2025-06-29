"""
Simplified Streamlit Frontend for Smart Travel Planner AI

A clean, focused interface for creating AI-powered travel itineraries.
"""

import streamlit as st
import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configuration for API backend
CLOUD_API_ENDPOINT = "https://oydiuxox5d.execute-api.us-east-1.amazonaws.com/dev/plan"

class APIClient:
    """Client for communicating with both local and cloud backends"""
    
    def __init__(self, use_cloud: bool = False):
        self.use_cloud = use_cloud
        self.local_app = None
        
        if not use_cloud:
            try:
                from src.core.application import TravelPlannerApp
                self.local_app = TravelPlannerApp()
            except ImportError as e:
                st.warning(f"Local backend not available: {e}")
                st.info("Using cloud backend instead...")
                self.use_cloud = True
    
    async def process_travel_request(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process travel request using either local or cloud backend"""
        
        if self.use_cloud:
            return await self._call_cloud_api(query, session_id)
        else:
            if self.local_app is None:
                raise Exception("Local backend not available")
            return await self.local_app.process_travel_request(query, session_id)
    
    async def _call_cloud_api(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Call the deployed AWS API"""
        try:
            payload = {"query": query}
            if session_id:
                payload["session_id"] = session_id
            
            response = requests.post(
                CLOUD_API_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API call failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            st.error(f"Cloud API error: {e}")
            raise

# Set page config
st.set_page_config(
    page_title="Smart Travel Planner AI",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .itinerary-day {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .cost-highlight {
        background: #e8f4fd;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #0066cc;
        margin: 0.5rem 0;
    }
    
    .sample-query {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        cursor: pointer;
    }
    
    .sample-query:hover {
        background: #e6f3ff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_client' not in st.session_state:
    # Default to cloud API for better reliability
    st.session_state.api_client = APIClient(use_cloud=True)

if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

def display_itinerary(itinerary: Dict[str, Any]):
    """Display the itinerary in a beautiful format matching the blueprint examples"""
    
    # Header with key details
    st.markdown(f"""
    ## 🌟 {itinerary.get('title', 'Your Travel Itinerary')}
    """)
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="cost-highlight">
        <strong>💰 Total Cost</strong><br>
        ${itinerary.get('total_cost', 0):,.0f} {itinerary.get('currency', 'USD')}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="cost-highlight">
        <strong>📅 Duration</strong><br>
        {itinerary.get('duration_days', 0)} days
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        destinations = itinerary.get('destinations', [])
        dest_text = destinations[0] if destinations else "Multiple"
        st.markdown(f"""
        <div class="cost-highlight">
        <strong>📍 Destination</strong><br>
        {dest_text}
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="cost-highlight">
        <strong>👥 Travelers</strong><br>
        {itinerary.get('traveler_count', 1)} person(s)
        </div>
        """, unsafe_allow_html=True)
    
    # Description
    if itinerary.get('description'):
        st.write(itinerary['description'])
    
    # Flight information if available
    flights = itinerary.get('total_flights', [])
    if flights:
        st.subheader("✈️ Flights")
        for flight in flights:
            st.write(f"• **{flight.get('origin', '')} → {flight.get('destination', '')}**: ${flight.get('price', 0):.0f} via {flight.get('airline', 'Airline')}")
    
    # Accommodation summary
    accommodations = itinerary.get('accommodations_summary', [])
    if accommodations:
        st.subheader("🏨 Accommodations")
        for acc in accommodations:
            st.write(f"• **{acc.get('name', 'Hotel')}**: ${acc.get('total_cost', 0):.0f} for {acc.get('nights', 0)} nights")
    
    # Daily itinerary
    days = itinerary.get('days', [])
    if days:
        st.subheader("🗓️ Daily Itinerary")
        
        for day in days:
            day_num = day.get('day_number', 0)
            location = day.get('location', '')
            estimated_cost = day.get('estimated_cost', 0)
            
            st.markdown(f"""
            <div class="itinerary-day">
            <h4>Day {day_num}: {location}</h4>
            <p><strong>Estimated daily cost:</strong> ${estimated_cost:.0f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Weather
            weather = day.get('weather_forecast', {})
            if weather:
                st.write(f"🌤️ **Weather**: {weather.get('description', 'Clear')} - High: {weather.get('temperature_high', 75)}°F, Low: {weather.get('temperature_low', 65)}°F")
            
            # Activities
            activities = day.get('activities', [])
            if activities:
                st.write("**Activities:**")
                for activity in activities:
                    time = activity.get('time', 'All day')
                    name = activity.get('name', 'Activity')
                    cost = activity.get('cost', 0)
                    description = activity.get('description', '')
                    
                    if cost > 0:
                        st.write(f"• **{time}**: {name} (${cost:.0f}) - {description}")
                    else:
                        st.write(f"• **{time}**: {name} - {description}")
            
            # Meals
            meals = day.get('meals', [])
            if meals:
                st.write("**Meals:**")
                for meal in meals:
                    meal_type = meal.get('type', 'Meal')
                    name = meal.get('name', 'Restaurant')
                    cost = meal.get('cost', 0)
                    st.write(f"• **{meal_type}**: {name} (${cost:.0f})")
            
            # Transportation
            transportation = day.get('transportation', [])
            if transportation:
                st.write("**Transportation:**")
                for transport in transportation:
                    mode = transport.get('mode', 'Transport')
                    cost = transport.get('cost', 0)
                    description = transport.get('description', '')
                    st.write(f"• {mode}: ${cost:.0f} - {description}")
            
            # Notes
            notes = day.get('notes', [])
            if notes:
                st.write("**Tips:**")
                for note in notes:
                    st.write(f"💡 {note}")
            
            st.write("")  # Add spacing
    
    # Budget breakdown
    budget_breakdown = itinerary.get('budget_breakdown', {})
    if budget_breakdown:
        st.subheader("💸 Budget Breakdown")
        
        # Create a simple breakdown display
        for category, amount in budget_breakdown.items():
            percentage = (amount / itinerary.get('total_cost', 1)) * 100
            st.write(f"• **{category.replace('_', ' ').title()}**: ${amount:.0f} ({percentage:.1f}%)")
    
    # Highlights
    highlights = itinerary.get('highlights', [])
    if highlights:
        st.subheader("✨ Trip Highlights")
        for highlight in highlights:
            st.write(f"🌟 {highlight}")
    
    # Download button
    st.download_button(
        label="📄 Download Itinerary (JSON)",
        data=json.dumps(itinerary, indent=2, default=str),
        file_name=f"itinerary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
    
    # New trip button
    if st.button("🔄 Plan Another Trip", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.current_result = None
        st.rerun()

# Backend Configuration
st.sidebar.markdown("### ⚙️ Configuration")
use_cloud = st.sidebar.toggle(
    "Use Cloud API", 
    value=True,
    help="Toggle between local backend and deployed AWS API"
)

# Update API client if backend selection changed
if st.session_state.api_client.use_cloud != use_cloud:
    st.session_state.api_client = APIClient(use_cloud=use_cloud)

if use_cloud:
    st.sidebar.success("🌐 Using AWS Cloud API")
    st.sidebar.markdown("**Endpoint:** AWS Lambda + Bedrock")
else:
    st.sidebar.info("💻 Using Local Backend")

# Header
st.markdown("""
<div class="main-header">
    <h1>✈️ Smart Travel Planner AI</h1>
    <p>Create personalized travel itineraries with AI-powered insights</p>
</div>
""", unsafe_allow_html=True)

# Sample queries from the blueprint
sample_queries = [
    "I want a quick weekend trip from New York in July. Prefer a beach or nature spot, under $400 all-in.",
    "I want a peaceful solo escape from San Francisco in August. Driving is okay. I prefer lakes or forests, want to stay under $300.",
    "Looking for a fun city to visit from Chicago for 2 nights with my best friend. Budget is $500 for both of us.",
    "I'm based in Denver and want a solo 2-day hiking trip in October. Must include stargazing and minimal cost.",
    "I'm looking for a 7-day international trip in November. Budget under $1500, somewhere warm with great food and culture. I'm open to solo travel.",
    "We're a couple looking for a 6-day European trip in early October. Somewhere romantic, with history and charm. Budget is $1800 for both of us.",
    "I want a 5–6 day adventure in a scenic international destination with hiking and volcanoes. Traveling solo from California, under $1800."
]

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗣️ Tell us about your dream trip")
    
    # User query input
    user_query = st.text_area(
        "Describe your travel preferences:",
        value=st.session_state.get('auto_fill', ''),
        height=150,
        placeholder="Example: I want a weekend getaway from Seattle in August. Looking for outdoor activities and good food, budget around $600.",
        key="user_query_input"
    )
    
    # Generate button
    if st.button("🚀 Plan My Trip", type="primary", use_container_width=True):
        if user_query.strip():
            with st.spinner("🤖 AI agents are crafting your perfect itinerary..."):
                try:
                    # Create the itinerary using process_travel_request
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        st.session_state.api_client.process_travel_request(user_query)
                    )
                    loop.close()
                    
                    if result:
                        st.session_state.current_result = result
                        if result.get('session_id'):
                            st.session_state.current_session_id = result['session_id']
                        st.success("✅ Your itinerary is ready!")
                        st.rerun()
                    else:
                        st.error("Failed to create itinerary. Please try again.")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter your travel preferences first.")

with col2:
    st.subheader("💡 Sample Queries")
    st.write("Click any example to try it:")
    
    for i, query in enumerate(sample_queries):
        if st.button(
            f"📝 Example {i+1}",
            key=f"sample_{i}",
            help=query,
            use_container_width=True
        ):
            st.session_state.sample_query = query
            st.rerun()
    
    # Auto-fill sample query if selected
    if 'sample_query' in st.session_state:
        st.text_area(
            "Selected example:",
            value=st.session_state.sample_query,
            height=100,
            disabled=True
        )
        if st.button("🔄 Use This Example", use_container_width=True):
            st.session_state.auto_fill = st.session_state.sample_query
            del st.session_state.sample_query
            st.rerun()

# Clear auto-fill after it's been used
if 'auto_fill' in st.session_state and st.session_state.get('user_query_input'):
    if st.session_state.user_query_input == st.session_state.auto_fill:
        del st.session_state.auto_fill

# Display itinerary if available
if st.session_state.current_result:
    result = st.session_state.current_result
    
    if result.get('success'):
        # Successful result with itinerary
        itinerary = result.get('itinerary', {})
        if itinerary:
            st.markdown("---")
            display_itinerary(itinerary)
    
    elif result.get('clarification_needed'):
        # Need clarification
        st.warning("🤔 The AI needs more information from you:")
        st.write(result.get('message', 'Please provide more details.'))
        
        missing_info = result.get('missing_info', [])
        if missing_info:
            st.write("**Missing information:**")
            for info in missing_info:
                st.write(f"• {info}")
        
        # Allow user to provide clarification
        clarification = st.text_area("Please provide additional details:")
        if st.button("Submit Clarification"):
            if clarification.strip() and st.session_state.current_session_id:
                with st.spinner("Processing your clarification..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(
                            st.session_state.api_client.process_travel_request(
                                clarification, str(st.session_state.current_session_id)
                            )
                        )
                        loop.close()
                        st.session_state.current_result = result
                        st.success("Clarification processed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing clarification: {str(e)}")
    
    else:
        # Failed result
        st.error("❌ Failed to create itinerary")
        if result.get('message'):
            st.write(result['message'])
        
        if st.button("🔄 Try Again"):
            st.session_state.current_result = None
            st.session_state.current_session_id = None
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Powered by LangGraph • AWS • Bedrock • Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
