import json
import pathlib
import logging
from typing import List

from src.openai_client import get_openai_client
from src.constants import OPENAI_MODEL, OPENAI_TEMPERATURE

logger = logging.getLogger(__name__)


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
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=OPENAI_TEMPERATURE,
        )
        
        content = response.choices[0].message.content.strip()
        
     
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()
      
        tables = json.loads(content)
       
        
        return tables
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response was: {content}")
        return []
    except Exception as e:
        logger.error(f"Error in table selection: {e}")
        return []