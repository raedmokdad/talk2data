"""
Automatisierte Tests für Talk2Data Agent
Testet verschiedene Frage-Typen und prüft SQL-Qualität
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from src.llm_sql_generator import generate_multi_table_sql
import logging

logging.basicConfig(level=logging.WARNING)  # Weniger Logs für bessere Lesbarkeit

def test_query(question, expected_tables=None, expected_keywords=None):
    """Testet eine einzelne Frage"""
    print("\n" + "=" * 70)
    print(f"FRAGE: {question}")
    print("=" * 70)
    
    try:
        sql = generate_multi_table_sql(question, schema_name="retial_star_schema")
        
        print("\nGENERIERTE SQL:")
        print("-" * 70)
        print(sql)
        print("-" * 70)
        
        # Prüfungen
        checks_passed = 0
        checks_total = 0
        
        # Check 1: SQL nicht leer
        checks_total += 1
        if sql and len(sql) > 10:
            print("✓ SQL generiert (nicht leer)")
            checks_passed += 1
        else:
            print("✗ SQL zu kurz oder leer")
        
        # Check 2: SELECT vorhanden
        checks_total += 1
        if "SELECT" in sql.upper():
            print("✓ SELECT Statement vorhanden")
            checks_passed += 1
        else:
            print("✗ Kein SELECT gefunden")
        
        # Check 3: FROM vorhanden
        checks_total += 1
        if "FROM" in sql.upper():
            print("✓ FROM Clause vorhanden")
            checks_passed += 1
        else:
            print("✗ Kein FROM gefunden")
        
        # Check 4: Erwartete Tabellen
        if expected_tables:
            checks_total += 1
            tables_found = all(table in sql for table in expected_tables)
            if tables_found:
                print(f"✓ Alle erwarteten Tabellen gefunden: {expected_tables}")
                checks_passed += 1
            else:
                missing = [t for t in expected_tables if t not in sql]
                print(f"✗ Fehlende Tabellen: {missing}")
        
        # Check 5: JOINs bei Multi-Table
        if expected_tables and len(expected_tables) > 1:
            checks_total += 1
            if "JOIN" in sql.upper():
                join_count = sql.upper().count("JOIN")
                print(f"✓ JOINs vorhanden ({join_count} JOINs)")
                checks_passed += 1
            else:
                print("✗ Keine JOINs gefunden (aber mehrere Tabellen erwartet)")
        
        # Check 6: Erwartete Keywords
        if expected_keywords:
            for keyword in expected_keywords:
                checks_total += 1
                if keyword.upper() in sql.upper():
                    print(f"✓ Keyword '{keyword}' gefunden")
                    checks_passed += 1
                else:
                    print(f"⚠ Keyword '{keyword}' nicht gefunden (optional)")
        
        # Check 7: Keine gefährlichen Commands
        checks_total += 1
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER"]
        if not any(cmd in sql.upper() for cmd in dangerous):
            print("✓ Keine gefährlichen SQL-Commands")
            checks_passed += 1
        else:
            print("✗ WARNUNG: Gefährliche SQL-Commands gefunden!")
        
        # Ergebnis
        success_rate = (checks_passed / checks_total) * 100
        print(f"\n{'='*70}")
        print(f"ERGEBNIS: {checks_passed}/{checks_total} Checks bestanden ({success_rate:.0f}%)")
        
        if success_rate >= 80:
            print("STATUS: ✓ ✓ ✓ EXCELLENT")
        elif success_rate >= 60:
            print("STATUS: ✓ GOOD")
        else:
            print("STATUS: ⚠ NEEDS REVIEW")
        
        return success_rate >= 60
        
    except Exception as e:
        print(f"\n✗ ✗ ✗ FEHLER: {e}")
        return False


print("=" * 70)
print("AUTOMATISIERTE TESTS - TALK2DATA AGENT")
print("=" * 70)

tests_passed = 0
tests_total = 0

# Test 1: Einfache Multi-Table Frage
tests_total += 1
if test_query(
    "Wie viel Umsatz hatte Store Hamburg im Januar 2023?",
    expected_tables=["fact_sales", "dim_store", "dim_date"],
    expected_keywords=["SUM", "WHERE"]
):
    tests_passed += 1

# Test 2: Meta-Frage (nur Dimension)
tests_total += 1
if test_query(
    "Welche Stores gibt es in der Datenbank?",
    expected_tables=["dim_store"],
    expected_keywords=["SELECT"]
):
    tests_passed += 1

# Test 3: Aggregation ohne Store-Filter
tests_total += 1
if test_query(
    "Was ist der Gesamtumsatz über alle Verkäufe?",
    expected_tables=["fact_sales"],
    expected_keywords=["SUM"]
):
    tests_passed += 1

# Test 4: Top N mit Zeitfilter
tests_total += 1
if test_query(
    "Zeige die Top 5 Produkte nach Umsatz in Q1 2023",
    expected_tables=["fact_sales", "dim_product", "dim_date"],
    expected_keywords=["GROUP BY", "ORDER BY", "LIMIT"]
):
    tests_passed += 1

# Test 5: Zeitbasierte Frage
tests_total += 1
if test_query(
    "Wie hoch ist der durchschnittliche Umsatz an Montagen?",
    expected_tables=["fact_sales", "dim_date"],
    expected_keywords=["AVG"]
):
    tests_passed += 1

# Test 6: Komplexe Multi-Dimension
tests_total += 1
if test_query(
    "Welcher Store hatte den höchsten Umsatz mit Produkt Laptop an Wochentagen?",
    expected_tables=["fact_sales", "dim_store", "dim_product", "dim_date"],
    expected_keywords=["WHERE", "GROUP BY"]
):
    tests_passed += 1

# Test 7: Englische Frage
tests_total += 1
if test_query(
    "What is the total revenue for all stores in 2023?",
    expected_tables=["fact_sales"],
    expected_keywords=["SUM", "WHERE"]
):
    tests_passed += 1

# Zusammenfassung
print("\n" + "=" * 70)
print("GESAMTERGEBNIS")
print("=" * 70)
print(f"Tests bestanden: {tests_passed}/{tests_total}")
success_rate = (tests_passed / tests_total) * 100
print(f"Erfolgsrate: {success_rate:.1f}%")

if success_rate >= 85:
    print("\n🎉 🎉 🎉 EXZELLENT! System ist production-ready!")
elif success_rate >= 70:
    print("\n✓ ✓ GUT! System funktioniert solide")
elif success_rate >= 50:
    print("\n⚠ OK - Einige Verbesserungen nötig")
else:
    print("\n✗ PROBLEME - System braucht Überarbeitung")

print("=" * 70)
