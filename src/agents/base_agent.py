"""
Base Agent Class

Common functionality shared by all agents in the Smart Travel Planner AI system.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from ..models.state import AgentState, AgentRole
from ..config import config


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Provides common functionality like logging, AWS service access,
    and standardized state management.
    """
    
    def __init__(self, role: AgentRole):
        self.role = role
        self.logger = logging.getLogger(f"agent.{role.value}")
        
        # Initialize AWS clients
        self._init_aws_clients()
    
    def _init_aws_clients(self) -> None:
        """Initialize AWS service clients"""
        try:
            # Bedrock client for AI inference
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=config.AWS_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
            
            # DynamoDB client for state persistence
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=config.DYNAMODB_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
            
            # S3 client for data storage
            self.s3_client = boto3.client(
                's3',
                region_name=config.S3_REGION,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize AWS clients: {e}")
            # Set clients to None for local development
            self.bedrock_client = None
            self.dynamodb = None
            self.s3_client = None
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Process the current state and return updated state.
        
        Each agent must implement this method to define their core logic.
        """
        pass
    
    async def call_bedrock(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Make a call to Amazon Bedrock for AI inference.
        
        Args:
            prompt: The prompt to send to the AI model
            max_tokens: Maximum tokens in the response
            
        Returns:
            The AI model's response as a string
        """
        if not self.bedrock_client:
            self.logger.warning("Bedrock client not available, returning mock response")
            return self._get_mock_response(prompt)
        
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=config.BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except ClientError as e:
            self.logger.error(f"Bedrock API error: {e}")
            return self._get_mock_response(prompt)
        except Exception as e:
            self.logger.error(f"Unexpected error calling Bedrock: {e}")
            return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """Return a mock response when Bedrock is not available"""
        if "parse" in prompt.lower():
            return """{
                "origin": "New York",
                "destinations": ["Miami"],
                "dates": {
                    "start": "2024-07-19",
                    "end": "2024-07-21",
                    "duration": "3"
                },
                "budget": {
                    "amount": 400,
                    "currency": "USD",
                    "type": "total"
                },
                "travelers": {
                    "count": 1,
                    "type": "solo"
                },
                "preferences": {
                    "style": ["relaxation", "beach"],
                    "accommodation": ["hostel"],
                    "transportation": ["flight"],
                    "activities": ["beach", "sightseeing"]
                }
            }"""
        return "Mock response - Bedrock not available"
    
    def log_execution(self, state: AgentState, message: str) -> None:
        """
        Log an execution message and add it to the state trace.
        
        Args:
            state: Current agent state
            message: Log message
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {self.role.value}: {message}"
        
        # Add to execution trace
        if "execution_trace" not in state:
            state["execution_trace"] = []
        state["execution_trace"].append(log_entry)
        
        # Log to logger
        self.logger.info(message)
    
    def save_state(self, state: AgentState) -> bool:
        """
        Save the current state to DynamoDB.
        
        Args:
            state: State to save
            
        Returns:
            True if successful, False otherwise
        """
        if not self.dynamodb:
            self.logger.warning("DynamoDB not available, state not saved")
            return False
        
        try:
            table = self.dynamodb.Table(config.DYNAMODB_TABLE_NAME)
            
            # Convert datetime objects to ISO strings for DynamoDB
            state_copy = dict(state)
            for key, value in state_copy.items():
                if isinstance(value, datetime):
                    state_copy[key] = value.isoformat()
            
            table.put_item(Item=state_copy)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self, session_id: str) -> Optional[AgentState]:
        """
        Load state from DynamoDB by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Loaded state or None if not found
        """
        if not self.dynamodb:
            self.logger.warning("DynamoDB not available, cannot load state")
            return None
        
        try:
            table = self.dynamodb.Table(config.DYNAMODB_TABLE_NAME)
            response = table.get_item(Key={'session_id': session_id})
            
            if 'Item' in response:
                state = response['Item']
                
                # Convert ISO strings back to datetime objects
                for key, value in state.items():
                    if isinstance(value, str) and 'T' in value:
                        try:
                            state[key] = datetime.fromisoformat(value)
                        except ValueError:
                            pass  # Not a datetime string
                
                return state
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            return None
    
    def calculate_confidence(self, metrics: Dict[str, float]) -> float:
        """
        Calculate overall confidence score from individual metrics.
        
        Args:
            metrics: Dictionary of metric name -> score (0-1)
            
        Returns:
            Overall confidence score (0-1)
        """
        if not metrics:
            return 0.0
        
        # Weighted average of metrics
        weights = {
            'budget_score': 0.3,
            'feasibility_score': 0.3,
            'preference_match_score': 0.2,
            'completeness_score': 0.2
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, score in metrics.items():
            weight = weights.get(metric, 0.1)  # Default weight for unknown metrics
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def should_retry(self, state: AgentState) -> bool:
        """
        Determine if the agent should retry based on confidence and retry count.
        
        Args:
            state: Current state
            
        Returns:
            True if should retry, False otherwise
        """
        retry_count = state.get("retry_count", 0)
        confidence_metrics = state.get("confidence_metrics", {})
        
        if retry_count >= config.MAX_RETRIES:
            return False
        
        overall_confidence = self.calculate_confidence(confidence_metrics)
        
        # Retry if confidence is medium (between thresholds)
        return (config.CONFIDENCE_THRESHOLD_MEDIUM <= overall_confidence < config.CONFIDENCE_THRESHOLD_HIGH)
    
    def needs_clarification(self, state: AgentState) -> bool:
        """
        Determine if user clarification is needed.
        
        Args:
            state: Current state
            
        Returns:
            True if clarification needed, False otherwise
        """
        confidence_metrics = state.get("confidence_metrics", {})
        overall_confidence = self.calculate_confidence(confidence_metrics)
        
        return overall_confidence < config.CONFIDENCE_THRESHOLD_MEDIUM
