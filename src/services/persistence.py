"""
Persistence Service for Smart Travel Planner AI

Handles DynamoDB operations for storing and retrieving agent state
and execution traces.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from ..models.state import AgentState, AgentRole, ConfidenceLevel
from ..config import Config

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        return super(DecimalEncoder, self).default(o)


class PersistenceService:
    """
    Service for persisting agent state and execution traces to DynamoDB.
    
    Handles serialization/deserialization and provides error handling
    for database operations.
    """
    
    def __init__(self):
        """Initialize the persistence service with DynamoDB connection"""
        self.config = Config()
        
        # Initialize DynamoDB resource
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.config.DYNAMODB_REGION
        )
        
        # Get table reference
        self.table = self.dynamodb.Table(self.config.DYNAMODB_TABLE_NAME)
        
        logger.info(f"PersistenceService initialized for table: {self.config.DYNAMODB_TABLE_NAME}")
    
    async def save_state(self, state: AgentState) -> bool:
        """
        Save agent state to DynamoDB.
        
        Args:
            state: Agent state to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare item for DynamoDB
            item = self._serialize_state(state)
            
            # Add TTL (30 days from now)
            ttl = int((datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60))
            item['ttl'] = ttl
            
            # Put item in DynamoDB
            response = self.table.put_item(Item=item)
            
            logger.info(f"State saved successfully for session: {state.get('session_id')}")
            return True
            
        except ClientError as e:
            logger.error(f"DynamoDB error saving state: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving state: {str(e)}")
            return False
    
    async def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent state from DynamoDB.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Agent state if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={'session_id': session_id}
            )
            
            if 'Item' not in response:
                logger.warning(f"No state found for session: {session_id}")
                return None
            
            # Deserialize and return state
            state = self._deserialize_state(response['Item'])
            logger.info(f"State loaded successfully for session: {session_id}")
            return state
            
        except ClientError as e:
            logger.error(f"DynamoDB error loading state: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading state: {str(e)}")
            return None
    
    async def save_execution_trace(self, session_id: str, agent_name: str, action: str, details: Dict[str, Any]) -> bool:
        """
        Save an execution trace entry.
        
        Args:
            session_id: Session identifier
            agent_name: Name of the agent performing the action
            action: Action description
            details: Additional details about the action
            
        Returns:
            True if successful, False otherwise
        """
        try:
            trace_item = {
                'session_id': session_id,
                'sort_key': f"trace#{int(datetime.utcnow().timestamp() * 1000)}",
                'agent_name': agent_name,
                'action': action,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60))
            }
            
            # Serialize the details
            trace_item['details'] = json.dumps(details, cls=DecimalEncoder)
            
            # Put trace item
            self.table.put_item(Item=trace_item)
            
            logger.debug(f"Execution trace saved for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving execution trace: {str(e)}")
            return False
    
    def _serialize_state(self, state: AgentState) -> Dict[str, Any]:
        """
        Serialize agent state for DynamoDB storage.
        
        Args:
            state: Agent state to serialize
            
        Returns:
            Serialized state dictionary
        """
        # Convert state to dictionary
        serialized = dict(state)
        
        # Handle datetime objects, enums, and complex objects
        for key, value in serialized.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, Enum):
                serialized[key] = value.value
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Serialize complex list items
                serialized[key] = json.dumps(value, cls=DecimalEncoder)
            elif isinstance(value, dict):
                # Serialize complex dict items
                serialized[key] = json.dumps(value, cls=DecimalEncoder)
        
        return serialized
    
    def _deserialize_state(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize agent state from DynamoDB.
        
        Args:
            item: DynamoDB item
            
        Returns:
            Deserialized agent state
        """
        # Remove DynamoDB-specific fields
        if 'ttl' in item:
            del item['ttl']
        
        # Deserialize datetime strings
        for key, value in item.items():
            if key.endswith('_at') and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
            elif isinstance(value, str) and (key.endswith('_results') or key.endswith('_versions') or key.endswith('_metrics')):
                try:
                    item[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass
            # Handle AgentRole enum
            elif key == 'current_agent' and isinstance(value, str):
                try:
                    item[key] = AgentRole(value)
                except ValueError:
                    pass
            # Handle ConfidenceLevel enum  
            elif key == 'confidence_level' and isinstance(value, str):
                try:
                    item[key] = ConfidenceLevel(value)
                except ValueError:
                    pass
        
        return item  # Return dict instead of AgentState object
    
    def health_check(self) -> bool:
        """
        Perform a health check on the DynamoDB connection.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to describe the table
            self.table.load()
            return True
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {str(e)}")
            return False
