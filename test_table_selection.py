"""
Test: LLM Table Selection
Tests ob das LLM die richtigen Tabellen auswählt
"""

from src.schema_parser import get_schema_parser

print("=" * 60)
print("TEST: LLM Table Selection")
print("=" * 60)

# Schema laden
parser = get_schema_parser("retial_star_schema")
print(f"\n✓ Schema geladen: {len(parser.tables)} Tabellen")
print(f"  Verfügbare Tabellen: {list(parser.tables.keys())}")

# Test 1: Frage mit Store und Datum
print("\n" + "=" * 60)
print("TEST 1: Umsatzfrage mit Store und Datum")
print("=" * 60)
question1 = "Wie viel Umsatz hatte Store Hamburg im Januar 2023?"
print(f"Frage: {question1}")
print(f"\nErwartete Tabellen: ['fact_sales', 'dim_store', 'dim_date']")

selected_tables1 = parser.get_relevant_tables(question1)
print(f"LLM ausgewählt: {selected_tables1}")

if set(selected_tables1) == {"fact_sales", "dim_store", "dim_date"}:
    print("✓ ✓ ✓ PERFEKT! Alle richtigen Tabellen ausgewählt")
else:
    print("⚠ Andere Tabellen ausgewählt (könnte trotzdem funktionieren)")

# Test 2: Frage nur mit Produkt
print("\n" + "=" * 60)
print("TEST 2: Produktfrage")
print("=" * 60)
question2 = "Welche Produkte sind verfügbar?"
print(f"Frage: {question2}")
print(f"\nErwartete Tabellen: ['dim_product']")

selected_tables2 = parser.get_relevant_tables(question2)
print(f"LLM ausgewählt: {selected_tables2}")

if "dim_product" in selected_tables2:
    print("✓ dim_product enthalten")
else:
    print("⚠ dim_product fehlt")

# Test 3: Komplexe Frage
print("\n" + "=" * 60)
print("TEST 3: Komplexe Frage mit mehreren Dimensionen")
print("=" * 60)
question3 = "Zeige mir die Top 5 Produkte nach Umsatz für alle Stores in Q1 2023"
print(f"Frage: {question3}")
print(f"\nErwartete Tabellen: Alle 4 (fact_sales + alle dims)")

selected_tables3 = parser.get_relevant_tables(question3)
print(f"LLM ausgewählt: {selected_tables3}")

if len(selected_tables3) == 4:
    print(f"✓ Alle {len(selected_tables3)} Tabellen ausgewählt")
else:
    print(f"⚠ {len(selected_tables3)} von 4 Tabellen ausgewählt")

# Test 4: Trick-Frage - Nur Berechnung ohne Dimensionen
print("\n" + "=" * 60)
print("TEST 4: Trick-Frage - Gesamtumsatz ohne Filter")
print("=" * 60)
question4 = "Was ist der Gesamtumsatz über alle Verkäufe?"
print(f"Frage: {question4}")
print(f"\nErwartete Tabellen: ['fact_sales'] (keine Dimensionen nötig)")

selected_tables4 = parser.get_relevant_tables(question4)
print(f"LLM ausgewählt: {selected_tables4}")

if selected_tables4 == ["fact_sales"]:
    print("✓ ✓ ✓ PERFEKT! Nur fact_sales ohne unnötige Dimensionen")
elif "fact_sales" in selected_tables4:
    print(f"⚠ fact_sales enthalten, aber auch: {[t for t in selected_tables4 if t != 'fact_sales']}")
else:
    print("✗ fact_sales fehlt!")

# Test 5: Zeitbasierte Frage mit spezifischem Wochentag
print("\n" + "=" * 60)
print("TEST 5: Schwere Zeitfrage - Wochentag")
print("=" * 60)
question5 = "Wie hoch ist der durchschnittliche Umsatz an Montagen?"
print(f"Frage: {question5}")
print(f"\nErwartete Tabellen: ['fact_sales', 'dim_date'] (day_name in dim_date)")

selected_tables5 = parser.get_relevant_tables(question5)
print(f"LLM ausgewählt: {selected_tables5}")

if set(selected_tables5) == {"fact_sales", "dim_date"}:
    print("✓ ✓ ✓ PERFEKT! Erkannt dass dim_date für day_name nötig ist")
elif "dim_date" in selected_tables5:
    print("✓ dim_date enthalten (gut!)")
else:
    print("✗ dim_date fehlt - LLM hat nicht erkannt dass day_name in dim_date ist")

# Test 6: Ambiguitäts-Test - "Store" könnte Name oder Key sein
print("\n" + "=" * 60)
print("TEST 6: Ambiguität - Store Name vs Store Table")
print("=" * 60)
question6 = "Wie viele Verkäufe gab es in Hamburg?"
print(f"Frage: {question6}")
print(f"\nErwartete Tabellen: ['fact_sales', 'dim_store'] (Hamburg = store_name)")

selected_tables6 = parser.get_relevant_tables(question6)
print(f"LLM ausgewählt: {selected_tables6}")

if "dim_store" in selected_tables6:
    print("✓ dim_store enthalten - LLM hat erkannt dass Hamburg ein Store-Name ist")
else:
    print("✗ dim_store fehlt - LLM hat nicht erkannt dass Hamburg ein Store ist")

# Test 7: Sehr schwere Frage - Implizite Zeitlogik
print("\n" + "=" * 60)
print("TEST 7: SCHWER - Implizite Zeitberechnung")
print("=" * 60)
question7 = "Welche Produkte hatten Umsatzrückgang im Vergleich zum Vorjahresmonat?"
print(f"Frage: {question7}")
print(f"\nErwartete Tabellen: ['fact_sales', 'dim_date', 'dim_product']")
print("  (Vergleich = dim_date für year/month, dim_product für Produkte)")

selected_tables7 = parser.get_relevant_tables(question7)
print(f"LLM ausgewählt: {selected_tables7}")

expected = {"fact_sales", "dim_date", "dim_product"}
if set(selected_tables7) == expected:
    print("✓ ✓ ✓ EXZELLENT! LLM hat komplexe Zeitvergleichslogik verstanden")
elif "dim_date" in selected_tables7 and "dim_product" in selected_tables7:
    print("✓ Gute Auswahl - beide kritischen Dimensionen enthalten")
else:
    missing = expected - set(selected_tables7)
    print(f"⚠ Fehlende Tabellen: {missing}")

# Test 8: Meta-Frage - Keine fact table nötig
print("\n" + "=" * 60)
print("TEST 8: Meta-Frage - Nur Dimension Info")
print("=" * 60)
question8 = "Welche Stores gibt es in der Datenbank?"
print(f"Frage: {question8}")
print(f"\nErwartete Tabellen: ['dim_store'] (keine Sales-Daten nötig)")

selected_tables8 = parser.get_relevant_tables(question8)
print(f"LLM ausgewählt: {selected_tables8}")

if selected_tables8 == ["dim_store"]:
    print("✓ ✓ ✓ PERFEKT! Nur dim_store, keine fact_sales")
elif "dim_store" in selected_tables8 and "fact_sales" not in selected_tables8:
    print("✓ dim_store enthalten, keine überflüssige fact_sales")
else:
    print(f"⚠ Auswahl: {selected_tables8}")

print("\n" + "=" * 60)
print("✓ TEST COMPLETED - 8 Tests ausgeführt")
print("=" * 60)
