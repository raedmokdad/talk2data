# 🎯 Phase 0 - Revidierter Plan (basierend auf aktuellem Stand)

**Datum**: 25. November 2025  
**Dauer**: 1 Woche (Montag-Freitag)  
**Ziel**: System Multi-Tenant-ready + Production-ready machen

---

## 📊 Aktueller Stand (Was bereits da ist)

### ✅ Bereits implementiert (15-20%)
- S3-Service nutzt bereits `schemas/{username}/{schema_name}.json` Struktur
- SchemaParser liest `kpis` korrekt aus Root-Level
- JOIN-Engine funktioniert (automatic table selection + JOIN generation)
- Date-Converter existiert und funktioniert

### ❌ Kritische Lücken (80%)
- `/generate-sql` ignoriert `username` → lädt nur lokale Files
- SchemaParser kann keine S3-Dictionaries laden
- Schema-Builder schreibt `metrics` (Parser liest `kpis`) → Daten-Bug
- SQL-Validator komplett deaktiviert → Sicherheitslücke
- Streamlit Username inkonsistent

---

## 👥 Rollenverteilung

### **Mo** (7,5h/Tag = 37,5h/Woche)
**Fokus**: Technische Implementation + System-Integration

### **Raed** (4h/Tag = 20h/Woche)  
**Fokus**: Business-Logik + Architektur + Testing

---

# 📋 Woche 1: Phase 0 Tasks

## 🔴 Tag 1 (Montag) - Foundation Day

### ☀️ Vormittag (9:00-12:00)

#### **P0-15: Kickoff-Call** [1h] - BEIDE
- Username-Strategie diskutieren
- Cognito Token-Felder prüfen (`cognito:username` vs Email)
- S3-Pfad-Konvention final festlegen
- Wochenplanung durchgehen

**Deliverable**: Gemeinsames Verständnis der Architektur

---

#### **P0-01: Username-Quelle festlegen** [2h] - BEIDE
**Owner**: Mo + Raed

**Aufgaben**:
1. Cognito JWT Token analysieren:
   ```python
   # Welches Feld nutzen wir?
   - cognito:username (Empfehlung)
   - email
   - sub (User-ID)
   ```

2. Entscheidung dokumentieren:
   - Master-Username-Feld: `cognito:username`
   - S3-Pfad: `s3://smart-forecast/schemas/{cognito:username}/{schema_name}.json`
   - Streamlit Session: `st.session_state.username = cognito:username`

3. Flow zeichnen:
   ```
   Cognito Login → JWT → API → S3 → SchemaParser → SQL Generator
   ```

**Deliverable**: Klare Username-Strategie (verbal, wird in P0-11 dokumentiert)

---

### 🌙 Nachmittag (13:00-18:00)

#### **Mo's Aufgaben** [5,5h]

##### **P0-02: API - Username aus Request nutzen** [4h] - MO
**Dateien**: `api_service.py`

**Problem**: 
```python
# AKTUELL (Zeile 122):
schema_name = request.schema_name if request.schema_name else "retial_star_schema"
sql_query = generate_multi_table_sql(
    user_question=request.question.strip(),
    schema_name=schema_name  # ❌ Lädt nur lokale Files!
)
```

**Lösung**:
```python
# NEU:
username = request.username if request.username else "demo_user"
schema_name = request.schema_name if request.schema_name else "retial_star_schema"

# Schema aus S3 laden
from src.s3_service import get_user_schema
success, schema_data = get_user_schema(username, schema_name)

if not success:
    raise HTTPException(404, f"Schema '{schema_name}' not found for user {username}")

# SQL mit S3-Schema generieren
sql_query = generate_multi_table_sql(
    user_question=request.question.strip(),
    schema_data=schema_data,  # NEU: Dictionary aus S3
    username=username
)
```

**Akzeptanzkriterien**:
- ✅ `/generate-sql` lädt Schema aus S3 (nicht mehr lokale Files)
- ✅ `username` Parameter wird genutzt
- ✅ Test mit 2 Usern: raedmokdad, demo_user

---

