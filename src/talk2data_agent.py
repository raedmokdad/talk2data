from dotenv import load_dotenv, dotenv_values
import os
import logging
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

try:
    from src.llm_sql_generator import generate_multi_table_sql
    from src.sql_validator import SQLValidator
except ModuleNotFoundError:
    
    from llm_sql_generator import generate_multi_table_sql
    from sql_validator import SQLValidator


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
logging.getLogger('httpx').setLevel(logging.ERROR)


load_dotenv()


env_values = dotenv_values(".env")
for key, value in env_values.items():
    if value:
        os.environ[key] = value


def main():
    try:
        
        user_text = input("Your Question: ").strip()
        if not user_text:
            print("No question provided")
            return 1
        
        print(f"\nProcessing: {user_text}")
        
        
        sql_query = generate_multi_table_sql(
            user_question=user_text,
            schema_name="retial_star_schema"
        )
        
        
        print("\n" + "="*60)
        print("GENERATED SQL QUERY:")
        print("="*60)
        print(f"```sql\n{sql_query}\n```")
        print("\n✓ Multi-table query with automatic JOINs generated successfully")
            
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