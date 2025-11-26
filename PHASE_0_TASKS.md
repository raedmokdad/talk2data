# 🚀 Phase 0: Kritische Systemlücken (1 Woche)

**Ziel**: System ist Multi-Tenant-ready, sicher und konsistent

**Team-Kapazität**:
- **Raed**: 4h/Tag = 20h/Woche
- **Mo**: 7,5h/Tag = 37,5h/Woche
- **Total Phase 0**: 42h (perfekt für 1 Woche)

---

## 📅 Tag 1 (Montag) - Foundation Day

### 🔴 KRITISCH: Username-Strategie definieren
**Owner**: Raed + Mo (gemeinsam)  
**Zeit**: 2h (Morning Kick-off)  
**Status**: ☐ To Do

**Deliverables**:
1. **Entscheidung**: Welcher Username-Typ ist "Single Source of Truth"?
   - Option A: Cognito `cognito:username` (aus JWT)
   - Option B: Email Local-Part (`user@example.com` → `user`)
   - **Empfehlung**: Option A (Cognito Username) für Konsistenz

2. **S3-Pfad-Standard definieren**:
   ```
   s3://smart-forecast/schemas/{username}/{schema_name}.json
   ```
   - `{username}` = Cognito Username (z.B. "raedmokdad")

3. **Mapping dokumentieren** (1 Seite):
   - Cognito JWT → Username → S3-Pfad → Streamlit Session
   - Beispiel-Flow zeigen

**Akzeptanzkriterien**:
- ✅ Ein Dokument (USERNAME_STRATEGY.md) mit klarer Entscheidung
- ✅ Beide verstehen, wie Username in jedem System verwendet wird

---

### 📝 Task 0.1: Username-Strategie dokumentieren
**Owner**: Raed  
**Zeit**: 2h  
**Status**: ☐ To Do

**Details**:
1. Erstelle `docs/USERNAME_STRATEGY.md` mit:
   ```markdown
   # Username-Strategie
   
   ## Master Source
   - Cognito `cognito:username` ist Single Source of Truth
   
   ## Flow
   1. User logged in → JWT enthält `cognito:username`
   2. Streamlit liest aus JWT: `st.session_state.username`
   3. API `/generate-sql` nimmt `username` aus JWT Header
   4. S3-Service nutzt: `s3://smart-forecast/schemas/{username}/...`
   
   ## Beispiele
   - User: raedmokdad@example.com
   - Cognito Username: raedmokdad
   - S3-Pfad: s3://smart-forecast/schemas/raedmokdad/retial_star_schema.json
   ```

2. Beispiel-Testfälle für 2 User:
   - User 1: raedmokdad
   - User 2: demo_user

**Akzeptanzkriterien**:
- ✅ Dokument existiert in `docs/`
- ✅ Mo hat es gelesen und verstanden

---

## 📅 Tag 2-3 (Dienstag-Mittwoch) - Multi-Tenant S3 Integration

### 🔧 Task 0.2: API - Username-Parameter hinzufügen
**Owner**: Mo  
**Zeit**: 4h  
**Status**: ☐ To Do  
**Depends on**: Task 0.1

**Dateien**:
- `api_service.py`

**Änderungen**:
1. `QueryRequest` Pydantic Model erweitern:
   ```python
   class QueryRequest(BaseModel):
       question: str
       schema_name: Optional[str] = "retial_star_schema"
       username: Optional[str] = None  # NEU
   ```

2. `/generate-sql` Endpoint anpassen:
   ```python
   @app.post("/generate-sql")
   async def generate_sql(request: QueryRequest):
       # Username aus Request holen (später aus JWT)
       username = request.username if request.username else "demo_user"
       
       # Schema aus S3 laden statt lokaler File
       success, schema_data = get_user_schema(username, request.schema_name)
       if not success:
           raise HTTPException(404, f"Schema not found for user {username}")
       
       # SchemaParser mit Dictionary initialisieren (nicht Filename)
       sql_query = generate_multi_table_sql(
           user_question=request.question,
           schema_data=schema_data,  # NEU: Dictionary statt schema_name
           username=username
       )
   ```

3. JWT-Integration (später verfeinern):
   ```python
   # TODO für später: Username aus JWT Header extrahieren
   # auth_header = request.headers.get("Authorization")
   # username = extract_username_from_jwt(auth_header)
   ```

**Akzeptanzkriterien**:
- ✅ `/generate-sql` akzeptiert `username` Parameter
- ✅ Schema wird aus S3 geladen (nicht mehr lokaler File)
- ✅ Test mit 2 Usern funktioniert (raedmokdad, demo_user)

---

### 🔧 Task 0.3: SchemaParser - Dictionary aus S3 akzeptieren
**Owner**: Mo  
**Zeit**: 6h  
**Status**: ☐ To Do  
**Depends on**: Task 0.2

**Dateien**:
- `src/schema_parser.py`

**Änderungen**:

1. **Neuer Constructor mit Dictionary-Support**:
   ```python
   class SchemaParser:
       def __init__(self, schema_name: str = None, schema_data: Dict = None, username: str = None):
           self.schema_name = schema_name
           self.username = username
           self.schema_data = schema_data  # NEU: Kann direkt Dictionary sein
           # ... rest bleibt gleich
   ```

2. **load_star_schema() anpassen**:
   ```python
   def load_star_schema(self) -> Dict:
       # Fall 1: Schema-Data bereits vorhanden (aus S3)
       if self.schema_data is not None:
           self._parse_tables()
           self._parse_relationships()
           # ... rest der Parsing-Logik
           return self.schema_data
       
       # Fall 2: Lokale File (Fallback für Tests)
       if self.schema_name:
           script_dir = pathlib.Path(__file__).parent
           path = script_dir / "config" / f"{self.schema_name}.json"
           with open(path, "r", encoding="utf-8") as f:
               self.schema_data = json.loads(f.read())
               # ... rest bleibt gleich
   ```

3. **Singleton-Pattern anpassen für Multi-Tenant**:
   ```python
   _schema_parser_cache = {}  # NEU: Cache pro (user, schema)
   
   def get_schema_parser(schema_name: str = None, schema_data: Dict = None, username: str = None):
       # Cache-Key: (username, schema_name)
       cache_key = f"{username}:{schema_name}" if username and schema_name else schema_name
       
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

