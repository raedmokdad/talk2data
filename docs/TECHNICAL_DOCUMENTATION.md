# Technical Documentation - Talk2Data

## 🏛️ System Architecture

### High-Level Design
```
User Request → JWT Auth → Schema Loading → Table Selection → JOIN Generation → SQL Generation → Validation → Response
```

### Component Interaction
```
┌────────────────────────────────────────────────────────────────┐
│                        FastAPI Layer                            │
│  api_service.py: REST Endpoints, Request Handling, Auth        │
└────────┬──────────────────────────────────────────────────────┘
         │
         ├──→ Authentication Layer
         │    ├── s3_service.get_current_user() → JWT Decode
         │    └── auth_service.py → Cognito Integration
         │
         ├──→ Schema Management Layer
         │    ├── s3_service.py → S3 CRUD (get/list/upload/delete)
         │    └── schema_parser.py → Parse & Validate Schemas
         │
         ├──→ SQL Generation Layer
         │    ├── llm_sql_generator.py → Orchestration
         │    ├── llm_table_selector.py → LLM picks tables
         │    ├── schema_parser.find_join_path() → Algorithm creates JOINs
         │    └── date_converter.py → Date preprocessing
         │
         └──→ Security Layer
              └── sql_validator.py → Injection protection
```

---

## 📦 Core Modules

### 1. `api_service.py` - FastAPI Backend

**Purpose:** REST API that handles all HTTP requests, authentication, and orchestrates SQL generation.

#### Key Endpoints

##### `POST /generate-sql`
**Function:**
```python
async def generate_sql(
    request: QueryRequest,
    current_user: str = Depends(get_current_user)
) -> QueryResponse
```

**Flow:**
1. Extract JWT token via `Depends(get_current_user)`
2. Extract username from token
3. Load user's schema from S3 via `get_user_schema(username, schema_name)`
4. Fallback to local schema if S3 fails
5. Call `generate_multi_table_sql(question, schema_data)`
6. Validate SQL with `SQLValidator().validate(sql)`
7. Return SQL + confidence + validation status

**Parameters:**
- `question`: str - Natural language question
- `schema_name`: Optional[str] - Schema to use (default: "retial_star_schema")
- `max_retries`: int - Not used yet
- `confidence_threshold`: float - Not used yet

**Response:**
```json
{
  "sql_query": "SELECT ...",
  "confidence": 0.95,
  "validation_passed": true,
  "processing_time": 1.23,
  "message": "SQL generated and validated successfully"
}
```

##### `GET /schemas/{username}`
Lists all schemas for a user from S3.

##### `GET /schemas/{username}/{schema_name}`
Retrieves specific schema JSON.

##### `POST /schemas/{username}/{schema_name}`
Creates new schema in S3.

##### `PUT /schemas/{username}/{schema_name}`
Updates existing schema.

##### `DELETE /schemas/{username}/{schema_name}`
Deletes schema from S3.

---

### 2. `src/schema_parser.py` - Schema Parsing & JOIN Engine

**Purpose:** Parses star schemas, manages table relationships, generates JOIN paths algorithmically.

#### Core Classes

##### `TableRelationship` (Dataclass)
Represents a relationship between two tables.

```python
@dataclass
class TableRelationship:
    from_table: str        # Source table (e.g., "fact_sales")
    from_column: str       # FK column (e.g., "store_id")
    to_table: str          # Target table (e.g., "dim_store")
    to_column: str         # PK column (e.g., "store_id")
    join_type: str = "LEFT JOIN"
    description: str = ""
    
    def to_sql_join(self) -> str:
        """Generates JOIN SQL: LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id"""
        return f"{self.join_type} {self.to_table} ON {self.from_table}.{self.from_column} = {self.to_table}.{self.to_column}"
```

##### `JoinPath` (Dataclass)
Represents a complete JOIN path through multiple tables.

```python
@dataclass
class JoinPath:
    tables: List[str]                         # ["fact_sales", "dim_store", "dim_product"]
    relationships: List[TableRelationship]    # List of JOINs
    total_cost: int = 0
    
    def to_sql(self) -> str:
        """Generates complete JOIN chain"""
        return "\n".join([rel.to_sql_join() for rel in self.relationships])
```

