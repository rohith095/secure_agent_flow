"""
Configuration settings for the secure agent flow application.
"""

import os
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the secure agent flow crew."""

    # AWS Bedrock configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

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
        from langchain_aws import ChatBedrock

        return ChatBedrock(
            model_id=cls.BEDROCK_MODEL_ID,
            region_name=cls.AWS_REGION,
            model_kwargs={
                "max_tokens": 4096,
                "temperature": 0.1,
                "top_p": 0.9,
            }
        )