**Akzeptanzkriterien**:
- ✅ SchemaParser kann mit Dictionary initialisiert werden
- ✅ Cache funktioniert pro `(username, schema_name)`
- ✅ Alte Tests laufen weiterhin (lokale Files)

---

### 🔧 Task 0.4: llm_sql_generator - S3-Schema-Integration
**Owner**: Mo  
**Zeit**: 3h  
**Status**: ☐ To Do  
**Depends on**: Task 0.3

**Dateien**:
- `src/llm_sql_generator.py`

**Änderungen**:

```python
def generate_multi_table_sql(
    user_question: str, 
    schema_name: str = None,
    schema_data: Dict = None,  # NEU
    username: str = None,      # NEU
    validator=None
) -> str:
    # Date-Preprocessing
    processed_question = extract_and_convert_dates(user_question)
    
    # Schema laden
    parser = get_schema_parser(
        schema_name=schema_name,
        schema_data=schema_data,  # NEU: Dictionary aus S3
        username=username
    )
    
    # Rest bleibt gleich
    relevant_tables = parser.get_relevant_tables(processed_question)
    # ...
```

**Akzeptanzkriterien**:
- ✅ Funktion akzeptiert `schema_data` Dictionary
- ✅ End-to-End Test: User-Frage → S3-Schema → SQL
- ✅ Logging zeigt korrekten Username

---

### 🎨 Task 0.5: Streamlit - Konsistenten Username nutzen
**Owner**: Mo  
**Zeit**: 2h  
**Status**: ☐ To Do  
**Depends on**: Task 0.1

**Dateien**:
- `streamlit_app_auth.py`
- `streamlit_schema_builder.py`

**Änderungen**:

1. **streamlit_app_auth.py**:
   ```python
   # Nach Login:
   if success:
       st.session_state.authenticated = True
       st.session_state.user_tokens = result['tokens']
       st.session_state.username = result['username']  # Cognito Username
       st.session_state.user_email = result.get('email', '')
   
   # API-Calls:
   response = requests.post(
       f"{API_URL}/generate-sql",
       json={
           "question": user_question,
           "schema_name": selected_schema,
           "username": st.session_state.username  # NEU: Cognito Username
       }
   )
   ```

