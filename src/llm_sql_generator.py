from openai import OpenAI
import os
import json
import pathlib
from dotenv import load_dotenv
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


load_dotenv()

# Lazy initialization - OpenAI client created on first use
_client = None

def get_openai_client():
    """Get or create OpenAI client - Railway compatible"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _client = OpenAI(api_key=api_key)
    return _client


_rossman_schema = None
_system_prompt = None
_user_prompt = None
_confidence_prompt = None
_validation_feedback_prompt = None


def load_prompt(prompt_name: str) -> str:
    """Load prompt template from the prompts folder"""
    script_dir = pathlib.Path(__file__).parent.parent
    prompt_path = script_dir / "prompts" / f"{prompt_name}.txt"
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_sql_prompts():
    """Loads all SQL prompts, cached after first call"""
    global _system_prompt, _user_prompt, _confidence_prompt, _validation_feedback_prompt
    
    if _system_prompt is None:
        _system_prompt = load_prompt("sql_generator_system")
        
    if _user_prompt is None:
        _user_prompt = load_prompt("sql_generator_user") 
        
    if _confidence_prompt is None:
        _confidence_prompt = load_prompt("sql_confidence_assessment") 
        
    if _validation_feedback_prompt is None:
        _validation_feedback_prompt = load_prompt("sql_validation_feedback")
        
    return _system_prompt, _user_prompt, _confidence_prompt, _validation_feedback_prompt




def load_rossmann_schema(path: str = None) -> Dict:
    """Load schema for Rossmann dataset, use default path if none is given"""
    global _rossman_schema   

    if _rossman_schema is not None:
        return _rossman_schema  

    if not path:
        script_dir = pathlib.Path(__file__).parent
        path = script_dir / "config" / "rossman_schema.json"
    
    with open(path, "r", encoding="utf-8") as f:
        _rossman_schema = json.loads(f.read())
        return _rossman_schema


def extract_validator_rules(validator) -> Dict[str, str]:
    """Gets the validation rules to use in prompt"""
    
    forbidden_commands = ", ".join(validator.forbidden_commands)
    allowed_functions = ", ".join(validator.allowed_functions)
    
    # Extract dangerous patterns (user-friendly descriptions)
    dangerous_patterns = []
    for pattern, description in validator.pattern_labels.items():
        # Simplify technical regex descriptions for LLM
        if "Comment" in description:
            dangerous_patterns.append("Comments (-- or /* */)")
        elif "injection" in description.lower():
            dangerous_patterns.append(description.replace("(possible injection)", "").replace("(dangerous", "(").strip())
        elif "Command chaining" in description:
            dangerous_patterns.append("Multiple commands in one query")
        else:
            dangerous_patterns.append(description)
    
    dangerous_patterns_text = "; ".join(set(dangerous_patterns))  # Remove duplicates
    
    return {
        "forbidden_commands": forbidden_commands,
        "allowed_functions": allowed_functions, 
        "dangerous_patterns": dangerous_patterns_text
    }
        

def generate_sql_query(user_question: str, rossmann_schema: dict = None, validator=None) -> str:
    """Generates SQL query from user question in natural language"""

    if rossmann_schema is None:
        rossmann_schema = load_rossmann_schema()
    
    system_template, user_template, _, _ = load_sql_prompts()  
    
    column_descriptions = "\n".join([f"- {col}: {desc}" for col, desc in rossmann_schema['columns'].items()])
    schema_notes = "\n".join([f"- {note}" for note in rossmann_schema['notes']])
    
    validator_rules = {}
    if validator:
        validator_rules = extract_validator_rules(validator)
    else:
        # Default  rules
        validator_rules = {
            "forbidden_commands": "INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, MERGE, REPLACE, EXEC, CALL, GRANT, REVOKE",
            "allowed_functions": "SUM, AVG, COUNT, MIN, MAX, DATE, DATE_TRUNC, COALESCE, YEAR, MONTH",
            "dangerous_patterns": "Comments, SQL injection patterns, Command chaining, UNION operations"
        }
    
    system_prompt = system_template.format(
        table_name=rossmann_schema['table'],
        column_descriptions=column_descriptions,
        schema_notes=schema_notes,
        **validator_rules 
    )
    
    user_prompt = user_template.format(user_question=user_question)
    
    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,  
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        

        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        if sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
            
        return sql_query
        
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        raise


def assess_sql_confidence(user_question: str, generated_sql: str) -> float:
    """Checks confidence score for generated SQL, returns value between 0 and 1"""
    try:

        _, _, confidence_template, _ = load_sql_prompts()
        
        confidence_prompt = confidence_template.format(
            user_question=user_question,
            generated_sql=generated_sql
        )
        
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": confidence_prompt}
            ],
            temperature=0,  # Deterministic assessment
            max_tokens=50
        )

        confidence_text = response.choices[0].message.content.strip()
        
        confidence_score = float(confidence_text)
        confidence_score = max(0.0, min(1.0, confidence_score))
        return confidence_score
            
    except:
        return 0.5


def provide_validation_feedback(user_question: str, failed_sql: str, validation_errors: str, rossmann_schema: dict = None) -> str:
    """Try to fix the SQL when validation fails"""
    try:

        if rossmann_schema is None:
            rossmann_schema = load_rossmann_schema()
            
        _, _, _, feedback_template = load_sql_prompts()
        
        # build validation dict to use it in prompt
        validator_rules = {
            "forbidden_commands": "INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, MERGE, REPLACE, EXEC, CALL, GRANT, REVOKE",
            "allowed_functions": "SUM, AVG, COUNT, MIN, MAX, DATE, DATE_TRUNC, COALESCE, YEAR, MONTH, ROUND, UPPER, LOWER, SUBSTR, LENGTH, TRIM, DAY",
            "dangerous_patterns": "Comments (-- or /* */), SQL injection patterns, Command chaining with semicolons, UNION operations"
        }
        
        feedback_prompt = feedback_template.format(
            original_question=user_question,
            failed_sql=failed_sql,
            validation_errors=validation_errors,
            table_name=rossmann_schema['table'],
            **validator_rules  
        )
        
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": feedback_prompt}
            ],
            temperature=0.1,  
            max_tokens=500
        )
        
        improved_sql = response.choices[0].message.content.strip()
        
        # Check if the improved SQL is identical to the failed one
        if improved_sql.strip() == failed_sql.strip():
            logger.warning("LLM returned identical SQL, adding retry context")
            # Add this info to the prompt and tr again with more temerature felxiblity
            retry_prompt = feedback_prompt + f"\n\nIMPORTANT: You returned the exact same SQL again: {failed_sql}\nPlease provide a DIFFERENT approach or query structure."
            
            retry_response = get_openai_client().chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "user", "content": retry_prompt}
                ],
                temperature=0.3,  
                max_tokens=500
            )
            improved_sql = retry_response.choices[0].message.content.strip()
        
        if improved_sql.startswith("```sql"):
            improved_sql = improved_sql.replace("```sql", "").replace("```", "").strip()
        if improved_sql.startswith("```"):
            improved_sql = improved_sql.replace("```", "").strip()
            
        return improved_sql
        
    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        return failed_sql


def generate_sql_with_validation(user_question: str, validator, rossmann_schema: dict = None, max_retries: int = 3, confidence_threshold: float = 0.7) -> Tuple[str, float, bool]:
    """Generate SQL with validation, retry when it fails or confidence too low"""
    
    for attempt in range(max_retries + 1):  
        if attempt == 0:
            sql_query = generate_sql_query(user_question, rossmann_schema, validator)
        else:
            # Generate  SQL based on previous  errors
            sql_query = provide_validation_feedback(user_question, previous_sql, validation_errors, rossmann_schema)
        
        #Validate the SQL result
        validation_result = validator.validate(sql_query)
        validation_passed = validation_result.get("ok", False)
        
        if not validation_passed:
            error_message = validation_result.get("error_message", "Unknown validation error")
            logger.warning(f"Validation failed: {error_message}")
            if attempt < max_retries:
                previous_sql = sql_query
                validation_errors = error_message
                continue
            else:
                logger.error("Maximum retries reached, returning last SQL with validation failure")
                return sql_query, 0.0, False
        
        # Assess confidence
        confidence_score = assess_sql_confidence(user_question, sql_query)
        
        # Check if confidence < threshold
        if confidence_score >= confidence_threshold:
            return sql_query, confidence_score, True
        else:
            if attempt < max_retries:
                # validation error -> confidence
                previous_sql = sql_query
                validation_errors = f"Low confidence score: {confidence_score:.2f}. Please improve the SQL query to better match the user's question."
                continue
            else:
                return sql_query, confidence_score, True  # Validation passed but low confidence
    
    return sql_query, confidence_score, validation_passed
