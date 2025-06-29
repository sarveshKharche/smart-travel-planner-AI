#!/usr/bin/env python3
"""
Simple HTTP API server for Smart Travel Planner AI
Demonstrates final output accessible via curl commands
"""

import json
import os
import sys
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.application import TravelPlannerApplication

app = FastAPI(
    title="Smart Travel Planner AI API",
    description="AI-powered travel planning with multi-agent orchestration",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TravelPlanRequest(BaseModel):
    query: str

class TravelPlanResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    message: str = ""

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Smart Travel Planner AI API is running!",
        "version": "1.0.0",
        "endpoints": {
            "plan": "POST /plan - Generate travel itinerary",
            "health": "GET /health - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "smart-travel-planner-ai"}

@app.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(request: TravelPlanRequest):
    """
    Generate a travel itinerary using AI agents
    
    Example curl command:
    ```
    curl -X POST "http://localhost:8000/plan" \
         -H "Content-Type: application/json" \
         -d '{"query": "Plan a 3-day trip to Paris for 2 people with a budget of $2000"}'
    ```
    """
    try:
        # Initialize the travel planner application
        app_instance = TravelPlannerApplication()
        
        # Process the travel planning request
        result = await app_instance.process_request(request.query)
        
        if result.get('success', False):
            return TravelPlanResponse(
                status="success",
                data=result,
                message="Travel itinerary generated successfully!"
            )
        else:
            return TravelPlanResponse(
                status="error",
                data=result,
                message=result.get('error', 'Failed to generate travel itinerary')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Internal server error: {str(e)}",
                "data": {}
            }
        )

@app.get("/demo")
async def demo_endpoint():
    """
    Demo endpoint with a sample travel plan request
    
    Example curl command:
    ```
    curl "http://localhost:8000/demo"
    ```
    """
    sample_query = "Plan a 3-day romantic trip to Paris for 2 people with a budget of $2000, focusing on culture and fine dining"
    
    try:
        app_instance = TravelPlannerApplication()
        result = await app_instance.process_request(sample_query)
        
        return {
            "sample_query": sample_query,
            "result": result,
            "curl_example": {
                "command": 'curl -X POST "http://localhost:8000/plan" -H "Content-Type: application/json" -d \'{"query": "' + sample_query + '"}\'',
                "description": "Use this curl command to generate your own travel plans"
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "sample_query": sample_query,
            "curl_example": {
                "command": 'curl -X POST "http://localhost:8000/plan" -H "Content-Type: application/json" -d \'{"query": "Plan a trip to Tokyo"}\'',
                "description": "Use this curl command to generate travel plans"
            }
        }

if __name__ == "__main__":
    print("🚀 Starting Smart Travel Planner AI API Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📖 Interactive docs at: http://localhost:8000/docs")
    print("🔗 Health check at: http://localhost:8000/health")
    print("\n📋 Example curl commands:")
    print("  Health check:")
    print('    curl "http://localhost:8000/health"')
    print("\n  Demo endpoint:")
    print('    curl "http://localhost:8000/demo"')
    print("\n  Generate travel plan:")
    print('    curl -X POST "http://localhost:8000/plan" \\')
    print('         -H "Content-Type: application/json" \\')
    print('         -d \'{"query": "Plan a 3-day trip to Paris for 2 people with budget $2000"}\'')
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
