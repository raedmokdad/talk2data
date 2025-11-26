"""
Test: Singleton Pattern für SchemaParser
Zeigt dass das Schema nur einmal geladen wird
"""

from src.schema_parser import get_schema_parser

print("=" * 60)
print("TEST: Singleton Pattern")
print("=" * 60)

# Erster Aufruf - sollte Schema laden
print("\n1. Aufruf von get_schema_parser()...")
parser1 = get_schema_parser("retial_star_schema")
print(f"✓ Parser1 erstellt")
print(f"  Anzahl Tabellen: {len(parser1.tables)}")
print(f"  Tabellen: {list(parser1.tables.keys())}")

# Zweiter Aufruf - sollte NICHT neu laden
print("\n2. Aufruf von get_schema_parser()...")
parser2 = get_schema_parser("retial_star_schema")
print(f"✓ Parser2 erstellt")

# Prüfen ob es dieselbe Instanz ist
print("\n" + "=" * 60)
print("VERGLEICH:")
print("=" * 60)
print(f"parser1 ID: {id(parser1)}")
print(f"parser2 ID: {id(parser2)}")
print(f"Sind identisch: {parser1 is parser2}")

if parser1 is parser2:
    print("\n✓ ✓ ✓ SINGLETON FUNKTIONIERT!")
    print("Schema wurde nur einmal geladen, beide Parser sind dieselbe Instanz")
else:
    print("\n✗ ✗ ✗ FEHLER: Zwei verschiedene Instanzen!")

print("\n" + "=" * 60)
print("✓ TEST COMPLETED")
print("=" * 60)
