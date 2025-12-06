from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import sys
import os
import time
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path


current_dir = Path(__file__).parent
src_path = current_dir / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from s3_service import list_user_schema, get_user_schema, upload_user_schema, delete_user_schema, get_current_user
from llm_sql_generator import generate_multi_table_sql
from sql_validator import SQLValidator
from constants import DEFAULT_SCHEMA_NAME, MAX_QUESTION_LENGTH


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Talk2Data Agent API",
    description="Convert natural language questions to SQL queries",
    version="1.0.0"
)

class UpdateSchemaRequest(BaseModel):
    schema_data: Dict[str, Any]
    
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    max_retries: int = Field(3, description="Maximum retry attempts")
    confidence_threshold: float = Field(0.7, description="Minimum confidence score")
    schema_name: Optional[str] = Field(None, description="Name of the schema to use")
    schema_data: Optional[Dict[str, Any]] = Field(None, description="Schema data directly provided")
    username: Optional[str] = Field(None, description="Username for schema lookup")

class QueryResponse(BaseModel):
    sql_query: str
    confidence: float
    validation_passed: bool
    processing_time: float
    message: str
    
class UpdateSchemaResponse(BaseModel):
    username: str
    schema_name: str
    message: str
    success: bool


class SchemaListResponse(BaseModel):
    username: str
    schemas: List[str]
    count: int
    success: bool
    
class GetSchemaResponse(BaseModel):
    username: str
    schema_name: str
    schema: Dict[str, Any]
    success: bool
    
class DeleteSchemaResponse(BaseModel):
    username: str
    schema_name: str
    message: str
    success: bool




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
    try:
        
        from schema_parser import get_schema_parser
        parser = get_schema_parser("retial_star_schema")
        return {
            "status": "healthy",
            "service": "talk2data-agent",
            "timestamp": time.time(),
            "schema_loaded": bool(parser.tables),
            "tables_count": len(parser.tables),
            "available_tables": list(parser.tables.keys())
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
    


@app.post("/generate-sql", response_model=QueryResponse)
async def generate_sql(request: QueryRequest,  current_user: str = Depends(get_current_user)):
    """Generate SQL query from natural language question"""
    start_time = time.time()
    
    try:
        # Validate input
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if len(request.question) > MAX_QUESTION_LENGTH:
            raise HTTPException(status_code=400, detail=f"Question too long (max {MAX_QUESTION_LENGTH} characters)")
        
        # Determine schema name to use
        schema_name = request.schema_name if request.schema_name else DEFAULT_SCHEMA_NAME
        
        # Use username from request if provided, otherwise use authenticated user
        username = request.username if request.username else current_user
        
        # Load schema from S3 for user
        logger.info(f"Loading schema '{schema_name}' for user '{username}' from S3")
        success, schema_data = get_user_schema(username, schema_name)
        
        if not success or not schema_data:
            # Fallback to local schema for testing
            logger.warning(f"Schema '{schema_name}' not found in S3 for user '{username}', using local fallback")
            sql_query = generate_multi_table_sql(
                user_question=request.question.strip(),
                schema_name=schema_name  # Local fallback
            )
        else:
            # Use S3 schema
            logger.info(f"Using S3 schema '{schema_name}' for user '{username}'")
            sql_query = generate_multi_table_sql(
                user_question=request.question.strip(),
                schema_data=schema_data
            )
        
        # Validate SQL for security threats
        validator = SQLValidator()
        validation_result = validator.validate(sql_query)
        validation_passed = validation_result["ok"]
        
        if not validation_passed:
            raise HTTPException(
                status_code=400, 
                detail=f"SQL validation failed: {validation_result['error_message']}"
            )
    
        processing_time = time.time() - start_time
        confidence = 0.95
        message = "SQL generated and validated successfully"
        
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
    
@app.get("/schemas/{username}")
async def listschemas(username: str, current_user: str = Depends(get_current_user)) -> SchemaListResponse:
    """List all schemas for a user"""
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    try:
        success, schemas = list_user_schema(username=username)
        if not success:
            return SchemaListResponse(username=username, schemas=[], count=0,success=success)
        return SchemaListResponse(username=username, schemas=schemas, count=len(schemas), success=success)
    except Exception as e:
        logger.error(f"Error listing schemas for user {username}: {e}")
        return SchemaListResponse(username=username, schemas=[], count=0, success=False)
    
@app.get("/schemas/{username}/{schema_name}")
async def get_schema(username: str, schema_name: str, current_user: str = Depends(get_current_user)) -> GetSchemaResponse:
    """Get a specific schema for a user"""
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not schema_name.strip():
        raise HTTPException(status_code=400, detail="Schema name cannot be empty")
    
    try:
        success, schema = get_user_schema(username, schema_name)
        if not success:
            return GetSchemaResponse(username=username, schema_name=schema_name, schema={}, success=False)
        return GetSchemaResponse(username=username, schema_name=schema_name, schema=schema, success=True)
    except Exception as e:
        logger.error(f"Error getting schema {schema_name} for user {username}: {e}")
        return GetSchemaResponse(username=username, schema_name=schema_name, schema={}, success=False)
    
    
@app.delete("/schemas/{username}/{schema_name}")
async def delete_schema(username: str, schema_name: str, current_user: str = Depends(get_current_user)) -> DeleteSchemaResponse:
    """Delete a specific schema for a user"""
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not schema_name.strip():
        raise HTTPException(status_code=400, detail="Schema name cannot be empty")
    
    try:
        success, message = delete_user_schema(username, schema_name)
        return DeleteSchemaResponse(username=username, schema_name=schema_name, message=message, success=success)
    except Exception as e:
        logger.error(f"Error deleting schema {schema_name} for user {username}: {e}")
        message = f"Delete failed: {str(e)}"
        return DeleteSchemaResponse(username=username, schema_name=schema_name, message=message, success=False)
    
@app.put("/schemas/{username}/{schema_name}")
async def update_schema(username: str, schema_name: str, request: UpdateSchemaRequest, current_user: str = Depends(get_current_user)) -> UpdateSchemaResponse:
    """ Update the given Schema"""
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not schema_name.strip():
        raise HTTPException(status_code=400, detail="Schema name cannot be empty")
    if not request.schema_data:
        raise HTTPException(status_code=400, detail="Schema data cannot be empty")
    try:
        success, message = upload_user_schema(username, schema_name,request.schema_data)
        return UpdateSchemaResponse(username = username, schema_name= schema_name, message= message, success= success)
    except Exception as e:
        logger.error(f"Error updating schema {schema_name} for user {username}: {e}")
        return UpdateSchemaResponse(username=username, schema_name=schema_name, message=f"Update failed: {str(e)}", success=False)


@app.post("/schemas/{username}/{schema_name}")
async def create_schema(username: str, schema_name: str, request: UpdateSchemaRequest, current_user: str = Depends(get_current_user)) -> UpdateSchemaResponse:
    """ Create the given Schema"""
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not schema_name.strip():
        raise HTTPException(status_code=400, detail="Schema name cannot be empty")
    if not request.schema_data:
        raise HTTPException(status_code=400, detail="Schema data cannot be empty")
    try:
        success, message = upload_user_schema(username, schema_name,request.schema_data)
        return UpdateSchemaResponse(username = username, schema_name= schema_name, message= message, success= success)
    except Exception as e:
        logger.error(f"Error creating schema {schema_name} for user {username}: {e}")
        return UpdateSchemaResponse(username=username, schema_name=schema_name, message=f"Create failed: {str(e)}", success=False)
   
    
    

@app.get("/info")
async def service_info():
    """Get service information and configuration"""
    try:
        from schema_parser import get_schema_parser
        parser = get_schema_parser("retial_star_schema")
        
        # Get schema summary
        schema_summary = parser.get_schema_summary()
        
        return {
            "service": "Talk2Data Agent",
            "version": "2.0.0",
            "features": [
                "Automatic table selection (LLM)",
                "Algorithmic JOIN generation",
                "Multi-table SQL queries",
                "Star schema optimized"
            ],
            "schema_name": parser.schema_name,
            "tables": list(parser.tables.keys()),
            "tables_count": len(parser.tables),
            "relationships_count": len(parser.relationships),
            "schema_summary": schema_summary[:500] + "..." if len(schema_summary) > 500 else schema_summary
        }
    except Exception as e:
        logger.error(f"Error getting service info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Railway sets PORT environment variable
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "api_service:app", 
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )