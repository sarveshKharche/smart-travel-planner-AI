"""
AWS Lambda function for Smart Travel Planner AI

This function handles HTTP requests and orchestrates the travel planning workflow
using the LangGraph supervisor-worker pattern.

Python Version: 3.11+
"""

from __future__ import annotations

import json
import logging
import asyncio
import sys
from src.core.application import TravelPlannerApp

# Check Python version compatibility
if sys.version_info < (3, 11):
    raise RuntimeError("This application requires Python 3.11 or higher")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the travel planner app
try:
    travel_app = TravelPlannerApp()
    logger.info("TravelPlannerApp initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TravelPlannerApp: {str(e)}")
    travel_app = None

def lambda_handler(event, context):
    """
    AWS Lambda handler for the Smart Travel Planner
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Check if app is initialized
    if travel_app is None:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Application not properly initialized'
            })
        }
    
    try:
        # Parse the request body
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        # Handle different endpoints
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/plan')
        
        if http_method == 'OPTIONS':
            # Handle CORS preflight
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
                },
                'body': ''
            }
        
        if path == '/health':
            # Health check endpoint
            health_status = travel_app.health_check()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(health_status)
            }
        
        elif path == '/plan':
            # Main travel planning endpoint
            user_query = body.get('query') or body.get('user_query')
            session_id = body.get('session_id')
            
            if not user_query:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Missing required parameter: query or user_query'
                    })
                }
            
            # Process the travel request asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    travel_app.process_travel_request(user_query, session_id)
                )
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(result)
                }
            finally:
                loop.close()
        
        elif path == '/continue':
            # Continue session with additional information
            session_id = body.get('session_id')
            additional_info = body.get('additional_info')
            
            if not session_id or not additional_info:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Missing required parameters: session_id and additional_info'
                    })
                }
            
            # Continue the session
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    travel_app.continue_session(session_id, additional_info)
                )
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(result)
                }
            finally:
                loop.close()
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Endpoint not found'
                })
            }
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }
