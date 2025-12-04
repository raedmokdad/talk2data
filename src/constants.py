"""
Application constants and configuration values.
Centralized location for magic strings and default values.
"""

# Default schema name (used when no schema is specified)
DEFAULT_SCHEMA_NAME = "retail_star_schema"

# Default user for local development (no authentication)
DEFAULT_LOCAL_USER = "raedmokdad"

# OpenAI model configuration
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS_SQL = 800
OPENAI_MAX_TOKENS_TABLE_SELECT = 200
OPENAI_TEMPERATURE = 0.0

# S3 paths
S3_SCHEMA_PREFIX = "schemas"

# API configuration
MAX_QUESTION_LENGTH = 500
DEFAULT_MAX_RETRIES = 3
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
