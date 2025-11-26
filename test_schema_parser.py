"""Test SchemaParser methods"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from schema_parser import SchemaParser, TableRelationship

def test_find_fact_table():
    """Test _find_fact_table method"""
    print("=" * 60)
    print("TEST 1: _find_fact_table()")
    print("=" * 60)
    
    parser = SchemaParser("retial")
    parser.load_star_schema()
    
    # Test 1: Mit fact_sales
    tables1 = ["fact_sales", "dim_store", "dim_product"]
    result1 = parser._find_fact_table(tables1)
    print(f"\nTest 1a - Input: {tables1}")
    print(f"Expected: 'fact_sales'")
    print(f"Got:      '{result1}'")
    print(f"✓ PASS" if result1 == "fact_sales" else "✗ FAIL")
    
    # Test 2: Nur Dimensions
    tables2 = ["dim_store", "dim_product"]
    result2 = parser._find_fact_table(tables2)
    print(f"\nTest 1b - Input: {tables2}")
    print(f"Expected: None")
    print(f"Got:      {result2}")
    print(f"✓ PASS" if result2 is None else "✗ FAIL")


def test_find_relationship():
    """Test _find_relationship method"""
    print("\n" + "=" * 60)
    print("TEST 2: _find_relationship()")
    print("=" * 60)
    
    parser = SchemaParser("retial")
    parser.load_star_schema()
    
    # Test 1: Forward relationship (fact_sales -> dim_store)
    connected = {"fact_sales"}
    target = "dim_store"
    result1 = parser._find_relationship(connected, target)
    print(f"\nTest 2a - Connected: {connected}, Target: '{target}'")
    if result1:
        print(f"✓ Found: {result1.from_table}.{result1.from_column} -> {result1.to_table}.{result1.to_column}")
    else:
        print("✗ FAIL: No relationship found")
    
    # Test 2: Reverse relationship (dim_store -> fact_sales)
    connected2 = {"dim_store"}
    target2 = "fact_sales"
    result2 = parser._find_relationship(connected2, target2)
    print(f"\nTest 2b - Connected: {connected2}, Target: '{target2}'")
    if result2:
        print(f"✓ Found: {result2.from_table}.{result2.from_column} -> {result2.to_table}.{result2.to_column}")
    else:
        print("✗ FAIL: No relationship found")
    
    # Test 3: Multiple connected tables
    connected3 = {"fact_sales", "dim_store"}
    target3 = "dim_product"
    result3 = parser._find_relationship(connected3, target3)
    print(f"\nTest 2c - Connected: {connected3}, Target: '{target3}'")
    if result3:
        print(f"✓ Found: {result3.from_table}.{result3.from_column} -> {result3.to_table}.{result3.to_column}")
    else:
        print("✗ FAIL: No relationship found")
    
    # Test 4: No connection possible
    connected4 = {"dim_store"}
    target4 = "dim_product"
    result4 = parser._find_relationship(connected4, target4)
    print(f"\nTest 2d - Connected: {connected4}, Target: '{target4}'")
    if result4 is None:
        print("✓ PASS: Correctly returns None (no direct connection)")
    else:
        print(f"✗ FAIL: Should return None but got {result4}")


def test_relationships_loaded():
    """Test if relationships are loaded correctly"""
    print("\n" + "=" * 60)
    print("TEST 3: Relationships loaded from JSON")
    print("=" * 60)
    
    parser = SchemaParser("retial")
    parser.load_star_schema()
    
    print(f"\nTotal relationships loaded: {len(parser.relationships)}")
    for i, rel in enumerate(parser.relationships, 1):
        print(f"{i}. {rel.from_table}.{rel.from_column} -> {rel.to_table}.{rel.to_column} ({rel.join_type})")


def test_find_join_path():
    """Test find_join_path method"""
    print("\n" + "=" * 60)
    print("TEST 4: find_join_path() - Multiple JOINs")
    print("=" * 60)
    
    parser = SchemaParser("retial")
    parser.load_star_schema()
    
    # Test 1: 3 Tabellen (2 JOINs)
    tables1 = ["fact_sales", "dim_store", "dim_date"]
    result1 = parser.find_join_path(tables1)
    print(f"\nTest 4a - Input: {tables1}")
    print(f"Expected: 2 JOINs (3 tables - 1)")
    if result1:
        print(f"✓ Got {len(result1.relationships)} JOINs:")
        print(result1.to_sql())
    else:
        print("✗ FAIL: No join path found")
    
    # Test 2: Alle 4 Tabellen (3 JOINs)
    tables2 = ["fact_sales", "dim_store", "dim_product", "dim_date"]
    result2 = parser.find_join_path(tables2)
    print(f"\nTest 4b - Input: {tables2}")
    print(f"Expected: 3 JOINs (4 tables - 1)")
    if result2:
        print(f"✓ Got {len(result2.relationships)} JOINs:")
        print(result2.to_sql())
    else:
        print("✗ FAIL: No join path found")
    
    # Test 3: Nur Fact-Tabelle (0 JOINs)
    tables3 = ["fact_sales"]
    result3 = parser.find_join_path(tables3)
    print(f"\nTest 4c - Input: {tables3}")
    print(f"Expected: 0 JOINs (nur fact table)")
    if result3:
        print(f"✓ Got {len(result3.relationships)} JOINs (correct!)")
    else:
        print("✗ FAIL: Should return JoinPath with 0 relationships")


if __name__ == "__main__":
    try:
        test_relationships_loaded()
        test_find_fact_table()
        test_find_relationship()
        test_find_join_path()
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