##### **P0-06: Schema-Format Start** [1,5h] - MO
**Dateien**: `streamlit_schema_builder.py`

**Problem**: Builder schreibt `["schema"]["metrics"]`, Parser liest `["kpis"]`

**Aufgabe**: Anfangen mit Umbenennung
- Tab-Label: "Metrics" → "KPIs"
- Kommentare anpassen
- Vorbereitung für morgen

---

#### **Raed's Aufgaben** [2h]

##### **P0-12: Business-KPIs erweitern (Start)** [2h] - RAED
**Dateien**: `src/config/retial_star_schema.json`

**Neue KPIs hinzufügen**:

```json
{
  "kpis": {
    // ... bestehende KPIs (net_sales, gross_sales, etc.)
    
    "profit": {
      "formula": "SUM(fact_sales.sales_amount - fact_sales.discount_amount - fact_sales.cost_amount)",
      "description": "Total profit (revenue minus costs)",
      "required_tables": ["fact_sales"],
      "keywords": ["gewinn", "profit", "ertrag", "überschuss"]
    },
    
    "profit_margin": {
      "formula": "(SUM(fact_sales.sales_amount - fact_sales.discount_amount) - SUM(fact_sales.cost_amount)) / NULLIF(SUM(fact_sales.sales_amount - fact_sales.discount_amount), 0) * 100",
      "description": "Profit margin as percentage of net sales",
      "required_tables": ["fact_sales"],
      "keywords": ["marge", "gewinnspanne", "profitabilität", "margin"]
    },
    
    "revenue_growth": {
      "formula": "(current_period_revenue - previous_period_revenue) / NULLIF(previous_period_revenue, 0) * 100",
      "description": "Revenue growth percentage compared to previous period",
      "required_tables": ["fact_sales", "dim_date"],
      "keywords": ["wachstum", "growth", "steigerung", "zunahme"]
    }
  }
}
```

**Akzeptanzkriterien**:
- ✅ 3 neue KPIs im Schema
- ✅ Deutsche + englische Keywords

---

## 🔴 Tag 2 (Dienstag) - Multi-Tenant Core

### **Mo's Aufgaben** [7,5h]

#### **P0-03: SchemaParser - S3 Dictionary-Support** [6h] - MO
**Dateien**: `src/schema_parser.py`, `src/llm_sql_generator.py`

**Problem**: Parser kann nur lokale JSON-Files laden

**Lösung**:

**1. SchemaParser Constructor erweitern** [2h]:
```python
class SchemaParser:
    def __init__(self, schema_name: str = None, schema_data: Dict = None, username: str = None):
        self.schema_name = schema_name
        self.username = username
        self.schema_data = schema_data  # NEU: Kann Dictionary sein
        # ... rest
```

**2. load_star_schema() anpassen** [2h]:
```python
def load_star_schema(self) -> Dict:
    # Fall 1: Schema-Data bereits vorhanden (aus S3)
    if self.schema_data is not None:
        self._parse_tables()
        self._parse_relationships()
        self._parse_synonyms()
        self._parse_kpis()
        self._parse_notes()
        self._parse_examples()
        self._parse_glossary()
        logger.info(f"Loaded schema from dictionary for user {self.username}")
        return self.schema_data
    
    # Fall 2: Lokale File (Fallback für Tests)
    if self.schema_name:
        # ... bestehender Code bleibt
```

**3. Singleton/Cache für Multi-Tenant** [2h]:
```python
_schema_parser_cache = {}  # NEU: Cache pro (user, schema)

def get_schema_parser(
    schema_name: str = None, 
    schema_data: Dict = None, 
    username: str = None
) -> SchemaParser:
    # Cache-Key basierend auf User + Schema
    if username and schema_name:
        cache_key = f"{username}:{schema_name}"
    else:
        cache_key = schema_name or "default"
    
    # Nur cachen wenn noch nicht vorhanden
    if cache_key not in _schema_parser_cache:
        parser = SchemaParser(
            schema_name=schema_name,
            schema_data=schema_data,
            username=username
        )
        parser.load_star_schema()
        _schema_parser_cache[cache_key] = parser
    
    return _schema_parser_cache[cache_key]
```