**Example Output:**
```sql
LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id
LEFT JOIN dim_product ON fact_sales.product_id = dim_product.product_id
```

##### `SchemaParser` (Main Class)

**Constructor:**
```python
def __init__(self, schema_name: str):
    self.schema_name = schema_name
    self.schema_data: Optional[Dict] = None
    self.relationships: List[TableRelationship] = []
    self.synonyms: Dict = {}
    self.kpis: Dict = {}
    self.tables: Dict = {}
    self.notes: List[str] = []
    self.examples: List[Dict] = []
    self.glossary: Dict = {}
```

**Key Methods:**

##### `load_star_schema() -> Dict`
Loads schema from `src/config/{schema_name}.json` and parses all components.

```python
def load_star_schema(self) -> Dict:
    path = pathlib.Path(__file__).parent / "config" / f"{self.schema_name}.json"
    with open(path, "r") as f:
        self.schema_data = json.loads(f.read())
    
    # Parse all components
    self._parse_tables()
    self._parse_relationships()
    self._parse_synonyms()
    self._parse_kpis()
    self._parse_notes()
    self._parse_examples()
    self._parse_glossary()
    
    return self.schema_data
```

##### `find_join_path(required_tables: List[str]) -> Optional[JoinPath]`
**THE CORE ALGORITHM:** Generates JOIN path from fact table to all required dimensions.

**Algorithm:**
```python
def find_join_path(self, required_tables: List[str]) -> Optional[JoinPath]:
    # 1. Find fact table (starts with "fact_" or has role="fact")
    fact_table = self._find_fact_table(required_tables)
    
    # 2. Initialize with fact table
    connected_tables = {fact_table}
    join_path = JoinPath(tables=[fact_table], relationships=[])
    
    # 3. Remaining tables to connect
    remaining_tables = [t for t in required_tables if t != fact_table]
    
    # 4. Iteratively find connections
    while remaining_tables:
        found_connection = False
        
        for target in remaining_tables:
            # Try to find relationship from any connected table to target
            rel = self._find_relationship(connected_tables, target)
            
            if rel:
                join_path.relationships.append(rel)
                join_path.tables.append(target)
                connected_tables.add(target)
                remaining_tables.remove(target)
                found_connection = True
                break
        
        # No connection found = orphaned table
        if not found_connection:
            return None
    
    return join_path
```

**Example:**
```python
required_tables = ["fact_sales", "dim_store", "dim_product"]

# Algorithm finds:
# Step 1: fact_sales → connected_tables = {fact_sales}
# Step 2: Find fact_sales → dim_store (via store_id)
# Step 3: Find fact_sales → dim_product (via product_id)
# 
# Result: JoinPath with 2 relationships
```

##### `get_relevant_tables(question: str) -> List[str]`
Uses LLM to identify which tables are needed for the question.

```python
def get_relevant_tables(self, question: str) -> List[str]:
    schema_summary = self.get_schema_summary()
    tables = select_tables(question, schema_summary)  # LLM call
    
    # Validate returned tables exist
    valid_tables = [t for t in tables if t in self.tables]
    
    if not valid_tables:
        logger.warning("LLM returned no valid tables, using all as fallback")
        return list(self.tables.keys())
    
    return valid_tables
```

##### `get_schema_summary() -> str`
Creates a concise schema description for LLM prompts.

```python
def get_schema_summary(self) -> str:
    summary = []
    for table_name, table_data in self.tables.items():
        role = table_data.get("role", "")
        grain = table_data.get("grain", "")
        columns = table_data.get("columns", {})
        
        summary.append(f"Table: {table_name} ({role})")
        summary.append(f"- Grain: {grain}")
        summary.append(f"- Columns: {', '.join(columns.keys())}\n")
    
    return "\n".join(summary)
```

**Output Example:**
```
Table: fact_sales (fact)
- Grain: One row per transaction
- Columns: sale_id, store_id, product_id, date_id, sales_amount, quantity

Table: dim_store (dimension)
- Grain: One row per store
- Columns: store_id, store_name, city, state, region
```

