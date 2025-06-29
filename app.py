"""
Enhanced Streamlit Frontend for Smart Travel Planner AI

A clean, focused interface that works with both local backend and deployed AWS API.
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
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .agent-trace {
        border-radius: 5px;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.9em;
    }
    
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class APIClient:
    """Client for communicating with both local and cloud backends"""
    
    def __init__(self, use_cloud: bool = False):
        self.use_cloud = use_cloud
        self.cloud_endpoint = "https://oydiuxox5d.execute-api.us-east-1.amazonaws.com/dev/plan"
        self.local_app = None
        
        if not use_cloud:
            try:
                from src.core.application import TravelPlannerApp
                self.local_app = TravelPlannerApp()
                st.success("✅ Local backend initialized successfully!")
            except ImportError as e:
                st.error(f"Failed to import local backend: {e}")
                st.info("Switching to cloud backend...")
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
                self.cloud_endpoint,
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

def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'api_client' not in st.session_state:
        st.session_state.api_client = None

def display_itinerary(result: Dict[str, Any]):
    """Display the generated itinerary in a beautiful format"""
    if not result or not result.get('success'):
        st.error("No valid itinerary data to display")
        return
    
    itinerary = result.get('itinerary', {})
    
    # Header with destination and duration
    st.markdown(f"""
    <div class="main-header">
        <h1>🗺️ {itinerary.get('destination', 'Your Destination')}</h1>
        <p>{itinerary.get('duration', 'Multi-day')} Trip • {itinerary.get('budget_estimate', 'Budget varies')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Highlights section
    highlights = itinerary.get('highlights', [])
    if highlights:
        st.markdown("### ✨ Trip Highlights")
        cols = st.columns(min(len(highlights), 3))
        for i, highlight in enumerate(highlights):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="highlight-box">
                    <strong>{highlight}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    # Daily schedule
    daily_schedule = itinerary.get('daily_schedule', {})
    if daily_schedule:
        st.markdown("### 📅 Daily Itinerary")
        
        for day, activities in daily_schedule.items():
            if isinstance(activities, list):
                st.markdown(f"""
                <div class="itinerary-day">
                    <h4>🗓️ {day.replace('_', ' ').title()}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for i, activity in enumerate(activities, 1):
                    st.markdown(f"**{i}.** {activity}")
                st.markdown("---")
    
    # Recommendations
    recommendations = itinerary.get('recommendations', {})
    if recommendations:
        st.markdown("### 💡 Recommendations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'accommodation' in recommendations:
                st.markdown("**🏨 Accommodation**")
                st.write(recommendations['accommodation'])
            
            if 'transportation' in recommendations:
                st.markdown("**🚗 Transportation**")
                st.write(recommendations['transportation'])
        
        with col2:
            if 'dining' in recommendations:
                st.markdown("**🍽️ Dining**")
                dining = recommendations['dining']
                if isinstance(dining, list):
                    for restaurant in dining:
                        st.write(f"• {restaurant}")
                else:
                    st.write(dining)
    
    # Execution trace (if available)
    execution_trace = result.get('execution_trace', [])
    if execution_trace:
        with st.expander("🔍 AI Execution Trace"):
            for step in execution_trace:
                st.markdown(f'<div class="agent-trace">✓ {step}</div>', unsafe_allow_html=True)
    
    # Session info
    if result.get('session_id'):
        st.markdown(f"**Session ID:** `{result['session_id']}`")
    if result.get('timestamp'):
        st.markdown(f"**Generated:** {result['timestamp']}")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>✈️ Smart Travel Planner AI</h1>
        <p>Create personalized travel itineraries with AI-powered recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Backend selection
    st.sidebar.markdown("### ⚙️ Configuration")
    use_cloud = st.sidebar.toggle(
        "Use Cloud API", 
        value=True,
        help="Toggle between local backend and deployed AWS API"
    )
    
    if use_cloud:
        st.sidebar.success("🌐 Using AWS Cloud API")
        st.sidebar.markdown("**Endpoint:** `https://oydiuxox5d.execute-api.us-east-1.amazonaws.com/dev/plan`")
    else:
        st.sidebar.info("💻 Using Local Backend")
    
    # Initialize API client
    if st.session_state.api_client is None or st.session_state.api_client.use_cloud != use_cloud:
        st.session_state.api_client = APIClient(use_cloud=use_cloud)
    
    # Main interface
    st.markdown("### 🎯 Plan Your Trip")
    
    # Input form
    with st.form("travel_form"):
        user_query = st.text_area(
            "Describe your ideal trip:",
            placeholder="e.g., Plan a 5-day romantic trip to Italy with interests in art, food, and wine. Budget is around $3000.",
            height=100
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("🚀 Generate Itinerary", use_container_width=True)
        with col2:
            clear_btn = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    # Handle clear button
    if clear_btn:
        st.session_state.current_result = None
        st.session_state.current_session_id = None
        st.rerun()
    
    # Handle form submission
    if submitted and user_query.strip():
        with st.spinner("🤖 AI is crafting your perfect itinerary..."):
            try:
                # Process the travel request
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    st.session_state.api_client.process_travel_request(
                        user_query, 
                        st.session_state.current_session_id
                    )
                )
                loop.close()
                
                if result and result.get('success'):
                    st.session_state.current_result = result
                    if result.get('session_id'):
                        st.session_state.current_session_id = result['session_id']
                    
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Your itinerary is ready!</strong> The AI has crafted a personalized travel plan just for you.
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.error("Failed to create itinerary. Please try again with a different query.")
                    
            except Exception as e:
                st.error(f"Error generating itinerary: {str(e)}")
                if "timeout" in str(e).lower():
                    st.info("The request is taking longer than expected. The AI might still be working on your itinerary.")
    
    # Display current result
    if st.session_state.current_result:
        st.markdown("---")
        display_itinerary(st.session_state.current_result)
    
    # Sidebar with examples
    st.sidebar.markdown("### 💡 Example Queries")
    st.sidebar.markdown("""
    **Quick Examples:**
    - "3-day cultural trip to Paris, $1500 budget"
    - "Week-long adventure in Costa Rica for nature lovers"
    - "Romantic weekend in Santorini with luxury accommodations"
    - "Family trip to Tokyo with kids, focus on technology and anime"
    - "Solo backpacking through Southeast Asia, budget-friendly"
    """)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Smart Travel Planner AI** • Powered by Amazon Bedrock & AWS")

if __name__ == "__main__":
    main()