**4. llm_sql_generator.py anpassen**:
```python
def generate_multi_table_sql(
    user_question: str, 
    schema_name: str = None,
    schema_data: Dict = None,  # NEU
    username: str = None,      # NEU
    validator=None
) -> str:
    # ...
    parser = get_schema_parser(
        schema_name=schema_name,
        schema_data=schema_data,
        username=username
    )
    # ... rest bleibt gleich
```

**Akzeptanzkriterien**:
- ✅ SchemaParser akzeptiert Dictionary aus S3
- ✅ Cache funktioniert pro `(username, schema_name)`
- ✅ Alte Tests mit lokalen Files laufen weiterhin
- ✅ End-to-End Test: User-Frage → S3-Schema → SQL

---

#### **P0-06: Schema-Format vereinheitlichen (Fortsetzung)** [1,5h] - MO
**Dateien**: `streamlit_schema_builder.py`

**Alle `metrics` Referenzen ersetzen**:
```python
# VORHER:
st.session_state.schema_data["schema"]["metrics"] = {}

# NACHHER:
st.session_state.schema_data["kpis"] = {}
```

**Suchen & Ersetzen**:
- `["schema"]["metrics"]` → `["kpis"]`
- `.get("metrics", {})` → `.get("kpis", {})`
- Tab-Label: "📈 Metrics" → "📈 KPIs"

**Akzeptanzkriterien**:
- ✅ Builder schreibt `kpis` (nicht mehr `metrics`)
- ✅ Upload nach S3 funktioniert

---

### **Raed's Aufgaben** [4h]

#### **P0-12: Business-KPIs fertigstellen** [2h] - RAED
Weiter an KPIs arbeiten + testen

---

#### **P0-13: Glossary erweitern** [2h] - RAED
**Dateien**: `src/config/retial_star_schema.json`

```json
{
  "glossary": {
    // ... bestehende Einträge
    
    "profit": "Gewinn = Nettoumsatz minus Kosten. Zeigt die tatsächliche Rentabilität nach Abzug aller Ausgaben.",
    "profit_margin": "Gewinnmarge = (Gewinn / Nettoumsatz) × 100. Prozentuale Rentabilität. Eine Marge von 20% bedeutet: 20 Cent Gewinn pro Euro Umsatz.",
    "cost_of_goods": "Wareneinsatz = Kosten für eingekaufte/produzierte Waren. Basis für Gewinnberechnung.",
    "gross_margin": "Bruttogewinnspanne = (Umsatz - Wareneinsatz) / Umsatz. Zeigt Rohgewinn vor Betriebskosten.",
    "loss": "Verlust = Negative Differenz zwischen Einnahmen und Ausgaben. Tritt auf, wenn Kosten höher als Umsatz.",
    "break_even": "Break-Even-Point = Punkt, an dem Umsatz = Kosten. Ab hier wird Gewinn gemacht.",
    "revenue_growth": "Umsatzwachstum = Prozentuale Veränderung des Umsatzes im Vergleich zur Vorperiode. Positiv = Wachstum, negativ = Rückgang."
  }
}
```

**Akzeptanzkriterien**:
- ✅ 7+ neue Glossar-Einträge
- ✅ Klare, business-verständliche Definitionen

---

## 🔴 Tag 3 (Mittwoch) - Streamlit Integration

### **Mo's Aufgaben** [7,5h]

#### **P0-04: Talk2Data Streamlit - Username korrigieren** [3h] - MO
**Dateien**: `streamlit_app_auth.py`

**Problem** (Zeile 799):
```python
username = st.session_state.user_email.split('@')[0] if st.session_state.user_email else "demo_user"
```

**Lösung**:
```python
# Nach Login (Zeile 78):
if success:
    st.session_state.authenticated = True
    st.session_state.user_tokens = result['tokens']
    st.session_state.username = result['username']  # ← Cognito Username
    st.session_state.user_email = result.get('email', '')

# Später bei API-Calls (überall wo Schema geladen wird):
username = st.session_state.get('username', 'demo_user')

# API Request:
response = requests.post(
    f"{API_URL}/generate-sql",
    json={
        "question": user_question,
        "schema_name": selected_schema,
        "username": username  # ← Cognito Username
    }
)
```