2. **streamlit_schema_builder.py**:
   ```python
   # Nicht mehr hardcoded "raedmokdad"
   username = st.session_state.get('username', 'demo_user')
   
   # Upload to S3:
   success, message = upload_user_schema(
       username,  # Aus Session State
       schema_name,
       schema_data
   )
   ```

**Akzeptanzkriterien**:
- ✅ Kein hardcoded Username mehr
- ✅ `st.session_state.username` wird konsistent genutzt
- ✅ Schema-Upload landet im richtigen S3-Pfad

---

## 📅 Tag 4 (Donnerstag) - SQL-Validator für Multi-Table

### 🔧 Task 0.6: SQL-Validator anpassen
**Owner**: Mo  
**Zeit**: 7,5h  
**Status**: ☐ To Do

**Dateien**:
- `src/sql_validator.py`

**Änderungen**:

1. **Constructor für Multi-Table**:
   ```python
   class SQLValidator:
       def __init__(self, schema: Dict = None, allowed_tables: List[str] = None):
           self.schema = schema
           self.allowed_tables = allowed_tables or []
           
           # Wenn Schema vorhanden, extrahiere alle Tabellen + Spalten
           if schema:
               self.table_columns = self._extract_table_columns(schema)
           
           # JOINS erlauben, aber nur definierte Tabellen
           self.pattern_labels = {
               # ... bestehende Patterns
               # JOIN-Pattern ENTFERNEN (nicht mehr blocken)
           }
   
       def _extract_table_columns(self, schema: Dict) -> Dict[str, Set[str]]:
           """Extrahiert alle erlaubten Tabellen und Spalten aus Schema"""
           result = {}
           for table in schema.get('schema', {}).get('tables', []):
               table_name = table['name']
               columns = set(table.get('columns', {}).keys())
               result[table_name] = columns
           return result
   ```

2. **Neue Validierung: Tabellen-Whitelist**:
   ```python
   def _check_table_whitelist(self, sql: str):
       """Prüft, ob alle genutzten Tabellen erlaubt sind"""
       # Regex: Finde alle FROM/JOIN ... table_name
       tables_in_query = re.findall(
           r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
           sql,
           re.IGNORECASE
       )
       
       for table in tables_in_query:
           if table not in self.allowed_tables:
               return False, f"Unknown table: {table}", table
       
       return True, "OK", None
   ```

3. **Neue Validierung: Spalten-Check**:
   ```python
   def _check_columns(self, sql: str):
       """Prüft, ob alle Spalten in den jeweiligen Tabellen existieren"""
       # Regex: Finde alle table.column oder column Referenzen
       # ... (komplexe Logik, kann vereinfacht werden)
       
       return True, "OK", None
   ```

4. **validate() anpassen**:
   ```python
   def validate(self, sql: str):
       checks = [
           self._check_forbidden_commands,
           self._check_dangerous_pattern,
           self._check_table_whitelist,  # NEU
           # self._check_columns,  # Optional
           self._check_limit,
           # self._check_functions,  # Eventuell lockern
       ]
       
       for check in checks:
           passed, message, _ = check(sql)
           if not passed:
               return passed, message
       
       return True, "OK"
   ```

**Akzeptanzkriterien**:
- ✅ JOINs zwischen erlaubten Tabellen sind OK
- ✅ Unbekannte Tabellen werden abgelehnt
- ✅ Destruktive Commands (DROP, DELETE) werden weiterhin geblockt
- ✅ Tests: 5 positive Cases, 5 negative Cases

---

### 📝 Task 0.7: Tests für SQL-Validator schreiben
**Owner**: Raed  
**Zeit**: 4h  
**Status**: ☐ To Do  
**Depends on**: Task 0.6

**Dateien**:
- `test_sql_validator_multitable.py` (NEU)

**Test-Cases**:

1. **Positive Cases (sollten durchgehen)**:
   ```python
   def test_valid_multi_table_query():
       sql = """
       SELECT f.sales_amount, d.date, s.store_name
       FROM fact_sales f
       JOIN dim_date d ON f.date_key = d.date_key
       JOIN dim_store s ON f.store_key = s.store_key
       WHERE d.year = 2024
       LIMIT 100
       """
       # Sollte valid sein
   
   def test_valid_aggregation():
       sql = """
       SELECT s.region, SUM(f.sales_amount) as revenue
       FROM fact_sales f
       JOIN dim_store s ON f.store_key = s.store_key
       GROUP BY s.region
       LIMIT 100
       """
       # Sollte valid sein
   ```

