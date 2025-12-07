"""
Simple debug script to check table names
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.factory import create_connector
from src.models import DBSelection, DBType, FileItem, FileType

# Test with test_orders.csv
test_file = project_root / "data" / "test_orders.csv"
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

print("\n=== Table Names Debug ===")
print(f"DB Tables: {connector.list_tables()}")

# Test query with actual table name
db_table = connector.list_tables()[0]
sql = f"SELECT COUNT(*) FROM {db_table}"
print(f"\nQuery: {sql}")

try:
    result = connector.run_query(sql)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    if result:
        print(f"First row: {result[0]}")
        print(f"Count: {result[0][0]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
