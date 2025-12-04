"""
Centralized OpenAI client management.
Use this module to get the OpenAI client instance across all modules.
"""
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

_client = None


def get_openai_client() -> OpenAI:
    """
    Get or create OpenAI client singleton.
    Thread-safe for most use cases.
    
    Returns:
        OpenAI: Configured OpenAI client instance
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    global _client
    
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _client = OpenAI(api_key=api_key)
        logger.debug("OpenAI client initialized")
    
    return _client
