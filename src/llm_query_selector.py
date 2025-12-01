from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Optional
import logging
import re
from time import sleep
from mapping import MappingOutput
from pydantic import ValidationError



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


load_dotenv()


_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
client = OpenAI(api_key=_api_key)



def load_prompt(path: str) -> str:
    if not path:
        raise ValueError("Path cannot be empty")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"Prompt file is empty: {path}")
            return content
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load prompt from {path}: {e}")
        raise IOError(f"Failed to load prompt from {path}: {e}") from e


def build_prompt(
    prompt_template: str,
    user_text: str,
    top_matches: List[Tuple[str, float]], 
    queries_dict: Dict[str, Dict]
) -> str:
    
    if not prompt_template or not prompt_template.strip():
        raise ValueError("prompt_template cannot be empty")
    if not user_text or not user_text.strip():
        raise ValueError("user_text cannot be empty")
    if not top_matches:
        raise ValueError("top_matches cannot be empty")
    if not queries_dict:
        raise ValueError("queries_dict cannot be empty")
    
    desc = []
    
    for k, _ in top_matches:
        try:
            desc.append({
                "key": k,
                "description": queries_dict[k]["description"]
            })
        except KeyError:
            logger.warning(f"Query key '{k}' not found in queries_dict.")
            continue
    
    if not desc:
        raise ValueError("No valid query descriptions found for given top_matches.")

    try:
        prompt = prompt_template.format(
            user_text=user_text,
            desc=json.dumps(desc, indent=2)
        )
    except KeyError as e:
        raise ValueError(f"Missing placeholder in prompt_template: {e}") from e
    
    return prompt
    

def call_llm(prompt: str, model: Optional[str] = None, temperature: float = 0.0) -> str:
    
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    
    try:
        logger.debug(f"Calling LLM with model={model}, temperature={temperature}")
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        if not response.choices:
            raise RuntimeError("LLM returned no choices")
        
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("LLM returned empty response")
            
        return content.strip()
        
    except Exception as e:
        logger.exception(f"LLM call failed with model {model}")
        raise RuntimeError(f"LLM call failed: {e}") from e

def parse_response(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text cannot be empty")
    
    
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Direct JSON parse failed. Trying regex fallback.")
    
    
    
    match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', raw_text, re.DOTALL)
    if not match:
        logger.error(f"No JSON object found in LLM response. Response: {raw_text[:200]}")
        raise RuntimeError("No JSON object found in LLM response.")
    
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logger.error(f"Regex-extracted JSON is still invalid: {e}")
        raise RuntimeError(f"Failed to parse JSON: {e}") from e
        
        
def validate_llm_response(data: dict) -> dict:
    try:
        validated = MappingOutput(**data)
        return validated.model_dump()
    except ValidationError as e:
        error_messages = []
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            msg = err["msg"]
            error_messages.append(f"{loc}: {msg}")
        full_error = " | ".join(error_messages)
        raise ValueError(f"Invalid LLM response: {full_error}")


def validate_and_retry(
    prompt: str, 
    max_retries: int = 3, 
    retry_delay: float = 1.0
) -> dict:
    
    if not prompt or not prompt.strip():
        raise ValueError("prompt cannot be empty")
    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")
    
    original_prompt = prompt
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries}")
            raw = call_llm(prompt)
            parsed = parse_response(raw)
            validated = validate_llm_response(parsed)
            logger.info(f"Valid LLM response received on attempt {attempt}")
            return validated
            
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
            
            if attempt < max_retries:
            
                prompt = (
                    original_prompt +
                    f"\n\nYour previous response could not be validated.\n"
                    f"Reason: {e}\n"
                    f"Please respond with valid JSON in this format:\n"
                    f'{{"query_key": "...", "params": {{"..."}}}}'
                )
                logger.debug(f"Retrying after {retry_delay}s delay")
                sleep(retry_delay)
            else:
                logger.error(f"All {max_retries} attempts failed")
    
    raise RuntimeError(
        f"LLM failed after {max_retries} attempts.\n"
        f"Last error: {last_error}"
    ) from last_error
            