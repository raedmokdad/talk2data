"""Test get_schema_summary method"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from schema_parser import SchemaParser

def test_schema_summary():
    print("=" * 60)
    print("TEST: get_schema_summary()")
    print("=" * 60)
    
    parser = SchemaParser("retial")
    parser.load_star_schema()
    
    # Test 1: Check tables loaded
    print(f"\n✓ Tables loaded: {list(parser.tables.keys())}")
    
    # Test 2: Get schema summary
    summary = parser.get_schema_summary()
    
    print("\n" + "=" * 60)
    print("SCHEMA SUMMARY:")
    print("=" * 60)
    print(summary)
    print("=" * 60)
    
    # Test 3: Check if all tables are in summary
    for table_name in parser.tables.keys():
        if table_name in summary:
            print(f"✓ {table_name} in summary")
        else:
            print(f"✗ {table_name} MISSING in summary")

if __name__ == "__main__":
    try:
        test_schema_summary()
        print("\n✓ TEST COMPLETED")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
