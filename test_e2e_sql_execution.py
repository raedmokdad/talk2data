"""
End-to-End Test: SQL Generation + Execution with Table Name Translation
Tests the complete flow: API generates SQL -> Translate table names -> Execute in DuckDB
"""
import sys
from pathlib import Path
import requests
import json

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.factory import create_connector
from src.models import DBType, DBSelection, FileItem
import re

def replace_table_names_in_sql(sql: str, schema_data: dict, connector) -> str:
    """
    Replace schema table names in SQL with actual DuckDB table names.
    (Copy of function from streamlit_schema_builder.py)
    """
    # Get schema table names
    schema_tables = []
    if schema_data and "schema" in schema_data:
        tables = schema_data["schema"].get("tables", [])
        schema_tables = [t.get("name", "") for t in tables if t.get("name")]
    
    # Get actual DB table names
    db_tables = []
    try:
        db_tables = connector.list_tables()
    except Exception as e:
        return sql
    
    # For single-table schemas (flat tables), create mapping
    if len(schema_tables) == 1 and len(db_tables) > 0:
        schema_table = schema_tables[0]
        db_table = db_tables[0]
        
        # Replace all occurrences of schema table name with DB table name
        pattern = r'\b' + re.escape(schema_table) + r'\b'
        modified_sql = re.sub(pattern, db_table, sql, flags=re.IGNORECASE)
        
        return modified_sql
    
    return sql

def test_end_to_end(csv_file: str, schema_name: str, question: str, expected_pattern: str = None):
    """
    Test complete flow: SQL generation + translation + execution
    
    Args:
        csv_file: Path to CSV file (relative to data/)
        schema_name: Name of schema on S3
        question: Natural language question
        expected_pattern: Optional regex pattern to validate SQL result
    """
    print(f"\n{'='*60}")
    print(f"Testing: {csv_file} with {schema_name}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")
    
    # Step 1: Setup connector
    test_file = project_root / "data" / csv_file
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    file_item = FileItem(
        name=test_file.name,
        path=str(test_file),
        type="csv"
    )
    
    db_selection = DBSelection(
        db_type=DBType.FILES,
        files=[file_item]
    )
    
    connector = create_connector(db_selection)
    print(f"✅ Step 1: Connector created")
    
    db_tables = connector.list_tables()
    print(f"   DB Tables: {db_tables}")
    
    # Step 2: Load schema
    schema_file = project_root / "src" / "config" / f"{schema_name}.json"
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    with open(schema_file) as f:
        schema_data = json.load(f)
    
    schema_tables = [t["name"] for t in schema_data["schema"]["tables"]]
    print(f"✅ Step 2: Schema loaded")
    print(f"   Schema Tables: {schema_tables}")
    
    # Step 3: Call API to generate SQL
    api_url = "https://talk2data-production.up.railway.app"
    payload = {
        "question": question,
        "schema_name": schema_name,
        "username": "raedmokdad"
    }
    
    try:
        response = requests.post(f"{api_url}/generate-sql", json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Step 3: API Error {response.status_code}: {response.text}")
            return False
        
        result = response.json()
        generated_sql = result.get('sql_query', '')
        confidence = result.get('confidence', 0)
        
        print(f"✅ Step 3: SQL generated (confidence: {confidence:.0%})")
        print(f"   Generated SQL: {generated_sql}")
        
    except Exception as e:
        print(f"❌ Step 3: API call failed: {e}")
        return False
    
    # Step 4: Translate table names
    executable_sql = replace_table_names_in_sql(generated_sql, schema_data, connector)
    
    if executable_sql != generated_sql:
        print(f"✅ Step 4: Table names translated")
        print(f"   Executable SQL: {executable_sql}")
    else:
        print(f"✅ Step 4: No translation needed (names match)")
    
    # Step 5: Execute SQL
    try:
        rows = connector.run_query(executable_sql)
        print(f"✅ Step 5: SQL executed successfully")
        print(f"   Result: {rows}")
        
        # Validate result if pattern provided
        if expected_pattern and rows:
            result_str = str(rows)
            if re.search(expected_pattern, result_str, re.IGNORECASE):
                print(f"✅ Result validation: Matches expected pattern")
                return True
            else:
                print(f"⚠️ Result validation: Does not match expected pattern")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Step 5: SQL execution failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("End-to-End SQL Execution Tests")
    print("="*60)
    
    # Test 1: test_orders
    test1 = test_end_to_end(
        csv_file="test_orders.csv",
        schema_name="test_orders_schema",
        question="How many orders are there?",
        expected_pattern=r"\d+"  # Should contain a number
    )
    
    # Test 2: employees
    test2 = test_end_to_end(
        csv_file="employees.csv",
        schema_name="employee_schema",
        question="How many employees are there?",
        expected_pattern=r"27"  # Should be 27 employees
    )
    
    # Test 3: test_orders - more complex query
    test3 = test_end_to_end(
        csv_file="test_orders.csv",
        schema_name="test_orders_schema",
        question="What is the average order amount?",
        expected_pattern=r"\d+\.?\d*"  # Should contain a decimal number
    )
    
    print("\n" + "="*60)
    print("Test Summary:")
    print(f"Test 1 (test_orders count):   {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (employees count):      {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (test_orders average):  {'✅ PASSED' if test3 else '❌ FAILED'}")
    print("="*60)
    
    if test1 and test2 and test3:
        print("\n🎉 All end-to-end tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