2. **Negative Cases (sollten abgelehnt werden)**:
   ```python
   def test_reject_unknown_table():
       sql = "SELECT * FROM evil_table LIMIT 100"
       # Sollte rejected werden
   
   def test_reject_drop_command():
       sql = "DROP TABLE fact_sales"
       # Sollte rejected werden
   
   def test_reject_delete():
       sql = "DELETE FROM fact_sales WHERE 1=1"
       # Sollte rejected werden
   ```

**Akzeptanzkriterien**:
- ✅ Alle 10 Tests laufen durch
- ✅ Validator ist aktiviert in `/generate-sql`

---

## 📅 Tag 5 (Freitag) - Schema-Format Vereinheitlichung

### 🔧 Task 0.8: Schema-Builder auf `kpis` umstellen
**Owner**: Mo  
**Zeit**: 5h  
**Status**: ☐ To Do

**Dateien**:
- `streamlit_schema_builder.py`

**Änderungen**:

1. **Initialisierung**:
   ```python
   # VORHER: "metrics": {}
   # NACHHER: "kpis": {}
   
   if 'builder_schema' not in st.session_state:
       st.session_state.builder_schema = {
           "schema": {
               "tables": [],
               "relationships": []
           },
           "synonyms": {},
           "kpis": {},  # GEÄNDERT von "metrics"
           "examples": [],
           "glossary": {}
       }
   ```

2. **Tab "Metrics" umbenennen**:
   ```python
   # Tab-Label ändern
   tabs = st.tabs(["📋 Tables", "🔗 Relationships", "📈 KPIs", "💡 Examples", "💾 Save & Download"])
   
   # In Tab 3:
   with tabs[2]:
       st.header("📈 Business KPIs")
       
       # Add KPI Form
       with st.expander("➕ Add New KPI"):
           kpi_name = st.text_input("KPI Name", key="kpi_name")
           kpi_formula = st.text_area("Formula", key="kpi_formula")
           # ...
           
           if st.button("Add KPI"):
               st.session_state.builder_schema["kpis"][kpi_name] = {
                   "formula": kpi_formula,
                   # ...
               }
   ```

3. **Alle `metrics` Referenzen ersetzen**:
   ```bash
   # Suche in streamlit_schema_builder.py:
   # ["schema"]["metrics"] → ["kpis"]
   # .get("metrics", {}) → .get("kpis", {})
   ```

**Akzeptanzkriterien**:
- ✅ Builder schreibt `kpis` (nicht mehr `metrics`)
- ✅ Bestehende Schemas werden korrekt geladen
- ✅ Upload nach S3 funktioniert

---

### 🔧 Task 0.9: SchemaParser `kpis` vs `metrics` Fallback
**Owner**: Mo  
**Zeit**: 2,5h  
**Status**: ☐ To Do  
**Depends on**: Task 0.8

**Dateien**:
- `src/schema_parser.py`

**Änderungen**:

```python
def _parse_kpis(self):
    """Parse KPIs - mit Fallback für alte 'metrics' Struktur"""
    
    # Primär: Root-Level "kpis"
    if "kpis" in self.schema_data:
        self.kpis = self.schema_data["kpis"]
    
    # Fallback 1: Schema-Level "kpis"
    elif "kpis" in self.schema_data.get("schema", {}):
        self.kpis = self.schema_data["schema"]["kpis"]
    
    # Fallback 2: Alte "metrics" Struktur (für Migration)
    elif "metrics" in self.schema_data.get("schema", {}):
        logger.warning("Old 'metrics' format detected, consider migrating to 'kpis'")
        self.kpis = self.schema_data["schema"]["metrics"]
    
    else:
        self.kpis = {}
    
    logger.info(f"Loaded {len(self.kpis)} KPIs")
```

**Akzeptanzkriterien**:
- ✅ Parser liest sowohl `kpis` als auch alte `metrics`
- ✅ Warning im Log bei alter Struktur
- ✅ Alle Tests laufen weiterhin

---

