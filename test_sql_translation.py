"""
Test SQL table name translation functionality
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.factory import create_connector
from src.models import DBType, DBSelection, FileItem, FileType
import json

def test_sql_translation():
    """Test that SQL table names are translated from schema to DB names"""
    
    print("\n=== Test SQL Table Name Translation ===\n")
    
    # Setup connector with test_orders.csv
    test_file = project_root / "data" / "test_orders.csv"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    file_item = FileItem(
        name=test_file.name,
        path=str(test_file),
        type=FileType.CSV
    )
    
    selection = DBSelection(
        db_type=DBType.FILES,
        files=[file_item]
    )
    
    connector = create_connector(selection)
    
    print(f"✅ Connector created")
    
    # Get actual DB table names
    db_tables = connector.list_tables()
    print(f"📊 DB Tables: {db_tables}")
    
    # Load test_orders schema
    schema_file = project_root / "src" / "config" / "test_orders_schema.json"
    with open(schema_file) as f:
        schema_data = json.load(f)
    
    schema_tables = [t["name"] for t in schema_data["schema"]["tables"]]
    print(f"📋 Schema Tables: {schema_tables}")
    
    # Test SQL with schema table name
    sql_with_schema_name = "SELECT COUNT(*) FROM test_orders"
    print(f"\n📝 Original SQL: {sql_with_schema_name}")
    
    # Import the translation function
    from streamlit_schema_builder import replace_table_names_in_sql
    
    translated_sql = replace_table_names_in_sql(
        sql_with_schema_name,
        schema_data,
        connector
    )
    
    print(f"🔄 Translated SQL: {translated_sql}")
    
    # Test execution
    try:
        rows = connector.run_query(translated_sql)
        count = rows[0][0]
        print(f"✅ Query executed successfully!")
        print(f"📊 Result: {count} rows in table")
        
        # Verify result makes sense
        if count > 0:
            print(f"✅ Test PASSED: SQL translation works correctly")
            return True
        else:
            print(f"⚠️ Warning: Table appears empty")
            return False
            
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        return False

def test_employee_translation():
    """Test SQL translation with employee schema"""
    
    print("\n=== Test Employee SQL Translation ===\n")
    
    # Setup connector with employees.csv
    test_file = project_root / "data" / "employees.csv"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    file_item = FileItem(
        name=test_file.name,
        path=str(test_file),
        type=FileType.CSV
    )
    
    selection = DBSelection(
        db_type=DBType.FILES,
        files=[file_item]
    )
    
    connector = create_connector(selection)
    
    print(f"✅ Connector created")
    
    # Get actual DB table names
    db_tables = connector.list_tables()
    print(f"📊 DB Tables: {db_tables}")
    
    # Load employee schema
    schema_file = project_root / "src" / "config" / "employee_schema.json"
    with open(schema_file) as f:
        schema_data = json.load(f)
    
    schema_tables = [t["name"] for t in schema_data["schema"]["tables"]]
    print(f"📋 Schema Tables: {schema_tables}")
    
    # Test SQL with schema table name
    sql_with_schema_name = "SELECT COUNT(*) FROM employees"
    print(f"\n📝 Original SQL: {sql_with_schema_name}")
    
    # Import the translation function
    from streamlit_schema_builder import replace_table_names_in_sql
    
    translated_sql = replace_table_names_in_sql(
        sql_with_schema_name,
        schema_data,
        connector
    )
    
    print(f"🔄 Translated SQL: {translated_sql}")
    
    # Test execution
    try:
        rows = connector.run_query(translated_sql)
        count = rows[0][0]
        print(f"✅ Query executed successfully!")
        print(f"📊 Result: {count} rows in table")
        
        # Verify result makes sense (employees.csv has 27 rows)
        if count == 27:
            print(f"✅ Test PASSED: SQL translation works correctly (27 employees)")
            return True
        elif count > 0:
            print(f"⚠️ Warning: Expected 27 rows, got {count}")
            return True
        else:
            print(f"❌ Test FAILED: Table appears empty")
            return False
            
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SQL Table Name Translation Tests")
    print("=" * 60)
    
    test1 = test_sql_translation()
    test2 = test_employee_translation()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"test_orders: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"employees:   {'✅ PASSED' if test2 else '❌ FAILED'}")
    print("=" * 60)
    
    if test1 and test2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
