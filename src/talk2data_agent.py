from dotenv import load_dotenv, dotenv_values
import os
import logging
import pathlib

from llm_sql_generator import generate_sql_with_validation, load_rossmann_schema
from sql_validator import SQLValidator

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# setup
load_dotenv()

# Force load values from .env file to override system environment
env_values = dotenv_values(".env")
for key, value in env_values.items():
    if value:
        os.environ[key] = value


def main():
    """
    Simple Talk2Data - converts question to SQL
    """
    try:
        # Get user question
        user_text = input("Your Question: ").strip()
        if not user_text:
            print("No question provided")
            return 1
        
        print(f"\nProcessing: {user_text}")
        
        # Direct SQL Generation 
        schema = load_rossmann_schema()
        validator = SQLValidator(schema)
        
        sql_query, confidence, validation_passed = generate_sql_with_validation(
            user_question=user_text,
            validator=validator,
            max_retries=3,
            confidence_threshold=0.7
        )
        
        # Show Results
        print("\n" + "="*60)
        print("GENERATED SQL QUERY:")
        print("="*60)
        print(f"```sql\n{sql_query}\n```")
        print(f"\nConfidence: {confidence:.2f}")
        print(f"Validation: {'PASSED' if validation_passed else 'FAILED'}")
        
        if confidence >= 0.8:
            print("Quality: Excellent - Ready for execution")
        elif confidence >= 0.6:
            print("Quality: Good - Review recommended")
        else:
            print("Quality: Low - Manual review required")
            
        return 0
        
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        return 130
        
    except Exception as e:
        print(f"\nERROR: Failed to generate SQL: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())