#### Global Functions

##### `get_schema_parser(schema_name: str) -> SchemaParser`
Singleton pattern - returns cached parser instance for local schemas.

```python
_schema_parser_instance = None

def get_schema_parser(schema_name: str = "retial_star_schema") -> SchemaParser:
    global _schema_parser_instance
    
    if _schema_parser_instance is None:
        _schema_parser_instance = SchemaParser(schema_name)
        _schema_parser_instance.load_star_schema()
    
    return _schema_parser_instance
```

##### `get_schema_parser_from_data(schema_data: Dict) -> SchemaParser`
Creates parser from dictionary (for S3-loaded schemas).

```python
def get_schema_parser_from_data(schema_data: Dict) -> SchemaParser:
    schema_name = schema_data.get("name", "user_schema")
    parser = SchemaParser(schema_name)
    parser.schema_data = schema_data
    
    # Parse all components
    parser._parse_tables()
    parser._parse_relationships()
    parser._parse_synonyms()
    parser._parse_kpis()
    parser._parse_notes()
    parser._parse_examples()
    parser._parse_glossary()
    
    return parser
```

---

### 3. `src/llm_sql_generator.py` - SQL Generation Engine

**Purpose:** Orchestrates the entire SQL generation process using LLM and algorithmic JOIN generation.

#### Main Function

##### `generate_multi_table_sql(user_question, schema_name=None, schema_data=None) -> str`

**Complete Flow:**

```python
def generate_multi_table_sql(
    user_question: str,
    schema_name: str = None,
    schema_data: Dict = None
) -> str:
    # Step 0: Preprocess dates
    # "Januar 2024" → "2024-01-01"
    processed_question = extract_and_convert_dates(user_question)
    
    # Step 1: Load schema
    if schema_data:
        parser = get_schema_parser_from_data(schema_data)  # From S3
    elif schema_name:
        parser = get_schema_parser(schema_name)  # From local file
    else:
        raise ValueError("Need either schema_data or schema_name")
    
    # Step 2: LLM selects relevant tables
    relevant_tables = parser.get_relevant_tables(processed_question)
    # e.g., ["fact_sales", "dim_store"]
    
    # Step 3: Algorithm generates JOIN path
    join_path = parser.find_join_path(relevant_tables)
    # Returns: JoinPath with relationships
    
    # Step 4: Build schema info for LLM
    tables_info = []
    for table_name in relevant_tables:
        table_data = parser.tables[table_name]
        columns = table_data.get("columns", {})
        
        col_descriptions = "\n".join([
            f"  - {col}: {desc}" 
            for col, desc in columns.items()
        ])
        
        tables_info.append(f"""
Table: {table_name}
- Grain: {table_data['grain']}
- Columns:
{col_descriptions}
        """)
    
    schema_info = "\n\n".join(tables_info)
    
    # Step 5: Build JOIN SQL
    join_sql = ""
    if join_path and join_path.relationships:
        join_sql = join_path.to_sql()
        # e.g., "LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id"
    
    # Step 6: Create LLM prompt
    system_prompt = f"""You are an expert SQL query generator.

Available Tables and Schema:
{schema_info}

JOIN Structure:
{join_sql if join_sql else "Single table query"}

Security Rules:
- FORBIDDEN commands: DROP, DELETE, INSERT, UPDATE, ...
- ALLOWED functions: SUM, AVG, COUNT, MIN, MAX, ...

Instructions:
1. Use the provided JOIN structure
2. Generate complete, valid SQL
3. Use only available columns
4. Return ONLY SQL, no explanations
"""
    
    user_prompt = f"Generate SQL for: {processed_question}"
    
    # Step 7: Call OpenAI
    response = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
        max_tokens=800
    )
    
    sql_query = response.choices[0].message.content.strip()
    
    # Step 8: Clean up formatting
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    
    return sql_query
```

**Key Insight:** The function combines:
- **LLM Intelligence:** For table selection and final SQL generation
- **Algorithmic Precision:** For JOIN generation (no hallucinations!)
- **Security Rules:** Embedded in LLM prompt

