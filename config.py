"""
Configuration settings for the secure agent flow application.
"""

import os
import boto3
from dotenv import load_dotenv
from crewai import Crew, LLM

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the secure agent flow crew."""

    # AWS Bedrock configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    # Crew configuration
    CREW_VERBOSE = True

    # Agent configuration
    AGENT_ALLOW_DELEGATION = False

    @classmethod
    def validate_config(cls):
        """Validate configuration and return status."""
        try:
            # Test AWS Bedrock access
            bedrock = boto3.client('bedrock-runtime', region_name=cls.AWS_REGION)
            return {
                "valid": True,
                "message": "AWS Bedrock configuration is valid."
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"AWS Bedrock configuration error: {str(e)}"
            }

    @classmethod
    def get_bedrock_llm(cls):
        """Get configured Bedrock LLM instance."""
        model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"

        llm = LLM(
            model=model_id
        )
        return llm
