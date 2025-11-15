from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sys
import os
import time
import logging
from typing import Optional

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from llm_sql_generator import generate_sql_with_validation, load_rossmann_schema
from sql_validator import SQLValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="Talk2Data Agent API",
    description="Convert natural language questions to SQL queries",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    max_retries: int = Field(3, description="Maximum retry attempts")
    confidence_threshold: float = Field(0.7, description="Minimum confidence score")

class QueryResponse(BaseModel):
    sql_query: str
    confidence: float
    validation_passed: bool
    processing_time: float
    message: str

# Global variables for caching
_schema = None
_validator = None

def get_schema_and_validator():
    """Cache schema and validator to avoid repeated loading"""
    global _schema, _validator
    if _schema is None or _validator is None:
        _schema = load_rossmann_schema()
        _validator = SQLValidator(_schema)
    return _schema, _validator

@app.get("/")
async def root():
    return {
        "service": "Talk2Data Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/generate-sql", "/health", "/docs"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test schema loading
        schema, validator = get_schema_and_validator()
        return {
            "status": "healthy",
            "service": "talk2data-agent",
            "timestamp": time.time(),
            "schema_loaded": bool(schema),
            "validator_ready": bool(validator)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/generate-sql", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    """Generate SQL query from natural language question"""
    start_time = time.time()
    
    try:
        # Validate input
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if len(request.question) > 500:
            raise HTTPException(status_code=400, detail="Question too long (max 500 characters)")
        
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Get schema and validator
        schema, validator = get_schema_and_validator()
        
        # Generate SQL
        sql_query, confidence, validation_passed = generate_sql_with_validation(
            user_question=request.question.strip(),
            validator=validator,
            rossmann_schema=schema,
            max_retries=request.max_retries,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = time.time() - start_time
        
        # Determine message based on results
        if validation_passed and confidence >= request.confidence_threshold:
            message = "SQL generated successfully"
        elif validation_passed:
            message = f"SQL generated but low confidence ({confidence:.2f})"
        else:
            message = "SQL generated but failed validation"
        
        logger.info(f"SQL generated in {processing_time:.2f}s, confidence: {confidence:.2f}")
        
        return QueryResponse(
            sql_query=sql_query,
            confidence=confidence,
            validation_passed=validation_passed,
            processing_time=processing_time,
            message=message
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/info")
async def service_info():
    """Get service information and configuration"""
    try:
        schema, validator = get_schema_and_validator()
        return {
            "service": "Talk2Data Agent",
            "table_name": schema.get('table', 'unknown'),
            "columns": list(schema.get('columns', {}).keys()),
            "allowed_functions": validator.allowed_functions if validator else [],
            "forbidden_commands": validator.forbidden_commands if validator else []
        }
    except Exception as e:
        logger.error(f"Error getting service info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )