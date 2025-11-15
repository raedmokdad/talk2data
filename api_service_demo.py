"""
Talk2Data Agent - Demo API Service
Mock version for testing without OpenAI API key
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from datetime import datetime

app = FastAPI(
    title="Talk2Data Agent API (Demo Mode)",
    description="REST API for SQL generation from natural language queries - Demo Version",
    version="1.0.0-demo"
)

class QueryRequest(BaseModel):
    question: str
    include_explanation: bool = True
    confidence_threshold: float = 0.7

class QueryResponse(BaseModel):
    sql_query: str
    confidence_score: float
    explanation: str
    validation_result: dict
    timestamp: str

# Mock responses for demonstration
DEMO_RESPONSES = {
    "sales": {
        "sql_query": "SELECT Store, SUM(Sales) as Total_Sales FROM rossmann_data GROUP BY Store ORDER BY Total_Sales DESC LIMIT 5;",
        "confidence_score": 0.95,
        "explanation": "Diese Abfrage gruppiert die Daten nach Store und berechnet die Gesamtumsätze, sortiert absteigend."
    },
    "stores": {
        "sql_query": "SELECT DISTINCT Store, StoreType FROM rossmann_data ORDER BY Store;",
        "confidence_score": 0.88,
        "explanation": "Zeigt alle einzigartigen Stores mit ihrem Typ aus der Rossmann-Datenbank."
    },
    "top": {
        "sql_query": "SELECT Store, AVG(Sales) as Avg_Sales FROM rossmann_data GROUP BY Store ORDER BY Avg_Sales DESC LIMIT 10;",
        "confidence_score": 0.92,
        "explanation": "Berechnet den durchschnittlichen Umsatz pro Store und zeigt die Top 10."
    }
}

@app.get("/")
async def root():
    """Service information endpoint"""
    return {
        "service": "Talk2Data Agent API (Demo Mode)",
        "version": "1.0.0-demo",
        "status": "running",
        "mode": "demonstration",
        "endpoints": ["/generate-sql", "/health", "/docs"],
        "note": "Dies ist eine Demo-Version ohne OpenAI API Anforderung"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "talk2data-agent-demo",
        "timestamp": datetime.now().isoformat(),
        "mode": "demo",
        "schema_loaded": True
    }

@app.post("/generate-sql", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    """Generate SQL query from natural language - Demo Mode"""
    
    try:
        # Simple keyword matching for demo
        question_lower = request.question.lower()
        
        if any(word in question_lower for word in ["umsatz", "sales", "verkauf"]):
            demo_key = "sales"
        elif any(word in question_lower for word in ["store", "laden", "geschäft"]):
            demo_key = "stores" 
        elif any(word in question_lower for word in ["top", "beste", "höchste"]):
            demo_key = "top"
        else:
            demo_key = "sales"  # Default
            
        demo_response = DEMO_RESPONSES[demo_key]
        
        return QueryResponse(
            sql_query=demo_response["sql_query"],
            confidence_score=demo_response["confidence_score"],
            explanation=demo_response["explanation"],
            validation_result={
                "is_valid": True,
                "syntax_check": "passed",
                "security_check": "passed",
                "performance_warning": None,
                "demo_mode": True
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo error: {str(e)}")

@app.get("/demo-examples")
async def demo_examples():
    """Zeigt verfügbare Demo-Beispiele"""
    return {
        "examples": [
            {
                "question": "Zeige mir die Top 5 Stores nach Umsatz",
                "category": "sales"
            },
            {
                "question": "Welche Stores gibt es?", 
                "category": "stores"
            },
            {
                "question": "Top 10 beste Stores",
                "category": "top"
            }
        ],
        "note": "Diese Demo-API funktioniert ohne OpenAI API Key"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Talk2Data Demo API...")
    print("📍 Demo Mode: Funktioniert ohne OpenAI API Key")
    print("🌐 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)