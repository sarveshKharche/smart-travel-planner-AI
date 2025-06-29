"""
Smart Travel Planner AI - Streamlit Community Cloud Version

Public-facing interface that connects to the deployed AWS API.
Optimized for Streamlit Community Cloud hosting.
"""

import streamlit as st
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import time

# Configuration
AWS_API_URL = "https://oydiuxox5d.execute-api.us-east-1.amazonaws.com/dev/plan"

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

def call_travel_api(query: str) -> Dict[str, Any]:
    """Call the AWS API Gateway endpoint for travel planning"""
    try:
        response = requests.post(
            AWS_API_URL,
            json={"query": query},
            timeout=45,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"🚨 API Error: {response.status_code}")
            return {"success": False, "error": f"API returned status {response.status_code}"}
            
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. The AI is working hard on your itinerary! Please try again.")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 Connection error: {str(e)}")
        return {"success": False, "error": str(e)}

def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

def display_itinerary(result: Dict[str, Any]):
    """Display the generated itinerary in a beautiful format"""
    if not result or not result.get('success'):
        st.error("No valid itinerary data to display")
        return
    
    itinerary = result.get('itinerary', {})
    
    # Extract destination and basic info
    destination = itinerary.get('destination', 'Your Destination')
    duration = itinerary.get('duration', 'Multi-day')
    budget_estimate = itinerary.get('budget_estimate', 'Budget varies')
    highlights = itinerary.get('highlights', [])
    
    # Header with destination and duration
    st.markdown(f"""
    <div class="main-header">
        <h1>🗺️ {destination}</h1>
        <p>{duration} • {budget_estimate}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Trip highlights section
    if highlights:
        st.markdown("### ✨ Trip Highlights")
        cols = st.columns(min(len(highlights), 3))
        for i, highlight in enumerate(highlights):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="highlight-box">
                    <h4>🎯 Highlight {i+1}</h4>
                    <p style="color: white; margin: 0;">{highlight}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Daily itinerary section
    st.markdown("### 📅 Your Complete Itinerary")
    
    # Check for daily_schedule format first
    daily_schedule = itinerary.get('daily_schedule', {})
    if daily_schedule:
        # Sort the days properly (day_1, day_2, etc.)
        day_keys = sorted([k for k in daily_schedule.keys() if k.startswith('day_')])
        
        for day_key in day_keys:
            activities = daily_schedule[day_key]
            day_num = day_key.split('_')[1]
            
            # Day container
            st.markdown(f"""
            <div class="itinerary-day">
                <h4>🗓️ Day {day_num}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Activities list
            if isinstance(activities, list) and activities:
                for i, activity in enumerate(activities, 1):
                    st.markdown(f"**{i}.** {activity}")
            else:
                st.markdown("*No specific activities planned for this day*")
            
            st.markdown("---")
    
    # Fallback: Check for direct day_X keys in itinerary
    else:
        day_keys = sorted([k for k in itinerary.keys() if k.startswith('day_')])
        
        if day_keys:
            for day_key in day_keys:
                day_data = itinerary[day_key]
                day_num = day_key.split('_')[1]
                
                # Day container
                st.markdown(f"""
                <div class="itinerary-day">
                    <h4>🗓️ Day {day_num}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Handle different formats
                if isinstance(day_data, list):
                    # Activities are directly in a list
                    for i, activity in enumerate(day_data, 1):
                        st.markdown(f"**{i}.** {activity}")
                elif isinstance(day_data, dict):
                    # Activities might be in a sub-field
                    activities = day_data.get('activities', [])
                    date = day_data.get('date', '')
                    cost = day_data.get('estimated_cost', 0)
                    
                    if date:
                        st.markdown(f"**Date:** {date}")
                    if cost:
                        st.markdown(f"**Budget:** ${cost}")
                    
                    for i, activity in enumerate(activities, 1):
                        st.markdown(f"**{i}.** {activity}")
                
                st.markdown("---")
        else:
            st.warning("⚠️ No daily itinerary found in the API response.")
    
    # Additional recommendations
    recommendations = itinerary.get('recommendations', {})
    if recommendations:
        st.markdown("### 💡 Additional Recommendations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'accommodation' in recommendations:
                st.markdown("**🏨 Accommodation**")
                st.info(recommendations['accommodation'])
            
            if 'transportation' in recommendations:
                st.markdown("**🚗 Transportation**")
                st.info(recommendations['transportation'])
        
        with col2:
            if 'dining' in recommendations:
                st.markdown("**🍽️ Dining**")
                dining = recommendations['dining']
                if isinstance(dining, list):
                    for restaurant in dining:
                        st.write(f"• {restaurant}")
                else:
                    st.info(dining)
    
    # Export functionality
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📄 Download Itinerary (JSON)",
            data=json.dumps(itinerary, indent=2),
            file_name=f"travel_itinerary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Session info
    if result.get('session_id'):
        st.markdown(f"**Session ID:** `{result['session_id']}`")
    if result.get('timestamp'):
        st.markdown(f"**Generated:** {result['timestamp']}")
    
    # # Additional recommendations if available
    # recommendations = itinerary.get('recommendations', {})
    # if recommendations:
    #     st.markdown("### 💡 Additional Recommendations")
        
    #     col1, col2 = st.columns(2)
        
    #     with col1:
    #         if 'accommodation' in recommendations:
    #             st.markdown("**🏨 Accommodation**")
    #             st.info(recommendations['accommodation'])
            
    #         if 'transportation' in recommendations:
    #             st.markdown("**🚗 Transportation**")
    #             st.info(recommendations['transportation'])
        
    #     with col2:
    #         if 'dining' in recommendations:
    #             st.markdown("**🍽️ Dining**")
    #             dining = recommendations['dining']
    #             if isinstance(dining, list):
    #                 for restaurant in dining:
    #                     st.write(f"• {restaurant}")
    #             else:
    #                 st.info(dining)
    
    # # Export functionality
    # st.markdown("---")
    # col1, col2, col3 = st.columns([1, 2, 1])
    # with col2:
    #     st.download_button(
    #         label="� Download Itinerary (JSON)",
    #         data=json.dumps(itinerary, indent=2),
    #         file_name=f"travel_itinerary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    #         mime="application/json",
    #         use_container_width=True
    #     )
    
    # # Session info
    # if result.get('session_id'):
    #     st.markdown(f"**Session ID:** `{result['session_id']}`")
    # if result.get('timestamp'):
    #     st.markdown(f"**Generated:** {result['timestamp']}")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>✈️ Smart Travel Planner AI</h1>
        <p>Create personalized travel itineraries with AI-powered recommendations</p>
        <p><em>Powered by Amazon Bedrock AI & Multi-Agent Architecture</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar info
    st.sidebar.markdown("### 🌟 Features")
    st.sidebar.markdown("""
    - 🤖 **AI-Powered Planning** - Advanced multi-agent system
    - 🌍 **Global Destinations** - Plan trips anywhere in the world  
    - 💰 **Budget-Aware** - Get recommendations that fit your budget
    - ⚡ **Real-time Generation** - Instant itinerary creation
    - 📱 **Mobile Friendly** - Works perfectly on all devices
    """)
    
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown("""
    This app uses advanced AI to create personalized travel itineraries.
    
    **Powered by:**
    - Amazon Bedrock AI
    - Multi-Agent Architecture  
    - AWS Cloud Infrastructure
    """)
    
    # Main interface
    st.markdown("### 🎯 Plan Your Trip")
    
    # Input form
    with st.form("travel_form"):
        user_query = st.text_area(
            "Describe your ideal trip:",
            placeholder="e.g., Plan a 5-day romantic trip to Italy with interests in art, food, and wine. Budget is around $3000.",
            height=120,
            help="💡 Be specific about destination, duration, number of travelers, budget, and preferences for best results!"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("🚀 Generate Itinerary", use_container_width=True)
    
    # Handle form submission
    if submitted and user_query.strip():
        st.markdown("---")
        
        # Progress indicators
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Animated progress steps
            steps = [
                ("🔍 Understanding your travel preferences...", 20),
                ("� AI agents collaborating on your itinerary...", 40), 
                ("✈️ Gathering destination insights and recommendations...", 60),
                ("🎨 Crafting your personalized travel plan...", 80),
                ("✅ Finalizing your perfect itinerary...", 95)
            ]
            
            for step_text, progress_val in steps:
                status_text.markdown(f"**{step_text}**")
                progress_bar.progress(progress_val)
                time.sleep(0.8)
            
            # Make the API call
            result = call_travel_api(user_query)
            
            progress_bar.progress(100)
            status_text.markdown("**🎉 Your personalized itinerary is ready!**")
            time.sleep(1)
            
            # Clear progress indicators
            progress_container.empty()
        
        if result and result.get('success'):
            st.session_state.current_result = result
            if result.get('session_id'):
                st.session_state.current_session_id = result['session_id']
            
            st.markdown("""
            <div class="success-message">
                <strong>✅ Your itinerary is ready!</strong> The AI has crafted a personalized travel plan just for you.
            </div>
            """, unsafe_allow_html=True)
            
        elif result and result.get('clarification_needed'):
            st.warning("🤔 I need more information to create your perfect itinerary. Please provide more details about your preferences, budget, or travel dates.")
        
        else:
            st.error("😅 Oops! There was an issue generating your itinerary. Please try again or rephrase your request.")
            if result.get('error'):
                st.info(f"Error details: {result['error']}")
    
    # Display current result
    if st.session_state.current_result:
        st.markdown("---")
        display_itinerary(st.session_state.current_result)
    
    # Sidebar with examples
    st.sidebar.markdown("### 💡 Example Queries")
    st.sidebar.markdown("""
    **Quick Examples:**
    - "5-day romantic trip to Paris for 2 people, budget $2500"
    - "Week-long adventure in Iceland with hiking and northern lights"
    - "3-day business trip to Tokyo with efficient scheduling"  
    - "Family vacation to Orlando for 4 days with kids aged 8 and 12"
    - "Budget backpacking through Southeast Asia for 10 days, $800"
    - "Luxury wellness retreat in Bali for 6 days, focus on relaxation"
    """)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Smart Travel Planner AI** • Powered by Amazon Bedrock & AWS")
    
    # Main footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <h4 style="color: #667eea;">🚀 Built with Advanced AI Technology</h4>
        <p><strong>Multi-Agent Architecture:</strong> Supervisor • Query Parser • Itinerary Generator • Quality Evaluator</p>
        <p><strong>Powered by:</strong> Amazon Bedrock AI • AWS Lambda • DynamoDB • Terraform Infrastructure</p>
        <p><strong>Open Source:</strong> 
           <a href="https://github.com/sarveshKharche/smart-travel-planner-AI" target="_blank" style="color: #667eea;">
               View on GitHub 🔗
           </a>
        </p>
        <br>
        <p><em>Made with ❤️ for travelers worldwide</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
