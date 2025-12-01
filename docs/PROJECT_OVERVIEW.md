# Talk2Data - Project Overview

## 🎯 Vision
Talk2Data ist ein KI-gestütztes Natural Language to SQL System, das es Business-Usern ermöglicht, Datenanalysen durch einfache Fragen in natürlicher Sprache durchzuführen - ohne SQL-Kenntnisse.

## 📊 Was macht Talk2Data?

**Problem:** Business-Analysten benötigen SQL-Kenntnisse oder Data-Team-Support für Datenabfragen.

**Lösung:** 
- User stellt Frage auf Deutsch/Englisch: *"Zeige Umsatz nach Store im Januar 2024"*
- KI generiert automatisch: `SELECT store_name, SUM(sales) FROM ... WHERE date >= '2024-01-01'`
- System führt Query aus und visualisiert Ergebnisse

## 🏗️ Architektur

```
┌─────────────────┐
│  Streamlit UI   │ ← User Interface (Login, Fragen stellen, Schemas verwalten)
└────────┬────────┘
         │
         │ HTTPS + JWT
         ▼
┌─────────────────┐
│   FastAPI       │ ← REST API Backend
│   /generate-sql │ ← SQL Generation Endpoint
│   /execute-sql  │ ← Query Execution (geplant von Mo)
└────────┬────────┘
         │
    ┌────┴─────┬─────────┬──────────┐
    ▼          ▼         ▼          ▼
┌────────┐ ┌─────┐  ┌──────┐  ┌────────┐
│ OpenAI │ │ AWS │  │  AWS │  │   DB   │
│GPT-4o  │ │ S3  │  │Cognito│ │Connector│
│  mini  │ │     │  │       │ │(Mo's)  │
└────────┘ └─────┘  └──────┘  └────────┘
```

## ✨ Features

### 1. Multi-Table SQL Generation (90% komplett)
- **LLM Table Selection:** KI wählt relevante Tabellen basierend auf Frage
- **Algorithmische JOINs:** System generiert automatisch korrekte JOIN-Pfade
- **Star Schema Support:** Optimiert für Fact + Dimension Tables
- **Date Intelligence:** Erkennt "Januar 2024" und konvertiert zu ISO-Format

**Beispiel:**
```
Frage: "Umsatz nach Store und Produkt"
→ Wählt: fact_sales, dim_store, dim_product
→ Generiert JOINs automatisch
→ Erstellt SQL: SELECT store_name, product_name, SUM(sales) FROM fact_sales LEFT JOIN ...
```

### 2. Multi-Tenant Architecture (100% komplett)
- **User Isolation:** Jeder User hat eigene Schemas in S3
- **JWT Authentication:** AWS Cognito basierte Authentifizierung
- **Username Normalization:** Email → Prefix Extraktion für S3-Pfade
- **S3 Storage:** `s3://bucket/schemas/{username}/{schema_name}.json`

### 3. Security Validator (100% komplett)
- **SQL Injection Protection:** Blockiert `OR 1=1`, `UNION SELECT`, etc.
- **Destructive Command Prevention:** Keine `DROP`, `DELETE`, `INSERT`
- **Comment Detection:** Blockiert `--` und `/* */` Patterns
- **Function Whitelist:** Nur erlaubte Aggregationen (SUM, AVG, COUNT...)

### 4. Schema Management (90% komplett)
- **Visual Schema Builder:** Streamlit UI zum Erstellen von Star Schemas
- **S3 CRUD Operations:** Create, Read, Update, Delete Schemas
- **Schema Validation:** Prüft Format und Struktur
- **Local Fallback:** Nutzt lokale Schemas wenn S3 nicht verfügbar

### 5. Database Connectors (20% komplett - Mo's Task)
- **PostgreSQL Connector:** Geplant von Mo
- **MySQL Connector:** Geplant von Mo
- **Result Visualization:** Charts und Tabellen (geplant von Mo)
- **/execute-sql Endpoint:** Query Ausführung (geplant von Mo)

## 🔄 User Flow

### Flow 1: SQL Generieren
```
1. User meldet sich an (Cognito)
   ↓
2. Wählt Schema aus (von S3 oder lokal)
   ↓
3. Stellt Frage: "Zeige Top 5 Stores"
   ↓
4. System extrahiert Username aus JWT Token
   ↓
5. Lädt User's Schema von S3
   ↓
6. LLM wählt relevante Tabellen (fact_sales, dim_store)
   ↓
7. Algorithmus generiert JOINs
   ↓
8. LLM erstellt finalen SQL Query
   ↓
9. Security Validator prüft SQL
   ↓
10. SQL wird zurückgegeben (+ Confidence Score)
```

### Flow 2: Schema Erstellen
```
1. User öffnet Schema Builder
   ↓
2. Definiert Fact Table (z.B. fact_sales)
   ↓
3. Definiert Dimension Tables (dim_store, dim_product)
   ↓
4. Definiert Relationships (store_id, product_id)
   ↓
5. Definiert KPIs (Umsatz, Gewinn, Marge)
   ↓
6. Speichert Schema zu S3: schemas/{username}/my_schema.json
```

## 🧩 Technologie Stack

### Backend
- **FastAPI:** REST API Framework
- **OpenAI GPT-4o-mini:** LLM für Table Selection & SQL Generation
- **Pydantic:** Data Validation
- **Boto3:** AWS SDK (S3, Cognito)
- **PyJWT:** Token Verification

### Frontend
- **Streamlit:** Web UI Framework
- **Requests:** HTTP Client für API Calls

### Infrastructure
- **Railway:** Cloud Hosting Platform
- **AWS S3:** Schema Storage
- **AWS Cognito:** User Management & Authentication
- **Docker:** Containerization

