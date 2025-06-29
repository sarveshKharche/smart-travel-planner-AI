"""
Configuration management for Smart Travel Planner AI

Handles environment variables, API keys, and application settings.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the application"""
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")  # Will use AWS CLI if None
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")  # Will use AWS CLI if None
    
    # Amazon Bedrock
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID", 
        "anthropic.claude-3-haiku-20240307-v1:0"
    )
    
    # External API Keys
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    FOURSQUARE_API_KEY: Optional[str] = os.getenv("FOURSQUARE_API_KEY")
    AMADEUS_CLIENT_ID: Optional[str] = os.getenv("AMADEUS_CLIENT_ID")
    AMADEUS_CLIENT_SECRET: Optional[str] = os.getenv("AMADEUS_CLIENT_SECRET")
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "travel-planner-state")
    DYNAMODB_REGION: str = os.getenv("DYNAMODB_REGION", "us-east-1")
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "travel-planner-data")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    
    # Application Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    CONFIDENCE_THRESHOLD_HIGH: float = float(os.getenv("CONFIDENCE_THRESHOLD_HIGH", "0.8"))
    CONFIDENCE_THRESHOLD_MEDIUM: float = float(os.getenv("CONFIDENCE_THRESHOLD_MEDIUM", "0.6"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Streamlit Configuration
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    SRC_ROOT: Path = PROJECT_ROOT / "src"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    TEMP_DIR: Path = PROJECT_ROOT / "temp"
    
    @classmethod
    def validate_required_keys(cls) -> bool:
        """Validate that all required API keys are present"""
        required_keys = [
            cls.OPENWEATHER_API_KEY,
            cls.FOURSQUARE_API_KEY,
            cls.AMADEUS_CLIENT_ID,
            cls.AMADEUS_CLIENT_SECRET,
        ]
        
        missing_keys = [key for key in required_keys if not key]
        
        if missing_keys:
            print(f"Warning: Missing API keys. Some features may not work.")
            return False
        
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.TEMP_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)


# Create an instance for easy importing
config = Config()

# Create directories on import
config.create_directories()

# Validate API keys on import
config.validate_required_keys()
