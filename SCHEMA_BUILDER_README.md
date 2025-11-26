# Schema Builder Dashboard

Ein visuelles Tool zum Erstellen und Verwalten von Star-Schema-Definitionen für Talk2Data.

## Features

### 📊 **Tables Tab**
- Erstelle Fact- und Dimension-Tabellen
- Definiere Columns mit Datentypen und Beschreibungen
- Setze Primary Keys und Foreign Keys
- Lösche Tabellen und Spalten einfach

### 🔗 **Relationships Tab**
- Zeigt automatisch erkannte Beziehungen aus Foreign Keys
- Visualisiert die Verbindungen zwischen Tabellen

### 📈 **Metrics Tab**
- Definiere vordefinierte Berechnungen (z.B. `total_revenue`)
- Hinterlege SQL-Formeln und Keywords
- LLM nutzt diese Metriken für intelligentere Abfragen

### 💡 **Examples Tab**
- Füge Beispiel-SQL-Queries hinzu
- Hilft dem LLM, komplexe Muster zu verstehen
- Best Practices dokumentieren

### 📖 **Glossary Tab**
- Business-Begriffe definieren
- Einheitliches Verständnis der Terminologie
- Hilfreich für neue Teammitglieder

## Nutzung

### Starten
```bash
streamlit run streamlit_schema_builder.py --server.port 8502
```

Dashboard öffnet sich auf: http://localhost:8502

### Schema erstellen

#### Option 1: Von Template starten
1. Klicke auf **"📥 Load Retail Template"** in der Sidebar
2. Das vollständige Retail-Schema wird geladen
3. Passe es nach deinen Bedürfnissen an

#### Option 2: Neues Schema
1. Klicke auf **"🆕 New Empty Schema"**
2. Gehe zum **Tables Tab**
3. Füge Tabellen hinzu (Fact oder Dimension)
4. Definiere Spalten und Keys
5. Füge Metriken, Beispiele und Glossar hinzu

### Schema speichern

Das Dashboard bietet 3 Speicheroptionen:

#### 1. **💾 Lokal speichern**
- Speichert in `schemas/` Verzeichnis
- Format: `schemas/my_schema.json`
- Ideal für lokale Entwicklung

#### 2. **☁️ S3 Upload**
- Lädt direkt zu AWS S3 hoch
- Format: `s3://bucket/schemas/{username}/{schema_name}.json`
- Benötigt AWS-Credentials in `.env`:
  ```
  AWS_ACCESS_KEY_ID=your_key
  AWS_SECRET_ACCESS_KEY=your_secret
  S3_BUCKET=your_bucket_name
  AWS_DEFAULT_REGION=us-east-1
  ```

#### 3. **📥 Download JSON**
- Lädt JSON-Datei direkt im Browser herunter
- Kann dann manuell verschoben/hochgeladen werden

## Schema-Struktur

Das generierte JSON folgt diesem Format:

```json
{
  "schema": {
    "tables": [
      {
        "name": "fact_sales",
        "role": "fact",
        "grain": "one row per sale",
        "columns": {
          "sales_id": "BIGINT - Primary key",
          "amount": "DECIMAL(12,2) - Sales amount"
        },
        "primary_key": "sales_id",
        "foreign_keys": {
          "date_key": "dim_date.date_key"
        }
      }
    ],
    "relationships": [],
    "metrics": {
      "total_revenue": {
        "formula": "SUM(fact_sales.amount)",
        "description": "Total revenue",
        "required_tables": ["fact_sales"],
        "keywords": ["umsatz", "revenue"]
      }
    },
    "examples": [
      {
        "description": "Monthly sales",
        "pattern": "SELECT ... FROM ... WHERE ..."
      }
    ],
    "glossary": {
      "net_sales": "Sales after discounts"
    }
  }
}
```

## Best Practices

### Tables
- **Fact-Tabellen**: Immer Foreign Keys zu allen Dimensionen definieren
- **Primary Keys**: Eindeutige Spalten verwenden (z.B. `sales_id`, `date_key`)
- **Grain**: Klar beschreiben auf welcher Ebene die Daten gespeichert sind

### Columns
- **Format**: `DATATYPE - Description`
- **Beispiel**: `VARCHAR(50) - Customer name`
- Immer Datentyp und Beschreibung angeben

### Metrics
- Häufig verwendete Berechnungen definieren
- Keywords in Deutsch und Englisch hinterlegen
- Required Tables angeben für optimale Tabellen-Selektion

### Examples
- Mindestens 3-5 Beispiel-Queries pro Schema
- Verschiedene Komplexitätsstufen abdecken
- JOIN-Patterns dokumentieren

## Integration mit Talk2Data

Nach dem Erstellen/Hochladen:

1. **Lokales Schema verwenden**:
   ```python
   from src.schema_parser import SchemaParser
   parser = SchemaParser("my_schema")  # lädt aus src/config/
   ```

2. **S3 Schema verwenden**:
   ```python
   from src.s3_service import get_user_schema
   schema = get_user_schema("username", "my_schema")
   ```

3. **API verwenden**:
   ```bash
   curl -X POST http://localhost:8000/generate-sql \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Wie viel Umsatz im Januar?",
       "schema_name": "my_schema"
     }'
   ```

## Troubleshooting

### S3 Upload funktioniert nicht
- Prüfe `.env` Datei auf korrekte AWS-Credentials
- Stelle sicher, dass der S3-Bucket existiert
- Prüfe IAM-Berechtigungen (s3:PutObject erforderlich)

### Schema wird nicht geladen
- Prüfe JSON-Syntax (nutze JSON Preview Tab)
- Stelle sicher, dass alle Pflichtfelder vorhanden sind
- Datei muss in `src/config/` oder S3 liegen

### Foreign Keys werden nicht erkannt
- Format muss sein: `"fk_column": "target_table.target_column"`
- Beispiel: `"date_key": "dim_date.date_key"`
- Tabelle muss existieren

## Weitere Funktionen

- **JSON Preview**: Zeigt das komplette Schema-JSON
- **Auto-Save**: Session State behält Änderungen während der Bearbeitung
- **Validation**: Automatische Prüfung der Schema-Struktur
- **Template Loading**: Schnellstart mit Beispiel-Schema

## Nächste Schritte

Nach Schema-Erstellung:
1. Teste mit `test_schema_parser.py`
2. Generiere Embeddings mit `embedding_build.py`
3. Nutze in Streamlit App unter Port 8501
4. API-Integration unter Port 8000

## Support

Bei Fragen oder Problemen:
- Prüfe die Logs in der Konsole
- Validiere JSON-Struktur im Preview Tab
- Kontaktiere: r.mokdad@example.com