### Database (Mo's Part)
- **PostgreSQL:** Primary Database (geplant)
- **MySQL:** Alternative Database (geplant)
- **SQLAlchemy:** ORM Layer (geplant)

## 📁 Projekt Struktur

```
talk2data/
├── api_service.py              # FastAPI Backend (100% komplett)
├── streamlit_app_auth.py       # Streamlit UI mit Auth (100% komplett)
├── streamlit_schema_builder.py # Schema Builder UI (90% komplett)
├── auth_service.py             # Cognito Integration (100% komplett)
│
├── src/
│   ├── llm_sql_generator.py    # SQL Generation Engine (95% komplett)
│   ├── schema_parser.py        # Schema Parser + JOIN Engine (100% komplett)
│   ├── llm_table_selector.py  # Table Selection LLM (100% komplett)
│   ├── sql_validator.py        # Security Validator (100% komplett)
│   ├── s3_service.py           # S3 CRUD Operations (100% komplett)
│   ├── date_converter.py       # Date Intelligence (100% komplett)
│   ├── mapping.py              # KPI Mappings (80% komplett)
│   │
│   ├── config/                 # Lokale Schema Dateien
│   │   ├── retial_star_schema.json  # Main Test Schema
│   │   ├── rossman_schema.json      # Legacy Schema
│   │   └── ...
│   │
│   └── db_connector.py         # Database Connector (0% - Mo's Task)
│       postgres_connector.py   # PostgreSQL (0% - Mo's Task)
│       mysql_connector.py      # MySQL (0% - Mo's Task)
│
├── prompts/                    # LLM Prompt Templates
│   ├── sql_generator_system.txt
│   ├── sql_generator_user.txt
│   ├── table_selector.txt
│   └── ...
│
├── docs/                       # Diese Dokumentation
│   ├── PROJECT_OVERVIEW.md
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── API_DOCUMENTATION.md
│   └── DEPLOYMENT_GUIDE.md
│
├── Dockerfile                  # API Container
├── Dockerfile.streamlit        # Streamlit Container
├── requirements.txt            # Python Dependencies
└── .env                        # Environment Variables
```

## 👥 Team & Verantwortlichkeiten

### Raed's Arbeit (80% des Projekts)
✅ **Komplett:**
- FastAPI Backend Architecture
- Multi-Table SQL Generation mit LLM
- Algorithmischer JOIN Generator
- AWS Cognito Authentication
- Multi-Tenant S3 Integration
- Security Validator
- Schema Parser & Management
- Date Converter
- Streamlit UI (Authentication, Schema Builder, Query Interface)
- Railway Deployment

⏳ **In Arbeit:**
- Business KPIs erweitern (Profit, Margin, Growth)
- Schema Format Konsistenz
- Test-Szenarien definieren

### Mo's Arbeit (20% des Projekts)
⏳ **Geplant:**
- Database Connectors (PostgreSQL, MySQL)
- `/execute-sql` Endpoint
- Result Visualization (Charts, Tabellen)
- Query Performance Monitoring
- Testing der Connectors

## 📊 Projektstatus

| Komponente | Status | Details |
|-----------|--------|---------|
| Multi-Table SQL | ✅ 95% | JOIN Generation funktioniert |
| Multi-Tenant | ✅ 100% | S3 + JWT komplett |
| Security | ✅ 100% | Validator aktiv |
| Schema Management | ✅ 90% | CRUD funktioniert |
| Authentication | ✅ 100% | Cognito integriert |
| Database Execution | ⏳ 0% | Mo's Task |
| Visualization | ⏳ 0% | Mo's Task |

**Gesamtfortschritt:** ~80% komplett

## 🎯 Nächste Schritte

### Phase 0 (aktuell - 1 Woche)
1. ✅ Multi-Tenant S3 aktivieren
2. ✅ SQL Validator aktivieren
3. ⏳ Business KPIs erweitern (Raed)
4. ⏳ Database Connectors implementieren (Mo)

### Phase 1 (Woche 2-3)
1. `/execute-sql` Endpoint (Mo)
2. Result Visualization (Mo)
3. Query History & Caching
4. Performance Optimization

### Phase 2 (Woche 4+)
1. Advanced KPIs (YoY, MoM Growth)
2. Multi-Database Support
3. Query Optimization Suggestions
4. Admin Dashboard

## 🚀 Live System

**API:** https://talk2data-production.up.railway.app
**Streamlit:** (wird noch deployed)

**Test Credentials:** (AWS Cognito)
- Username: `testuser`
- Password: [aus .env]

## 📝 Wichtige Entscheidungen

### Warum OpenAI statt lokales LLM?
- **Qualität:** GPT-4o-mini generiert sehr gute SQL Queries
- **Geschwindigkeit:** API ist schneller als lokale Modelle
- **Kosten:** ~$0.001 pro Query (sehr günstig)
- **Wartung:** Kein Model Training/Hosting nötig

### Warum Star Schema?
- **BI Standard:** Fact + Dimensions ist Industrie-Standard
- **JOIN Algorithmus:** Eindeutige Paths von Fact zu Dimensions
- **Performance:** Optimiert für analytische Queries
- **Verständlichkeit:** Business Users kennen die Struktur

### Warum Security Validator ohne Schema-Checks?
- **LLM Verantwortung:** LLM kennt Schema und wählt valide Tables/Columns
- **Security First:** Injection-Prevention ist kritischer
- **Flexibilität:** Funktioniert mit allen Schema-Formaten
- **Einfachheit:** Weniger false positives

## 📞 Kontakt

**Raed Mokdad**
- Email: raed.mokdad@example.com
- GitHub: raedmokdad/talk2data

**Mo** (Database Spezialist)
- Verantwortlich für: DB Connectors, Query Execution, Visualization