---

### 4. `src/llm_table_selector.py` - Table Selection

**Purpose:** Uses LLM to identify which tables are needed for a question.

```python
def select_tables(user_question: str, schema_summary: str) -> List[str]:
    """
    Asks LLM: "Which tables do you need for this question?"
    
    Args:
        user_question: "Show sales by store"
        schema_summary: """
            Table: fact_sales (fact)
            - Columns: sale_id, store_id, sales_amount
            
            Table: dim_store (dimension)
            - Columns: store_id, store_name, city
        """
    
    Returns:
        ["fact_sales", "dim_store"]
    """
    
    prompt = load_prompt("table_selector")  # From prompts/table_selector.txt
    
    prompt_filled = prompt.format(
        schema_summary=schema_summary,
        user_question=user_question
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_filled}],
        temperature=0
    )
    
    # Parse response: "fact_sales, dim_store"
    tables = response.choices[0].message.content.strip().split(",")
    return [t.strip() for t in tables]
```

---

### 5. `src/sql_validator.py` - Security Validator

**Purpose:** Validates generated SQL for security threats (not schema correctness).

#### Core Class

##### `SQLValidator`

```python
class SQLValidator:
    def __init__(self, schema: Dict = None):
        self.schema = schema  # Optional, not used for security checks
        
        # Dangerous patterns to detect
        self.pattern_labels = {
            r";\s*(DROP|DELETE|UPDATE|ALTER|INSERT)": 
                "Command chaining with destructive SQL",
            r"--": 
                "Inline SQL comment (possible injection)",
            r"\bUNION\s+SELECT\b": 
                "UNION-based SQL injection attempt",
            r"\bOR\s+1\s*=\s*1\b": 
                "Boolean-based SQL injection (OR 1=1)",
            # ... more patterns
        }
        
        self.forbidden_commands = [
            "INSERT", "UPDATE", "DELETE", "DROP", 
            "CREATE", "ALTER", "TRUNCATE", "MERGE", 
            "REPLACE", "EXEC", "CALL", "GRANT", "REVOKE"
        ]
        
        self.allowed_functions = [
            "SUM", "AVG", "COUNT", "MIN", "MAX",
            "DATE", "DATE_TRUNC", "COALESCE", "YEAR", "MONTH"
        ]
```

##### `validate(sql: str) -> Dict[str, Any]`

**Validation Flow:**

```python
def validate(self, sql: str) -> Dict[str, Any]:
    errors = []
    
    # Check 1: Forbidden commands
    if self._check_forbidden_commands(sql):
        errors.append("Security violation: DROP detected")
    
    # Check 2: Dangerous patterns
    if self._check_dangerous_pattern(sql):
        errors.append("Injection risk: OR 1=1 detected")
    
    # Check 3: Function whitelist
    if self._check_functions(sql):
        errors.append("Function restriction: EXEC() not allowed")
    
    # Check 4: Basic syntax
    if not sql.strip().upper().startswith("SELECT"):
        errors.append("Syntax error: Must start with SELECT")
    
    if errors:
        return {
            "ok": False,
            "error_message": "; ".join(errors),
            "sql": sql
        }
    
    return {"ok": True, "sql": sql}
```

**Example:**
```python
validator = SQLValidator()

# Good SQL
result = validator.validate("SELECT * FROM fact_sales LIMIT 10")
# → {"ok": True, "sql": "..."}

# Bad SQL (Injection)
result = validator.validate("SELECT * FROM fact_sales WHERE 1=1 OR 1=1")
# → {"ok": False, "error_message": "Injection risk: Boolean-based SQL injection (OR 1=1)"}

# Bad SQL (Destructive)
result = validator.validate("DROP TABLE fact_sales; SELECT * FROM fact_sales")
# → {"ok": False, "error_message": "Security violation: Forbidden SQL operation detected: DROP"}
```

---

### 6. `src/s3_service.py` - S3 & Authentication

**Purpose:** Manages S3 operations and JWT token validation.

#### Authentication

