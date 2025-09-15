"""
Configuration settings for the secure agent flow application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the secure agent flow crew."""

    # OpenAI API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # Crew configuration
    CREW_VERBOSE = True

    # Agent configuration
    AGENT_ALLOW_DELEGATION = False

    @classmethod
    def validate_config(cls):
        """Validate configuration and return status."""
        if not cls.OPENAI_API_KEY:
            return {
                "valid": False,
                "message": "OPENAI_API_KEY is required. Please set it in your .env file."
            }
        return {
            "valid": True,
            "message": "Configuration is valid."
        }
