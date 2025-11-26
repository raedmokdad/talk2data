"""Test tables.items()"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from schema_parser import SchemaParser

parser = SchemaParser("retial")
parser.load_star_schema()

print("=" * 60)
print("TESTING: self.tables.items()")
print("=" * 60)

# Test 1: Was ist self.tables?
print(f"\nType of self.tables: {type(parser.tables)}")
print(f"Keys: {list(parser.tables.keys())}")

# Test 2: Iteriere mit .items()
print("\n" + "=" * 60)
print("Iterating with .items():")
print("=" * 60)

for table_name, table_info in parser.tables.items():
    print(f"\n✓ table_name: {table_name}")
    print(f"✓ table_info type: {type(table_info)}")
    print(f"✓ table_info keys: {list(table_info.keys())}")
    print(f"✓ role: {table_info.get('role')}")
    print(f"✓ grain: {table_info.get('grain')[:50]}...")  # First 50 chars
    break  # Nur erste Tabelle zeigen

print("\n✓ .items() funktioniert perfekt!")