##### `get_current_user(credentials) -> str`

**Flow:**
```python
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    # Extract JWT token from Authorization header
    token = credentials.credentials
    
    # Decode without signature verification (for development)
    payload = jwt.decode(token, options={"verify_signature": False})
    
    # Get username from token
    username = payload.get("cognito:username") or payload.get("username")
    
    if not username:
        raise HTTPException(401, "Username not found in token")
    
    # Normalize username for S3
    # "raed.mokdad@example.com" → "raed_mokdad"
    if '@' in username:
        username = username.split('@')[0]
    
    username = username.lower().replace('.', '_')
    
    return username
```

**Why Normalization?**
- S3 keys don't like special characters
- Email addresses have `@` and `.`
- Convert `raed.mokdad@example.com` → `raed_mokdad`
- Consistent S3 paths: `schemas/raed_mokdad/my_schema.json`

#### S3 Operations

##### `get_user_schema(username: str, schema_name: str) -> tuple[bool, Dict]`

```python
def get_user_schema(username: str, schema_name: str) -> tuple[bool, Dict]:
    try:
        client = boto3.client('s3')
        
        # S3 path: schemas/{username}/{schema_name}.json
        response = client.get_object(
            Bucket="smart-forecast",
            Key=f"schemas/{username}/{schema_name}.json"
        )
        
        content = response['Body'].read().decode('utf-8')
        schema_data = json.loads(content)
        
        return True, schema_data
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False, {}
```

##### `upload_user_schema(username, schema_name, schema_data) -> tuple[bool, str]`

```python
def upload_user_schema(username: str, schema_name: str, schema_data: Dict) -> tuple[bool, str]:
    try:
        client = boto3.client('s3')
        
        key = f"schemas/{username}/{schema_name}.json"
        
        client.put_object(
            Bucket="smart-forecast",
            Key=key,
            Body=json.dumps(schema_data),
            ContentType="application/json"
        )
        
        return True, f"{schema_name} uploaded successfully"
    except Exception as e:
        return False, f"Upload failed: {str(e)}"
```

##### `list_user_schema(username: str) -> tuple[bool, List[str]]`

```python
def list_user_schema(username: str) -> tuple[bool, List[str]]:
    try:
        client = boto3.client('s3')
        
        response = client.list_objects_v2(
            Bucket="smart-forecast",
            Prefix=f"schemas/{username}/"
        )
        
        files = []
        if 'Contents' in response:
            files = [
                obj['Key'].split('/')[-1].replace('.json', '')
                for obj in response['Contents']
            ]
        
        return True, files
    except Exception as e:
        return False, []
```

---

### 7. `src/date_converter.py` - Date Intelligence

**Purpose:** Converts natural language dates to ISO format.

```python
def extract_and_convert_dates(user_question: str) -> str:
    """
    Converts date expressions to ISO format.
    
    Examples:
        "Januar 2024" → "2024-01-01"
        "Q2 2024" → "2024-04-01 to 2024-06-30"
        "last month" → "2024-10-01" (if current is Nov 2024)
    
    Args:
        user_question: "Zeige Umsatz im Januar 2024"
    
    Returns:
        "Zeige Umsatz between '2024-01-01' and '2024-01-31'"
    """
    
    # Regex patterns for different date formats
    patterns = {
        r'(\w+)\s+(\d{4})': convert_month_year,  # "Januar 2024"
        r'Q(\d)\s+(\d{4})': convert_quarter,      # "Q2 2024"
        r'(\d{4})': convert_year,                  # "2024"
        # ... more patterns
    }
    
    processed = user_question
    
    for pattern, converter in patterns.items():
        match = re.search(pattern, processed)
        if match:
            iso_date = converter(match.groups())
            processed = processed.replace(match.group(0), iso_date)
    
    return processed
```

---

## 🔄 Complete Request Flow

### Example: "Show total sales by store"

