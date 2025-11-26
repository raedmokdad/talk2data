"""
Test: Multi-Table SQL Generation
Tests ob generate_multi_table_sql() korrekte SQL mit JOINs erstellt
"""

from src.llm_sql_generator import generate_multi_table_sql
import logging

# Enable logging to see what's happening
logging.basicConfig(level=logging.INFO)

print("=" * 60)
print("TEST: Multi-Table SQL Generation")
print("=" * 60)

# Test 1: Einfache Multi-Table Frage
print("\n" + "=" * 60)
print("TEST 1: Store + Datum Filter")
print("=" * 60)
question1 = "Wie viel Umsatz hatte Store Hamburg im Januar 2023?"
print(f"Frage: {question1}\n")

sql1 = generate_multi_table_sql(question1)
print("Generierte SQL:")
print("-" * 60)
print(sql1)
print("-" * 60)

# Prüfe ob JOINs enthalten sind
if "JOIN" in sql1.upper():
    print("✓ SQL enthält JOINs")
    if "dim_store" in sql1 and "dim_date" in sql1:
        print("✓ Beide Dimensionen (dim_store, dim_date) verwendet")
    if "Hamburg" in sql1 or "store_name" in sql1:
        print("✓ Store-Filter enthalten")
    if "January" in sql1 or "month" in sql1 or "01" in sql1:
        print("✓ Datum-Filter enthalten")
else:
    print("⚠ Keine JOINs gefunden")

# Test 2: Komplexe Aggregation
print("\n" + "=" * 60)
print("TEST 2: Top Produkte mit Zeit-Filter")
print("=" * 60)
question2 = "Zeige die Top 5 Produkte nach Umsatz in Q1 2023"
print(f"Frage: {question2}\n")

sql2 = generate_multi_table_sql(question2)
print("Generierte SQL:")
print("-" * 60)
print(sql2)
print("-" * 60)

if "JOIN" in sql2.upper():
    print("✓ SQL enthält JOINs")
if "SUM" in sql2.upper() or "GROUP BY" in sql2.upper():
    print("✓ Aggregation enthalten")
if "LIMIT 5" in sql2 or "TOP 5" in sql2:
    print("✓ TOP 5 Limit gesetzt")
if "ORDER BY" in sql2.upper():
    print("✓ Sortierung enthalten")

# Test 3: Nur Dimension-Abfrage (keine fact table)
print("\n" + "=" * 60)
print("TEST 3: Meta-Frage ohne Fact Table")
print("=" * 60)
question3 = "Welche Stores gibt es in der Datenbank?"
print(f"Frage: {question3}\n")

sql3 = generate_multi_table_sql(question3)
print("Generierte SQL:")
print("-" * 60)
print(sql3)
print("-" * 60)

if "dim_store" in sql3:
    print("✓ dim_store verwendet")
if "fact_sales" not in sql3:
    print("✓ KORREKT: Keine fact_sales (nicht benötigt)")
else:
    print("⚠ fact_sales enthalten (unnötig, aber nicht falsch)")

# Test 4: Alle Dimensionen
print("\n" + "=" * 60)
print("TEST 4: Komplexe Frage mit mehreren Dimensionen")
print("=" * 60)
question4 = "Welcher Store hatte den höchsten Umsatz mit Produkt 'Laptop' an Wochentagen?"
print(f"Frage: {question4}\n")

sql4 = generate_multi_table_sql(question4)
print("Generierte SQL:")
print("-" * 60)
print(sql4)
print("-" * 60)

join_count = sql4.upper().count("JOIN")
print(f"Anzahl JOINs: {join_count}")

if join_count >= 2:
    print("✓ Mehrere JOINs enthalten")
if "dim_store" in sql4 and "dim_product" in sql4 and "dim_date" in sql4:
    print("✓ Alle 3 Dimensionen verwendet")

print("\n" + "=" * 60)
print("✓ TEST COMPLETED - 4 Multi-Table Queries generiert")
print("=" * 60)
