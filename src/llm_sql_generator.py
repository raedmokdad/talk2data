from openai import OpenAI
import os
import json
import pathlib
from dotenv import load_dotenv
from typing import Dict, Tuple, Optional
import logging
from src.schema_parser import get_schema_parser, get_schema_parser_from_data
from src.date_converter import extract_and_convert_dates

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


load_dotenv()


_client = None

def get_openai_client():
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
    script_dir = pathlib.Path(__file__).parent.parent
    prompt_path = script_dir / "prompts" / f"{prompt_name}.txt"
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_sql_prompts():
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
    
    forbidden_commands = ", ".join(validator.forbidden_commands)
    allowed_functions = ", ".join(validator.allowed_functions)
    
    dangerous_patterns = []
    for pattern, description in validator.pattern_labels.items():
        if "Comment" in description:
            dangerous_patterns.append("Comments (-- or /* */)")
        elif "injection" in description.lower():
            dangerous_patterns.append(description.replace("(possible injection)", "").replace("(dangerous", "(").strip())
        elif "Command chaining" in description:
            dangerous_patterns.append("Multiple commands in one query")
        else:
            dangerous_patterns.append(description)
    
    dangerous_patterns_text = "; ".join(set(dangerous_patterns))  
    
    return {
        "forbidden_commands": forbidden_commands,
        "allowed_functions": allowed_functions, 
        "dangerous_patterns": dangerous_patterns_text
    }
        

def generate_sql_query(user_question: str, rossmann_schema: dict = None, validator=None) -> str:

    if rossmann_schema is None:
        rossmann_schema = load_rossmann_schema()
    
    system_template, user_template, _, _ = load_sql_prompts()  
    
    column_descriptions = "\n".join([f"- {col}: {desc}" for col, desc in rossmann_schema['columns'].items()])
    schema_notes = "\n".join([f"- {note}" for note in rossmann_schema['notes']])
    
    validator_rules = {}
    if validator:
        validator_rules = extract_validator_rules(validator)
    else:
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
        
        if "```" in sql_query:
            sql_query = sql_query.replace("```sql", "").replace("```json", "").replace("```", "").strip()
            
        return sql_query
        
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        raise


def assess_sql_confidence(user_question: str, generated_sql: str) -> float:
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
            temperature=0,  
            max_tokens=50
        )

        confidence_text = response.choices[0].message.content.strip()
        
        confidence_score = float(confidence_text)
        confidence_score = max(0.0, min(1.0, confidence_score))
        return confidence_score
            
    except:
        return 0.5


def provide_validation_feedback(user_question: str, failed_sql: str, validation_errors: str, rossmann_schema: dict = None) -> str:
    try:

        if rossmann_schema is None:
            rossmann_schema = load_rossmann_schema()
            
        _, _, _, feedback_template = load_sql_prompts()
        
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
        
        if improved_sql.strip() == failed_sql.strip():
            logger.warning("LLM returned identical SQL, adding retry context")
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
        
        if "```" in improved_sql:
            improved_sql = improved_sql.replace("```sql", "").replace("```json", "").replace("```", "").strip()
        
       
        return improved_sql
        
    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        return failed_sql


def generate_sql_with_validation(user_question: str, validator, rossmann_schema: dict = None, max_retries: int = 3, confidence_threshold: float = 0.7) -> Tuple[str, float, bool]:
    
    for attempt in range(max_retries + 1):  
        if attempt == 0:
            sql_query = generate_sql_query(user_question, rossmann_schema, validator)
        else:
            sql_query = provide_validation_feedback(user_question, previous_sql, validation_errors, rossmann_schema)
        
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
        
        confidence_score = assess_sql_confidence(user_question, sql_query)
        
        if confidence_score >= confidence_threshold:
            return sql_query, confidence_score, True
        else:
            if attempt < max_retries:
                previous_sql = sql_query
                validation_errors = f"Low confidence score: {confidence_score:.2f}. Please improve the SQL query to better match the user's question."
                continue
            else:
                return sql_query, confidence_score, True  
    
    return sql_query, confidence_score, validation_passed