```
1. User → Streamlit UI
   Input: "Show total sales by store"
   Schema: "retial_star_schema"

2. Streamlit → FastAPI POST /generate-sql
   Headers: Authorization: Bearer <jwt_token>
   Body: {"question": "Show total sales by store", "schema_name": "retial_star_schema"}

3. FastAPI → JWT Validation
   get_current_user() decodes token
   → username = "raed_mokdad"

4. FastAPI → S3 Schema Loading
   get_user_schema("raed_mokdad", "retial_star_schema")
   → Tries S3: schemas/raed_mokdad/retial_star_schema.json
   → Not found, falls back to local: src/config/retial_star_schema.json

5. FastAPI → SQL Generation
   generate_multi_table_sql(question, schema_data)
   
   5a. Date Conversion
       extract_and_convert_dates("Show total sales by store")
       → No dates found, returns unchanged
   
   5b. Schema Parser Creation
       parser = get_schema_parser_from_data(schema_data)
       → Parses tables, relationships, KPIs
   
   5c. Table Selection (LLM)
       parser.get_relevant_tables("Show total sales by store")
       → LLM Call to GPT-4o-mini
       → Prompt: "Which tables needed? User asked: Show total sales by store"
       → Response: ["fact_sales", "dim_store"]
   
   5d. JOIN Generation (Algorithm)
       parser.find_join_path(["fact_sales", "dim_store"])
       → Algorithm finds: fact_sales.store_id → dim_store.store_id
       → Returns: JoinPath with 1 relationship
       → SQL: "LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id"
   
   5e. Build LLM Prompt
       schema_info = """
           Table: fact_sales (fact)
           - Grain: One row per transaction
           - Columns: sale_id, store_id, sales_amount, quantity
           
           Table: dim_store (dimension)
           - Grain: One row per store
           - Columns: store_id, store_name, city, state
       """
       
       join_sql = "LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id"
       
       system_prompt = f"You are SQL expert. Schema: {schema_info}. JOINs: {join_sql}"
       user_prompt = "Generate SQL for: Show total sales by store"
   
   5f. LLM SQL Generation
       → OpenAI GPT-4o-mini call
       → Response: """
           SELECT dim_store.store_name, SUM(fact_sales.sales_amount) as total_sales
           FROM fact_sales
           LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id
           GROUP BY dim_store.store_name
           ORDER BY total_sales DESC
       """

6. FastAPI → SQL Validation
   validator = SQLValidator()
   result = validator.validate(sql_query)
   
   Checks:
   ✅ No forbidden commands (DROP, DELETE)
   ✅ No injection patterns (OR 1=1, UNION)
   ✅ Functions allowed (SUM, GROUP BY)
   ✅ Starts with SELECT
   
   → result = {"ok": True, "sql": "..."}

7. FastAPI → Response
   return QueryResponse(
       sql_query="SELECT dim_store.store_name...",
       confidence=0.95,
       validation_passed=True,
       processing_time=1.23,
       message="SQL generated and validated successfully"
   )

8. Streamlit → Display
   Shows SQL in code block
   Shows confidence: 95%
   Shows validation: ✅ Passed
```

---

## 🧪 Testing

### Unit Test Examples

```python
# Test Schema Parser
def test_join_path_generation():
    parser = SchemaParser("retial_star_schema")
    parser.load_star_schema()
    
    tables = ["fact_sales", "dim_store", "dim_product"]
    join_path = parser.find_join_path(tables)
    
    assert join_path is not None
    assert len(join_path.relationships) == 2
    assert "dim_store" in join_path.tables
    assert "dim_product" in join_path.tables

# Test SQL Validator
def test_sql_injection_detection():
    validator = SQLValidator()
    
    sql = "SELECT * FROM fact_sales WHERE 1=1 OR 1=1"
    result = validator.validate(sql)
    
    assert result["ok"] == False
    assert "Injection risk" in result["error_message"]

# Test Date Converter
def test_date_conversion():
    question = "Zeige Umsatz im Januar 2024"
    result = extract_and_convert_dates(question)
    
    assert "2024-01-01" in result
    assert "2024-01-31" in result
```

---

## 📊 Performance Characteristics

### Timing Breakdown (Typical Request)