**Alle Stellen anpassen**:
- Schema-Upload: `upload_user_schema(username, ...)`
- Schema-Liste laden: `list_user_schema(username)`
- SQL-Generierung: API-Request mit `username`

**Akzeptanzkriterien**:
- ✅ Kein `email.split('@')[0]` mehr
- ✅ `st.session_state.username` wird überall genutzt
- ✅ Test: Login → Schema laden → Query → funktioniert

---

#### **P0-05: Schema-Builder - Multi-User** [2,5h] - MO
**Dateien**: `streamlit_schema_builder.py`

**Problem**: Hardcoded `"raedmokdad"`

**Lösung**:
```python
# Nicht mehr hardcoded:
username = st.session_state.get('username', 'demo_user')

# Upload to S3:
success, message = upload_user_schema(
    username,  # Aus Session State
    schema_name,
    schema_data
)

# Schema laden:
success, schemas = list_user_schema(username)
```

**Akzeptanzkriterien**:
- ✅ Kein hardcoded Username
- ✅ Schema landet im richtigen S3-Pfad

---

#### **P0-07: Parser - Fallback für alte `metrics`** [2h] - MO
**Dateien**: `src/schema_parser.py`

**Für Migration-Phase**:
```python
def _parse_kpis(self):
    """Parse KPIs - mit Fallback für alte 'metrics' Struktur"""
    
    # Primär: Root-Level "kpis"
    if "kpis" in self.schema_data:
        self.kpis = self.schema_data["kpis"]
    
    # Fallback: Schema-Level "metrics" (alte Struktur)
    elif "metrics" in self.schema_data.get("schema", {}):
        logger.warning(f"Old 'metrics' format in schema {self.schema_name}, consider migrating")
        self.kpis = self.schema_data["schema"]["metrics"]
    
    else:
        self.kpis = {}
    
    logger.info(f"Loaded {len(self.kpis)} KPIs")
```

**Akzeptanzkriterien**:
- ✅ Parser liest sowohl `kpis` als auch alte `metrics`
- ✅ Warning im Log bei alter Struktur

---

### **Raed's Aufgaben** [4h]

#### **P0-14: Business-Fragen definieren** [4h] - RAED
**Erstelle**: `docs/TEST_SCENARIOS_PHASE_0.md`

**15-20 Business-Fragen mit Kontext**:

```markdown
# Test-Szenarien für Phase 0

## Kategorie: Basic Aggregation

### 1. Gesamtumsatz
**Frage**: "Wie hoch ist der Gesamtumsatz im Jahr 2024?"
**Erwartete Tabellen**: fact_sales, dim_date
**Erwartete KPI**: gross_sales
**Erwartete Dimensionen**: Jahr
**Erwartetes SQL-Pattern**:
```sql
SELECT SUM(f.sales_amount) as total_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.year = 2024
LIMIT 100
```

### 2. Umsatz pro Region
**Frage**: "Umsatz pro Region im letzten Jahr"
**Erwartete Tabellen**: fact_sales, dim_store, dim_date
**Erwartete KPI**: gross_sales
**Erwartete Dimensionen**: Region, Jahr
...

## Kategorie: Business-KPIs

### 5. Gewinnmarge
**Frage**: "Wie hoch ist die Gewinnmarge pro Filiale?"
**Erwartete Tabellen**: fact_sales, dim_store
**Erwartete KPI**: profit_margin
**Erwartete Dimensionen**: Filiale
...

## Kategorie: Zeitvergleiche (Vorbereitung Phase 1)

### 10. Umsatz-Wachstum
**Frage**: "Ist der Umsatz im Vergleich zum Vorjahr gestiegen?"
**Erwartete Tabellen**: fact_sales, dim_date
**Erwartete KPI**: revenue_growth
**Erwartete Logik**: YoY-Vergleich
**Hinweis**: Wird in Phase 1 implementiert
...

(Insgesamt 15-20 Szenarien)
```

**Akzeptanzkriterien**:
- ✅ 15-20 Fragen dokumentiert
- ✅ Jede mit erwarteter KPI + Tabellen
- ✅ Abdeckung: Aggregation, Multi-Dimension, KPIs, Zeit (Prep)

---

## 🔴 Tag 4 (Donnerstag) - SQL Validator

### **Mo's Aufgaben** [7,5h]

#### **P0-09: SQL-Validator für Multi-Table** [5h] - MO
**Dateien**: `src/sql_validator.py`

**Aufgabe**: Validator anpassen für Multi-Table-Queries

**1. Constructor erweitern** [1,5h]:
```python
class SQLValidator:
    def __init__(self, schema: Dict = None, allowed_tables: List[str] = None):
        self.schema = schema
        self.allowed_tables = allowed_tables or []
        
        # Extrahiere Tabellen + Spalten aus Schema
        if schema:
            self.table_columns = self._extract_table_columns(schema)
        
        # JOIN-Pattern ENTFERNEN (nicht mehr blocken)
        self.pattern_labels = {
            r";\s*(DROP|DELETE|UPDATE|ALTER|INSERT)": "Destructive SQL",
            r"--": "SQL comment injection",
            # ... andere Patterns
            # ❌ JOIN-Pattern LÖSCHEN
        }
```

**2. Tabellen-Whitelist Check** [1,5h]:
```python
def _check_table_whitelist(self, sql: str):
    """Prüft, ob alle Tabellen erlaubt sind"""
    tables_in_query = re.findall(
        r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        sql,
        re.IGNORECASE
    )
    
    for table in tables_in_query:
        if table.lower() not in [t.lower() for t in self.allowed_tables]:
            return False, f"Unknown table: {table}", table
    
    return True, "OK", None
```

**3. validate() anpassen** [2h]:
```python
def validate(self, sql: str):
    checks = [
        self._check_forbidden_commands,
        self._check_dangerous_pattern,
        self._check_table_whitelist,  # NEU
        self._check_limit,
    ]
    
    errors = []
    for check in checks:
        passed, message, _ = check(sql)
        if not passed:
            errors.append(message)
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "OK"
```

**Akzeptanzkriterien**:
- ✅ JOINs zwischen erlaubten Tabellen sind OK
- ✅ Unbekannte Tabellen werden abgelehnt
- ✅ Destruktive Commands werden geblockt

---

#### **P0-10: Validator-Tests** [2,5h] - MO
**Erstelle**: `test_sql_validator_multitable.py`

**Positive Tests** (sollten durchgehen):
```python
def test_valid_multi_table_join():
    validator = SQLValidator(
        schema=retail_schema,
        allowed_tables=["fact_sales", "dim_date", "dim_store"]
    )
    
    sql = """
    SELECT f.sales_amount, d.date, s.store_name
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_store s ON f.store_key = s.store_key
    WHERE d.year = 2024
    LIMIT 100
    """
    
    passed, message = validator.validate(sql)
    assert passed, f"Valid query rejected: {message}"
```

**Negative Tests** (sollten abgelehnt werden):
```python
def test_reject_unknown_table():
    sql = "SELECT * FROM evil_table LIMIT 100"
    passed, message = validator.validate(sql)
    assert not passed
    assert "Unknown table" in message

def test_reject_delete():
    sql = "DELETE FROM fact_sales WHERE 1=1"
    passed, message = validator.validate(sql)
    assert not passed
    assert "DELETE" in message
```

**5 positive, 5 negative Tests schreiben**

**Akzeptanzkriterien**:
- ✅ 10 Tests schreiben
- ✅ Alle Tests laufen durch
- ✅ Coverage: JOINs, unknown tables, destructive commands

---

### **Raed's Aufgaben** [4h]

#### **P0-11: Username-Strategie dokumentieren** [2h] - RAED
**Erstelle**: `docs/USERNAME_STRATEGY.md`

