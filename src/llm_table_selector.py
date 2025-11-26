import json
import pathlib
import logging
from typing import List
from openai import OpenAI
import os
from dotenv import load_dotenv


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


def load_prompt(prompt_name: str) -> str:
    """Load prompt template from the prompts folder"""
    script_dir = pathlib.Path(__file__).parent.parent
    prompt_path = script_dir / "prompts" / f"{prompt_name}.txt"
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()



def select_tables(question: str, schema_summary: str) -> List[str]:
    """
    Uses LLM to identify which tables are needed to answer the question.
    """
    
    try:
        prompt_template = load_prompt("table_selector")
        
        prompt = prompt_template.format(question = question, schema_summary = schema_summary)
        
        client = get_openai_client()
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [{"role": "user", "content": prompt}],
            temperature = 0.0,
        )
        
        content = response.choices[0].message.content.strip()
        tables = json.loads(content)
        
        return tables
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response was: {content}")
        return []
    except Exception as e:
        logger.error(f"Error in table selection: {e}")
        return []