def generate_multi_table_sql(user_question: str, schema_name: str = None , schema_data: Dict = None, validator=None ) -> str:
    try:
      
        processed_question = extract_and_convert_dates(user_question)
        if processed_question != user_question:
            logger.info(f"Date conversion applied:\nOriginal: {user_question}\nProcessed: {processed_question}")
        
     
        if schema_data:
            parser = get_schema_parser_from_data(schema_data)
        elif schema_name:
            parser = get_schema_parser(schema_name)
        else:
            raise ValueError("Both schema_data and schema_name are not available")
        
      
        relevant_tables = parser.get_relevant_tables(processed_question)
        logger.info(f"Selected tables: {relevant_tables}")
        
        if not relevant_tables:
            raise ValueError("No relevant tables identified for the question")
        
        # Validate that all selected tables actually exist in schema
        is_valid, error_msg = parser.validate_selected_tables(relevant_tables)
        if not is_valid:
            raise ValueError(error_msg)
       
        join_path = parser.find_join_path(relevant_tables)
        
        if join_path is None and len(relevant_tables) > 1:
            logger.error(f"Could not find JOIN path for tables: {relevant_tables}")
            raise ValueError("Unable to connect selected tables with JOINs")
        
        
        tables_info = []
        for table_name in relevant_tables:
            table_data = parser.tables.get(table_name, {})
            role = table_data.get("role", "")
            grain = table_data.get("grain", "")
            columns = table_data.get("columns", {})
            
            col_descriptions = "\n".join([f"  - {col}: {desc}" for col, desc in columns.items()])
            table_info = f"Table: {table_name} ({role})\n- Grain: {grain}\n- Columns:\n{col_descriptions}"
            tables_info.append(table_info)
        
        schema_info = "\n\n".join(tables_info)
        
       
        join_sql = ""
        if join_path and join_path.relationships:
            join_sql = join_path.to_sql()
            logger.info(f"Generated JOINs:\n{join_sql}")
        
       
        validator_rules = {}
        if validator:
            validator_rules = extract_validator_rules(validator)
        else:
            validator_rules = {
                "forbidden_commands": "INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, MERGE, REPLACE, EXEC, CALL, GRANT, REVOKE",
                "allowed_functions": "SUM, AVG, COUNT, MIN, MAX, DATE, DATE_TRUNC, COALESCE, YEAR, MONTH",
                "dangerous_patterns": "Comments, SQL injection patterns, Command chaining, UNION operations"
            }
        
        
        kpis_info = parser.get_kpis_summary()
        synonyms_info = parser.get_synonyms_summary()
        
        system_prompt = f"""You are an expert SQL query generator for a star schema database.

Available Tables and Schema:
{schema_info}

JOIN Structure:
The tables are connected with the following JOINs:
{join_sql if join_sql else "Single table query - no JOINs needed"}

{kpis_info}

{synonyms_info}

Security Rules:
- FORBIDDEN commands: {validator_rules['forbidden_commands']}
- ALLOWED functions: {validator_rules['allowed_functions']}
- AVOID: {validator_rules['dangerous_patterns']}


CRITICAL Instructions:
1. Use the provided JOIN structure in your FROM clause
2. Generate a complete, valid SQL query
3. Use ONLY the columns listed in the schema above - NO OTHER COLUMNS EXIST
4. For KPIs, use the formulas provided in the KPI section above.
5. Check the Term Glossary for synonym mappings to map user terms to schema columns.
6. If the question asks for DATA that is NOT in the available columns AND NOT calculable from KPIs, you MUST respond with exactly: "ERROR: Required data not available in schema"
7. Follow proper SQL syntax and best practices
8. For date filters, use the ISO format dates provided in the question
9. Return ONLY the SQL query (or the ERROR message), no explanations

IMPORTANT - What counts as "missing data":
- Asking for a METRIC or COLUMN that is not in the schema/KPIs → ERROR
- Asking for a concept that requires data not present in the tables → ERROR
- Do NOT invent formulas for metrics if they are not defined in the KPI section → ERROR
- CRITICAL: Asking for specific FILTER VALUES is ALWAYS VALID. If the user mentions a specific value (like "Berlin", "ABC123", "Finance", "2024-01-15"), this is a filter value for a WHERE clause, NOT a column name. As long as the corresponding column exists (e.g., city, sku, department_name, date), generate the query. Do NOT return ERROR just because you don't see "Berlin" or "ABC123" in the schema description.
"""
        
        user_prompt = f"Generate a SQL query to answer this question: {processed_question}"
        
        
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=800
        )
        
        sql_query = response.choices[0].message.content.strip()
        

        if "```" in sql_query:
                       sql_query = sql_query.replace("```sql", "").replace("```json", "").replace("```", "").strip()
       
        
        if sql_query.startswith("ERROR:"):
            error_message = sql_query.replace("ERROR:", "").strip()
            logger.warning(f"LLM detected missing data: {error_message}")
            raise ValueError(f"Cannot answer question: {error_message}")
        
        is_valid, error_msg = parser.validate_sql_columns(sql_query)
        if not is_valid:
            logger.warning(f"Column validation failed: {error_msg}")
            return None
        
        logger.info(f"Generated SQL:\n{sql_query}")
        return sql_query
        
    except Exception as e:
        logger.error(f"Multi-table SQL generation failed: {e}")
        raise