```markdown
# Username-Strategie für Talk2Data

**Datum**: 25. November 2025  
**Status**: Final

## Entscheidung

**Master Source of Truth**: `cognito:username` aus AWS Cognito JWT Token

## Architektur-Flow

```
┌─────────────┐
│ User Login  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ AWS Cognito     │
│ Returns JWT     │
│ - cognito:username
│ - email
│ - sub (user-id)
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ Streamlit App    │
│ st.session_state │
│ .username        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ FastAPI Backend  │
│ /generate-sql    │
│ {username: "..."}│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ S3 Service       │
│ Path:            │
│ schemas/         │
│  {username}/     │
│   {schema}.json  │
└──────────────────┘
```

## Beispiele

### User 1: raedmokdad
- Cognito Username: `raedmokdad`
- S3-Pfad: `s3://smart-forecast/schemas/raedmokdad/retial_star_schema.json`
- Streamlit Session: `st.session_state.username = "raedmokdad"`

### User 2: demo_user
- Cognito Username: `demo_user`
- S3-Pfad: `s3://smart-forecast/schemas/demo_user/my_schema.json`
- Streamlit Session: `st.session_state.username = "demo_user"`

## Implementierungs-Checklist

- [x] Cognito JWT-Feld festgelegt: `cognito:username`
- [x] S3-Pfad-Konvention: `schemas/{username}/{schema}.json`
- [ ] Streamlit nutzt `st.session_state.username` (P0-04)
- [ ] API nutzt `username` aus Request (P0-02)
- [ ] Schema-Builder nutzt Session-Username (P0-05)

## Sicherheit

- Username darf nur alphanumerische Zeichen + Unterstrich
- Path Traversal Prevention: Validierung in `s3_service.py`
- Multi-Tenant Isolation: Jeder User sieht nur eigene Schemas
```

**Akzeptanzkriterien**:
- ✅ Dokument existiert in `docs/`
- ✅ Flow-Diagramm vorhanden
- ✅ Beispiele für 2 User

---

#### **P0-08a Vorbereitung: Migration-Script Design** [2h] - RAED
**Aufgabe**: Design für Migrations-Script erstellen

**Dokumentiere** in `docs/SCHEMA_MIGRATION.md`:
```markdown
# Schema-Migration: metrics → kpis

## Betroffene Schemas (S3)
- raedmokdad/ecommerce_schema.json
- raedmokdad/employee_schema.json
- raedmokdad/retial_star_schema.json
- raedmokdad/rossman_schema.json
- raedmokdad/sales_analitics_schema.json

## Transformations-Logik

### Fall 1: metrics auf Schema-Level
```json
// VORHER:
{
  "schema": {
    "metrics": { ... }
  }
}

// NACHHER:
{
  "kpis": { ... }
}
```

### Fall 2: Bereits kpis
→ Keine Änderung nötig