### 📝 Task 0.10: S3-Schemas migrieren (optional)
**Owner**: Raed  
**Zeit**: 2h  
**Status**: ☐ To Do (Optional)

**Details**:
1. Bestehende S3-Schemas prüfen:
   ```
   s3://smart-forecast/schemas/raedmokdad/
     - ecommerce_schema.json
     - employee_schema.json
     - retial_star_schema.json
     - rossman_schema.json
     - sales_analitics_schema.json
   ```

2. Falls `metrics` vorhanden → umbenennen zu `kpis`

3. Script (optional):
   ```python
   # migrate_schemas.py
   for schema in list_user_schema("raedmokdad"):
       success, data = get_user_schema("raedmokdad", schema)
       if "metrics" in data.get("schema", {}):
           data["kpis"] = data["schema"].pop("metrics")
           upload_user_schema("raedmokdad", schema, data)
   ```

**Akzeptanzkriterien**:
- ✅ Alle Schemas nutzen `kpis`
- ✅ Keine `metrics` mehr in S3

---

## 📅 Ende Woche 1 - Integration & Testing

### 🧪 Task 0.11: End-to-End Tests für Multi-Tenant
**Owner**: Raed  
**Zeit**: 4h  
**Status**: ☐ To Do  
**Depends on**: Alle vorherigen Tasks

**Test-Szenarien**:

1. **User 1: raedmokdad**
   - Login → Schema aus S3 laden → Query stellen → SQL generieren
   - Upload neues Schema → Query mit neuem Schema

2. **User 2: demo_user**
   - Login → Schema aus S3 laden → Query stellen
   - Sollte NICHT auf raedmokdad's Schemas zugreifen können

3. **SQL-Validierung**:
   - 15-20 Test-Queries (aus Task 0.1 Liste)
   - Positive: Valid JOINs, Aggregationen, Zeitfilter
   - Negative: Unbekannte Tabellen, DELETE, DROP

**Test-Dokumentation**:
```markdown
# End-to-End Test Report

## Test 1: Multi-Tenant Isolation
- User: raedmokdad
- Schema: retial_star_schema
- Query: "Umsatz pro Region im Januar 2024"
- Result: ✅ SQL generiert, korrektes Schema geladen

## Test 2: SQL Validation
- Query: "DELETE FROM fact_sales"
- Result: ✅ Rejected (Forbidden command)

...
```

**Akzeptanzkriterien**:
- ✅ Alle 15-20 Queries funktionieren
- ✅ Multi-Tenant Isolation bestätigt
- ✅ SQL-Validator aktiv und funktionsfähig

---

### 📝 Task 0.12: Business-Logik erweitern (KPIs)
**Owner**: Raed  
**Zeit**: 4h  
**Status**: ☐ To Do

**Dateien**:
- `src/config/retial_star_schema.json`

**Neue KPIs hinzufügen**:

```json
{
  "kpis": {
    // ... bestehende KPIs
    
    "profit": {
      "formula": "SUM(fact_sales.sales_amount - fact_sales.discount_amount) - SUM(fact_sales.cost_amount)",
      "description": "Total profit (revenue minus costs)",
      "required_tables": ["fact_sales"],
      "keywords": ["gewinn", "profit", "ertrag"]
    },
    
    "profit_margin": {
      "formula": "(SUM(fact_sales.sales_amount - fact_sales.discount_amount) - SUM(fact_sales.cost_amount)) / NULLIF(SUM(fact_sales.sales_amount - fact_sales.discount_amount), 0)",
      "description": "Profit margin as percentage of net sales",
      "required_tables": ["fact_sales"],
      "keywords": ["marge", "gewinnspanne", "profitabilität"]
    },
    
    "loss": {
      "formula": "SUM(CASE WHEN fact_sales.sales_amount < 0 THEN ABS(fact_sales.sales_amount) ELSE 0 END)",
      "description": "Total losses from negative sales",
      "required_tables": ["fact_sales"],
      "keywords": ["verlust", "minus", "negativ"]
    }
  }
}
```

**Glossary erweitern**:
```json
{
  "glossary": {
    // ... bestehende Einträge
    
    "profit": "Gewinn = Nettoumsatz minus Kosten. Zeigt die tatsächliche Rentabilität.",
    "profit_margin": "Gewinnspanne = Profit geteilt durch Nettoumsatz. Wird als Prozentsatz ausgedrückt.",
    "loss": "Verlust = Summe aller negativen Verkäufe (z.B. Retouren, Gutschriften)."
  }
}
```