| Step | Duration | Details |
|------|----------|---------|
| JWT Decode | ~5ms | Fast, no signature verification |
| S3 Schema Load | ~100-200ms | Network call, or 0ms if fallback |
| Table Selection (LLM) | ~500-800ms | OpenAI API call |
| JOIN Generation | ~1-5ms | Pure algorithm, very fast |
| SQL Generation (LLM) | ~800-1200ms | OpenAI API call |
| SQL Validation | ~1-2ms | Regex matching |
| **Total** | **~1.5-2.5s** | End-to-end |

### Optimization Opportunities

1. **Cache Schema Parser:** ✅ Already done via singleton
2. **Cache Table Selection:** Could cache for same question
3. **Parallel LLM Calls:** Table selection + SQL generation could be combined
4. **S3 Caching:** Could cache schemas in memory (Redis)

---

## 🔒 Security Considerations

### 1. JWT Token Handling
- **Current:** No signature verification (`verify_signature=False`)
- **Risk:** Tokens could be forged
- **Mitigation:** Should verify signature in production with Cognito public key

### 2. SQL Injection
- **Protection:** Multi-layered
  1. LLM instructed to avoid injection patterns
  2. Validator checks for known patterns
  3. Query will be executed with parameterized queries (Mo's task)

### 3. S3 Access Control
- **Current:** IAM credentials in .env
- **Risk:** If credentials leak, full S3 access
- **Mitigation:** Use IAM roles with least privilege

### 4. Schema Isolation
- **Protection:** S3 paths enforce user isolation
- **Format:** `schemas/{username}/...`
- **Risk:** Username normalization must be consistent

---

## 🚀 Deployment Architecture

### Railway Deployment

```
GitHub (main branch)
    ↓ (auto-deploy on push)
Railway
    ├── Build: docker build -f Dockerfile
    ├── Environment Variables from Railway settings
    └── Run: uvicorn api_service:app --host 0.0.0.0 --port $PORT
```

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=smart-forecast

# Cognito
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_...
COGNITO_APP_CLIENT_ID=...
COGNITO_APP_CLIENT_SECRET=...

# Railway
PORT=8000  # Set by Railway
```

---

## 📈 Future Enhancements

### Code Improvements

1. **Async S3 Operations:** Use aioboto3 for async S3 calls
2. **LLM Response Caching:** Cache identical questions
3. **Schema Versioning:** Track schema changes over time
4. **Query History:** Store and analyze user queries
5. **A/B Testing:** Test different prompts for quality

### Feature Additions

1. **Query Optimization:** Suggest indexes, better queries
2. **Natural Language Explanations:** Explain what SQL does
3. **Query Building UI:** Visual query builder
4. **Collaborative Schemas:** Share schemas between users
5. **Advanced KPIs:** YoY growth, rolling averages

---

## 🐛 Known Issues & Limitations

### Current Limitations

1. **No Query Execution:** SQL generated but not executed (Mo's task)
2. **No Result Visualization:** No charts/tables yet (Mo's task)
3. **Limited KPI Support:** Basic aggregations only
4. **No Query History:** Users can't see past queries
5. **Schema Format Inconsistency:** Builder writes "metrics", parser reads "kpis"

### Bug Fixes Needed

1. **streamlit_schema_builder.py:** Change "metrics" to "kpis" format
2. **Error Handling:** Better error messages for users
3. **Token Expiration:** No refresh token handling yet

---

## 📚 Code Style & Conventions

### Python Style
- **PEP 8** compliant
- Type hints for all function signatures
- Docstrings for all public functions
- Logging instead of print statements

### Naming Conventions
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Error Handling
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## 🔗 Module Dependencies

```
api_service.py
├── s3_service.py
│   ├── boto3
│   └── PyJWT
├── llm_sql_generator.py
│   ├── schema_parser.py
│   │   └── llm_table_selector.py
│   └── date_converter.py
└── sql_validator.py

streamlit_app_auth.py
├── auth_service.py
│   └── boto3 (Cognito)
└── requests (to call api_service)
```

---

This technical documentation covers the complete codebase architecture, all key classes and methods, and the full request flow. For API endpoint details, see `API_DOCUMENTATION.md`.