## Test-Plan
1. Backup aller Schemas
2. Script lokal testen (mit Kopie)
3. Auf S3 anwenden
4. Validierung: Schema laden + Query testen
```

**Akzeptanzkriterien**:
- ✅ Transformations-Logik dokumentiert
- ✅ Liste betroffener Schemas

---

## 🔴 Tag 5 (Freitag) - Migration & Review

### **Mo's Aufgaben** [7,5h]

#### **P0-08a: Migrations-Script schreiben** [3h] - MO
**Erstelle**: `scripts/migrate_schemas_to_kpis.py`

```python
#!/usr/bin/env python3
"""
Schema-Migration: metrics → kpis
Migriert S3-Schemas vom alten Format (metrics) zum neuen (kpis)
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from s3_service import get_user_schema, upload_user_schema, list_user_schema

def migrate_schema(schema_data: dict) -> tuple[bool, dict]:
    """
    Migriert ein Schema von metrics zu kpis Format
    
    Returns:
        (changed, migrated_schema)
    """
    changed = False
    
    # Fall 1: metrics auf Schema-Level
    if "schema" in schema_data and "metrics" in schema_data["schema"]:
        print("  ✓ Found metrics on schema level")
        schema_data["kpis"] = schema_data["schema"].pop("metrics")
        changed = True
    
    # Fall 2: Bereits kpis vorhanden
    elif "kpis" in schema_data:
        print("  → Already has kpis, skipping")
    
    else:
        print("  → No metrics or kpis found")
    
    return changed, schema_data


def migrate_user_schemas(username: str, dry_run: bool = True):
    """Migriert alle Schemas eines Users"""
    print(f"\n{'='*60}")
    print(f"Migrating schemas for user: {username}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    # Liste alle Schemas
    success, schemas = list_user_schema(username)
    if not success:
        print(f"❌ Could not list schemas for {username}")
        return
    
    print(f"Found {len(schemas)} schemas\n")
    
    for schema_name in schemas:
        print(f"Processing: {schema_name}")
        
        # Schema laden
        success, schema_data = get_user_schema(username, schema_name)
        if not success:
            print(f"  ❌ Could not load schema")
            continue
        
        # Migrieren
        changed, migrated = migrate_schema(schema_data)
        
        if changed:
            if dry_run:
                print(f"  → Would upload migrated version (DRY RUN)")
            else:
                success, msg = upload_user_schema(username, schema_name, migrated)
                if success:
                    print(f"  ✅ Migrated and uploaded")
                else:
                    print(f"  ❌ Upload failed: {msg}")
        
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate schemas from metrics to kpis")
    parser.add_argument("username", help="Username to migrate schemas for")
    parser.add_argument("--live", action="store_true", help="Actually perform migration (default: dry-run)")
    
    args = parser.parse_args()
    
    migrate_user_schemas(args.username, dry_run=not args.live)
```

**Akzeptanzkriterien**:
- ✅ Script kann Schemas analysieren
- ✅ Dry-Run Mode zeigt was passieren würde
- ✅ Live-Mode migriert tatsächlich

---

#### **P0-02: API - Validator reaktivieren** [2h] - MO
**Dateien**: `api_service.py`

**Validator wieder aktivieren**:
```python
@app.post("/generate-sql")
async def generate_sql(request: QueryRequest):
    # ... Schema laden ...
    
    # SQL generieren
    sql_query = generate_multi_table_sql(...)
    
    # Validator aktivieren
    from src.sql_validator import SQLValidator
    
    # Extrahiere Tabellennamen aus Schema
    table_names = [t["name"] for t in schema_data["schema"]["tables"]]
    
    validator = SQLValidator(
        schema=schema_data,
        allowed_tables=table_names
    )
    
    validation_passed, validation_message = validator.validate(sql_query)
    
    if not validation_passed:
        raise HTTPException(400, f"SQL validation failed: {validation_message}")
    
    # ... return response
```

**Akzeptanzkriterien**:
- ✅ Validator ist aktiv
- ✅ Ungültige Queries werden abgelehnt

---

#### **Buffer / Code-Reviews** [2,5h] - MO
- Code-Reviews für alle Tasks
- Bug-Fixes
- Vorbereitung für Review

---

### **Raed's Aufgaben** [4h]

#### **P0-08b: Schemas migrieren** [1h] - RAED
**Script anwenden**:

```bash
# 1. Dry-Run (zeigt was passiert)
python scripts/migrate_schemas_to_kpis.py raedmokdad

# 2. Live-Migration
python scripts/migrate_schemas_to_kpis.py raedmokdad --live

# 3. Validieren
# Streamlit öffnen → Schema laden → Query testen
```

**Akzeptanzkriterien**:
- ✅ Alle Schemas migriert
- ✅ Keine `metrics` mehr in S3
- ✅ Parser lädt korrekt

---

#### **Phase 1 Vorbereitung** [3h] - RAED
**Recherche für nächste Woche**:
- Zeitlogik-Patterns (YoY, MoM, QoQ)
- SQL-Patterns für Trends ("steigt/sinkt")
- Beispiele aus anderen Tools sammeln

---

### **BEIDE: End-of-Week Review** [2h]

#### **P0-16: Live-Test & Review** [2h] - BEIDE

**Test-Szenario**:

1. **User 1: raedmokdad**
   ```
   - Login in Streamlit
   - Schema-Liste laden → retial_star_schema sichtbar?
   - Query stellen: "Umsatz pro Region 2024"
   - SQL generiert? Korrekt?
   - Validator aktiv? (Test mit ungültiger Query)
   ```

2. **User 2: demo_user** (falls vorhanden)
   ```
   - Login
   - Sieht NICHT raedmokdad's Schemas? ✅ Isolation
   - Eigenes Schema hochladen
   - Query testen
   ```

3. **Schema-Builder Test**
   ```
   - Neues Schema erstellen
   - KPI hinzufügen (nicht metrics!)
   - Upload nach S3
   - In Talk2Data laden
   - Query mit neuem KPI
   ```

**Checkliste**:
- [ ] Multi-Tenant funktioniert (User sehen nur eigene Schemas)
- [ ] S3-Schemas werden geladen (nicht lokale Files)
- [ ] SchemaParser verarbeitet S3-Dictionaries
- [ ] Schema-Builder schreibt `kpis`
- [ ] SQL-Validator ist aktiv
- [ ] Validator erlaubt JOINs, blockt Unsinn
- [ ] Business-KPIs (Profit, Marge) im Schema
- [ ] Username konsistent in allen Komponenten

**Deliverable**: ✅ oder ❌ für jeden Punkt + Notizen für Bugs

---

## 📊 Zusammenfassung Phase 0

### **Mo's Deliverables** (33h)
- ✅ API nutzt Username + S3-Schemas
- ✅ SchemaParser unterstützt S3-Dictionaries
- ✅ Streamlit nutzt konsistenten Username (beide Apps)
- ✅ Schema-Builder schreibt `kpis`
- ✅ Parser liest `kpis` (mit Fallback)
- ✅ Migrations-Script funktioniert
- ✅ SQL-Validator für Multi-Table angepasst
- ✅ Validator-Tests geschrieben
- ✅ Validator in API reaktiviert

### **Raed's Deliverables** (13h)
- ✅ Username-Strategie dokumentiert
- ✅ Business-KPIs erweitert (Profit, Marge, Growth)
- ✅ Glossary erweitert (7+ Einträge)
- ✅ 15-20 Test-Szenarien definiert
- ✅ Schemas migriert (metrics → kpis)
- ✅ Phase 1 vorbereitet

### **Gemeinsam**
- ✅ End-to-End Test erfolgreich
- ✅ System ist Multi-Tenant-ready
- ✅ Validator aktiv + sicher
- ✅ Schema-Format konsistent

---

## 🚀 Nächste Woche: Phase 1

**Fokus**: Zeit & Trends
- Periodenlogik ("letztes Jahr", "Q1 2024")
- YoY/MoM/QoQ Vergleiche
- Zeitvergleichs-SQL-Patterns
- KPI-Resolver (User-Text → KPI-Formel)
- Prompt-Engineering (KPIs explizit nutzen)

**Start**: Montag, 2. Dezember 2025

---

## 📝 Daily Standups

**Format** (10-15 Min täglich um 9:00):
1. Was habe ich gestern gemacht?
2. Was mache ich heute?
3. Gibt es Blocker?

**Communication**:
- Slack/Teams für schnelle Fragen
- GitHub Issues für Bugs
- End-of-Day: Kurzes Update im Chat

---

## ⏰ Zeittracking

| Tag | Raed (4h) | Mo (7,5h) | Tasks | Total |
|-----|-----------|-----------|-------|-------|
| **Mo** | 4h | 5,5h | Kickoff + Username + Start | 9,5h |
| **Di** | 4h | 7,5h | Multi-Tenant Core | 11,5h |
| **Mi** | 4h | 7,5h | Streamlit Integration | 11,5h |
| **Do** | 4h | 7,5h | SQL Validator | 11,5h |
| **Fr** | 4h | 7,5h | Migration + Review | 11,5h |
| **Total** | **20h** | **35,5h** | | **55,5h** |

**Puffer**: 4,5h eingebaut für unerwartete Probleme

---

**🎉 Los geht's! Montag 9:00 Uhr Kickoff-Call!** 🚀