**Akzeptanzkriterien**:
- ✅ 3 neue KPIs im Schema
- ✅ Glossary-Einträge vorhanden
- ✅ Test-Query: "Wie hoch ist die Gewinnmarge pro Region?" funktioniert

---

### 📋 Task 0.13: Test-Szenarien dokumentieren
**Owner**: Raed  
**Zeit**: 2h  
**Status**: ☐ To Do

**Erstelle**: `docs/TEST_SCENARIOS_PHASE_0.md`

**15-20 Business-Fragen mit erwarteter SQL**:

```markdown
# Test-Szenarien für Phase 0

## 1. Basic Aggregation
**Frage**: "Gesamtumsatz im Jahr 2024"
**Erwartete Tabellen**: fact_sales, dim_date
**Erwartete KPI**: gross_sales
**Erwartetes SQL-Pattern**:
```sql
SELECT SUM(f.sales_amount) as total_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.year = 2024
LIMIT 100
```

## 2. Multi-Dimension
**Frage**: "Umsatz pro Region und Produktkategorie"
**Erwartete Tabellen**: fact_sales, dim_store, dim_product
**Erwartete KPI**: gross_sales
...

## 3. Business KPI
**Frage**: "Gewinnmarge pro Filiale"
**Erwartete Tabellen**: fact_sales, dim_store
**Erwartete KPI**: profit_margin
...

... (15 weitere Szenarien)
```

**Akzeptanzkriterien**:
- ✅ 15-20 dokumentierte Szenarien
- ✅ Deckt ab: Aggregation, JOINs, KPIs, Zeitfilter
- ✅ Wird für Phase 1 als Basis genutzt

---

## 📊 Phase 0 Summary

### ✅ Deliverables

**Technisch (Mo)**:
- ✅ Multi-Tenant S3-Integration (Username-basiert)
- ✅ SchemaParser akzeptiert Dictionary aus S3
- ✅ SQL-Validator für Multi-Table angepasst
- ✅ Schema-Format vereinheitlicht (`kpis` statt `metrics`)
- ✅ Streamlit nutzt konsistenten Username

**Business (Raed)**:
- ✅ Username-Strategie dokumentiert
- ✅ 3 neue KPIs (Profit, Marge, Verlust)
- ✅ 15-20 Test-Szenarien definiert
- ✅ End-to-End Tests durchgeführt

### 🎯 Wochenziel erreicht:
**System ist Multi-Tenant-ready, sicher und konsistent!**

---

## 🚀 Nächste Schritte: Phase 1

**Start**: Montag nächste Woche  
**Fokus**: Zeitvergleiche (YoY/MoM/QoQ) + KPI-Integration in LLM-Prompts

**Preview Tasks**:
- Periodenlogik ("letztes Jahr", "Q1 2024")
- Zeitvergleichs-SQL-Patterns (CTEs, LAG/LEAD)
- KPI-Resolver (User-Text → KPI-Formel)
- Prompt-Engineering (KPIs explizit nutzen)

---

## 📝 Daily Standups

**Format** (15 Min täglich):
1. Was habe ich gestern gemacht?
2. Was mache ich heute?
3. Gibt es Blocker?

**Communication**:
- Slack/Teams für schnelle Fragen
- Code Reviews: Mo reviewed Raed's Tests, Raed reviewed Mo's Code
- End-of-Week: 1h Demo + Retrospektive

---

## ⏰ Zeittracking

| Tag | Raed (4h) | Mo (7,5h) | Total |
|-----|-----------|-----------|-------|
| Mo  | 2h (0.1)  | -         | 2h    |
| Di  | -         | 7,5h (0.2-0.5) | 7,5h |
| Mi  | -         | 7,5h (0.3-0.5) | 7,5h |
| Do  | 4h (0.7)  | 7,5h (0.6) | 11,5h |
| Fr  | 4h (0.10-0.13) | 7,5h (0.8-0.9) | 11,5h |
| **Total** | **10h** | **30h** | **40h** |

**Puffer**: 2h (für unerwartete Probleme)

---

**🎉 Los geht's! Viel Erfolg in Phase 0!**
