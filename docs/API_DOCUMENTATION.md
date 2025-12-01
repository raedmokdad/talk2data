# API Documentation - Talk2Data

## 🌐 Base URL

**Production:** `https://talk2data-production.up.railway.app`  
**Local Development:** `http://localhost:8000`

**Swagger UI:** `{BASE_URL}/docs`  
**ReDoc:** `{BASE_URL}/redoc`

---

## 🔐 Authentication

All endpoints (except `/`, `/health`, `/docs`) require JWT authentication.

### Authentication Header
```http
Authorization: Bearer <jwt_token>
```

### Getting a JWT Token

Use AWS Cognito to authenticate and get tokens:

```python
import boto3

cognito = boto3.client('cognito-idp', region_name='us-east-1')

response = cognito.initiate_auth(
    ClientId='6dst32npudvcr207ufsacfavui',
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'your-username',
        'PASSWORD': 'your-password'
    }
)

access_token = response['AuthenticationResult']['AccessToken']
```

---

## 📍 Endpoints

### 1. Root Endpoint

#### `GET /`

Returns basic service information.

**Request:**
```bash
curl https://talk2data-production.up.railway.app/
```

**Response:**
```json
{
  "service": "Talk2Data Agent API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": ["/generate-sql", "/health", "/docs"]
}
```

---

### 2. Health Check

#### `GET /health`

Health check endpoint for monitoring and load balancers.

**Request:**
```bash
curl https://talk2data-production.up.railway.app/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "talk2data-agent-multitable",
  "timestamp": 1701000000.123,
  "schema_loaded": true,
  "tables_count": 4,
  "available_tables": [
    "fact_sales",
    "dim_store",
    "dim_product",
    "dim_date"
  ]
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy (schema loading failed, etc.)

---

### 3. Generate SQL

#### `POST /generate-sql`

🔐 **Requires Authentication**

Generates SQL query from natural language question.

**Request Body:**
```json
{
  "question": "Show total sales by store",
  "schema_name": "retial_star_schema",
  "max_retries": 3,
  "confidence_threshold": 0.7
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | string | ✅ Yes | - | Natural language question (max 500 chars) |
| `schema_name` | string | ❌ No | "retial_star_schema" | Name of schema to use |
| `max_retries` | integer | ❌ No | 3 | Not implemented yet |
| `confidence_threshold` | float | ❌ No | 0.7 | Not implemented yet |

**cURL Example:**
```bash
curl -X POST https://talk2data-production.up.railway.app/generate-sql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "question": "Show total sales by store in January 2024",
    "schema_name": "retial_star_schema"
  }'
```

**Python Example:**
```python
import requests

url = "https://talk2data-production.up.railway.app/generate-sql"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {jwt_token}"
}
data = {
    "question": "What are the top 5 products by revenue?",
    "schema_name": "retial_star_schema"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

print(f"SQL: {result['sql_query']}")
print(f"Confidence: {result['confidence']}")
```

**Success Response (200 OK):**
```json
{
  "sql_query": "SELECT dim_store.store_name, SUM(fact_sales.sales_amount) as total_sales FROM fact_sales LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id WHERE fact_sales.sale_date >= '2024-01-01' AND fact_sales.sale_date <= '2024-01-31' GROUP BY dim_store.store_name ORDER BY total_sales DESC",
  "confidence": 0.95,
  "validation_passed": true,
  "processing_time": 1.234,
  "message": "SQL generated and validated successfully"
}
```

**Error Responses:**

**400 Bad Request - Empty Question**
```json
{
  "detail": "Question cannot be empty"
}
```

**400 Bad Request - Question Too Long**
```json
{
  "detail": "Question too long (max 500 characters)"
}
```

**400 Bad Request - SQL Validation Failed**
```json
{
  "detail": "SQL validation failed: Security violation: Forbidden SQL operation detected: DROP"
}
```

**401 Unauthorized - Missing/Invalid Token**
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found - Schema Not Found**
```json
{
  "detail": "Schema 'my_schema' not found for user 'raed_mokdad'"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error: Unable to connect selected tables with JOINs"
}
```

---

### 4. List User Schemas

#### `GET /schemas/{username}`

🔐 **Requires Authentication**

Lists all schemas for a specific user.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `username` | string | Username (extracted from JWT token) |

**cURL Example:**
```bash
curl -X GET https://talk2data-production.up.railway.app/schemas/raed_mokdad \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python Example:**
```python
import requests

url = "https://talk2data-production.up.railway.app/schemas/raed_mokdad"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.get(url, headers=headers)
result = response.json()

print(f"Found {result['count']} schemas:")
for schema in result['schemas']:
    print(f"  - {schema}")
```

**Success Response (200 OK):**
```json
{
  "username": "raed_mokdad",
  "schemas": [
    "retial_star_schema",
    "sales_analytics",
    "ecommerce_schema"
  ],
  "count": 3,
  "success": true
}
```

**Empty Response:**
```json
{
  "username": "raed_mokdad",
  "schemas": [],
  "count": 0,
  "success": true
}
```

---

### 5. Get Specific Schema

#### `GET /schemas/{username}/{schema_name}`

🔐 **Requires Authentication**

Retrieves a specific schema JSON.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `username` | string | Username |
| `schema_name` | string | Schema name (without .json) |

**cURL Example:**
```bash
curl -X GET https://talk2data-production.up.railway.app/schemas/raed_mokdad/retial_star_schema \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "username": "raed_mokdad",
  "schema_name": "retial_star_schema",
  "schema": {
    "name": "retial_star_schema",
    "description": "Retail star schema with fact_sales and dimensions",
    "schema": {
      "tables": [
        {
          "name": "fact_sales",
          "role": "fact",
          "grain": "One row per transaction",
          "columns": {
            "sale_id": "Unique transaction ID",
            "store_id": "Foreign key to dim_store",
            "product_id": "Foreign key to dim_product",
            "date_id": "Foreign key to dim_date",
            "sales_amount": "Total sales value",
            "quantity": "Number of items sold"
          }
        }
      ],
      "relationships": [
        {
          "from": "fact_sales.store_id",
          "to": "dim_store.store_id",
          "join_type": "LEFT JOIN",
          "description": "Link sales to store information"
        }
      ]
    },
    "kpis": {
      "total_sales": {
        "description": "Sum of all sales",
        "calculation": "SUM(sales_amount)",
        "keywords": ["umsatz", "sales", "revenue"]
      }
    }
  },
  "success": true
}
```

**Error Response (404):**
```json
{
  "username": "raed_mokdad",
  "schema_name": "nonexistent_schema",
  "schema": {},
  "success": false
}
```

---

### 6. Create Schema

#### `POST /schemas/{username}/{schema_name}`

🔐 **Requires Authentication**

Creates a new schema in S3.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `username` | string | Username |
| `schema_name` | string | Schema name (without .json) |

**Request Body:**
```json
{
  "schema_data": {
    "name": "my_new_schema",
    "description": "My custom schema",
    "schema": {
      "tables": [...],
      "relationships": [...]
    },
    "kpis": {...}
  }
}
```

**cURL Example:**
```bash
curl -X POST https://talk2data-production.up.railway.app/schemas/raed_mokdad/my_schema \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d @schema.json
```

**Python Example:**
```python
import requests

url = "https://talk2data-production.up.railway.app/schemas/raed_mokdad/my_schema"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {jwt_token}"
}

schema_data = {
    "schema_data": {
        "name": "my_schema",
        "description": "Custom retail schema",
        "schema": {
            "tables": [
                {
                    "name": "fact_orders",
                    "role": "fact",
                    "columns": {
                        "order_id": "Unique order ID",
                        "customer_id": "FK to dim_customer"
                    }
                }
            ]
        }
    }
}

response = requests.post(url, json=schema_data, headers=headers)
result = response.json()

print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
```

**Success Response (200 OK):**
```json
{
  "username": "raed_mokdad",
  "schema_name": "my_schema",
  "message": "my_schema uploaded",
  "success": true
}
```

**Error Response (400):**
```json
{
  "detail": "Schema data cannot be empty"
}
```

---

### 7. Update Schema

#### `PUT /schemas/{username}/{schema_name}`

🔐 **Requires Authentication**

Updates an existing schema in S3.

**Request/Response:** Same as Create Schema

---

### 8. Delete Schema

#### `DELETE /schemas/{username}/{schema_name}`

🔐 **Requires Authentication**

Deletes a schema from S3.

**cURL Example:**
```bash
curl -X DELETE https://talk2data-production.up.railway.app/schemas/raed_mokdad/old_schema \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "username": "raed_mokdad",
  "schema_name": "old_schema",
  "message": "Schema 'old_schema' deleted successfully",
  "success": true
}
```

**Error Response:**
```json
{
  "username": "raed_mokdad",
  "schema_name": "nonexistent",
  "message": "Schema 'nonexistent' not found or error",
  "success": false
}
```

---

### 9. Service Info

#### `GET /info`

Returns detailed service information including schema summary.

**Request:**
```bash
curl https://talk2data-production.up.railway.app/info
```

**Response:**
```json
{
  "service": "Talk2Data Agent - Multi-Table",
  "version": "2.0.0",
  "features": [
    "Automatic table selection (LLM)",
    "Algorithmic JOIN generation",
    "Multi-table SQL queries",
    "Star schema optimized"
  ],
  "schema_name": "retial_star_schema",
  "tables": [
    "fact_sales",
    "dim_store",
    "dim_product",
    "dim_date"
  ],
  "tables_count": 4,
  "relationships_count": 3,
  "schema_summary": "Table: fact_sales (fact)\n- Grain: One row per transaction\n- Columns: sale_id, store_id, product_id..."
}
```

---

## 🧪 Testing Examples

### Test 1: Simple Single-Table Query

```python
import requests

url = "https://talk2data-production.up.railway.app/generate-sql"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

data = {
    "question": "Show total sales amount",
    "schema_name": "retial_star_schema"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

# Expected SQL: SELECT SUM(sales_amount) FROM fact_sales
print(result['sql_query'])
```

### Test 2: Multi-Table Query with JOINs

```python
data = {
    "question": "Show sales by store and product category",
    "schema_name": "retial_star_schema"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

# Expected: Joins fact_sales → dim_store → dim_product
# SQL will contain multiple LEFT JOINs
print(result['sql_query'])
```

### Test 3: Date Intelligence

```python
data = {
    "question": "Show monthly sales in 2024",
    "schema_name": "retial_star_schema"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

# Expected: Date filter converted to ISO format
# WHERE date >= '2024-01-01' AND date <= '2024-12-31'
print(result['sql_query'])
```

### Test 4: Security Test (Should Fail)

```python
data = {
    "question": "DROP TABLE fact_sales; SELECT * FROM fact_sales",
    "schema_name": "retial_star_schema"
}

response = requests.post(url, json=data, headers=headers)

# Expected: 400 Bad Request
# Detail: "SQL validation failed: Security violation: Forbidden SQL operation detected: DROP"
print(response.status_code)  # 400
print(response.json()['detail'])
```

---

## 🔧 Error Handling

### Standard Error Response Format

All errors follow FastAPI's standard format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid input, validation failed, SQL injection detected |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Schema not found, endpoint doesn't exist |
| 500 | Internal Server Error | LLM API failure, S3 connection error, JOIN generation failed |
| 503 | Service Unavailable | Health check failed, service not ready |

---

## 📊 Rate Limits

Currently no rate limits enforced.

**Future Implementation:**
- 100 requests per minute per user
- 1000 requests per day per user

---

## 🔄 Versioning

Current API version: **v1.0.0**

Version is included in all responses via the `version` field.

**Future:** Will use URL versioning when breaking changes occur:
- `/v1/generate-sql`
- `/v2/generate-sql`

---

## 🌍 CORS Configuration

CORS is enabled for all origins in development.

**Production CORS Policy:**
```python
origins = [
    "https://talk2data-frontend.up.railway.app",
    "http://localhost:8501"  # Streamlit
]
```

---

## 📝 Request/Response Examples Collection

### Example 1: Sales Analysis

**Request:**
```json
{
  "question": "What are the top 5 stores by total sales in Q1 2024?",
  "schema_name": "retial_star_schema"
}
```

**Response SQL:**
```sql
SELECT 
    dim_store.store_name,
    dim_store.city,
    SUM(fact_sales.sales_amount) as total_sales
FROM fact_sales
LEFT JOIN dim_store ON fact_sales.store_id = dim_store.store_id
LEFT JOIN dim_date ON fact_sales.date_id = dim_date.date_id
WHERE dim_date.quarter = 1 AND dim_date.year = 2024
GROUP BY dim_store.store_name, dim_store.city
ORDER BY total_sales DESC
LIMIT 5
```

### Example 2: Product Performance

**Request:**
```json
{
  "question": "Show products with sales above average",
  "schema_name": "retial_star_schema"
}
```

**Response SQL:**
```sql
SELECT 
    dim_product.product_name,
    SUM(fact_sales.sales_amount) as product_sales
FROM fact_sales
LEFT JOIN dim_product ON fact_sales.product_id = dim_product.product_id
GROUP BY dim_product.product_name
HAVING SUM(fact_sales.sales_amount) > (
    SELECT AVG(total_sales) 
    FROM (
        SELECT SUM(sales_amount) as total_sales 
        FROM fact_sales 
        GROUP BY product_id
    ) as subquery
)
ORDER BY product_sales DESC
```

### Example 3: Time-Based Analysis

**Request:**
```json
{
  "question": "Compare sales between January and February 2024",
  "schema_name": "retial_star_schema"
}
```

**Response SQL:**
```sql
SELECT 
    dim_date.month_name,
    SUM(fact_sales.sales_amount) as monthly_sales,
    COUNT(DISTINCT fact_sales.sale_id) as transaction_count
FROM fact_sales
LEFT JOIN dim_date ON fact_sales.date_id = dim_date.date_id
WHERE dim_date.year = 2024 
  AND dim_date.month IN (1, 2)
GROUP BY dim_date.month_name, dim_date.month
ORDER BY dim_date.month
```

---

## 🚀 Performance Tips

### 1. Schema Caching
The system caches loaded schemas. First request loads from S3, subsequent requests use cached version.

### 2. Question Optimization
- **Good:** "Show total sales by store"
- **Better:** "Show total sales by store for 2024"
- **Best:** "Show total sales amount grouped by store name for year 2024"

More specific questions generate better SQL.

### 3. Schema Design
- Keep schemas focused (don't include unused tables)
- Clear column descriptions help LLM generate better SQL
- Define relationships explicitly

---

## 🔐 Security Best Practices

### Client-Side

1. **Store JWT Securely:**
   ```python
   # ❌ Don't do this
   jwt_token = "eyJhbGc..."  # Hardcoded
   
   # ✅ Do this
   jwt_token = os.getenv("JWT_TOKEN")  # From environment
   ```

2. **Validate Server Responses:**
   ```python
   response = requests.post(url, json=data, headers=headers)
   response.raise_for_status()  # Raise exception for 4xx/5xx
   ```

3. **Handle Token Expiration:**
   ```python
   if response.status_code == 401:
       # Token expired, refresh it
       jwt_token = refresh_token()
       # Retry request
   ```

### Server-Side (Implemented)

- ✅ JWT token validation on all protected endpoints
- ✅ SQL injection prevention via validator
- ✅ Input length limits (500 chars for questions)
- ✅ Schema isolation per user (S3 paths)
- ✅ Forbidden command detection (DROP, DELETE, etc.)

---

## 📞 Support

**Issues:** https://github.com/raedmokdad/talk2data/issues  
**Email:** raed.mokdad@example.com

**Response Time:**
- Critical bugs: < 24 hours
- Feature requests: 1-2 weeks
- General questions: 2-3 days

---

## 📚 Additional Resources

- **Project Overview:** `docs/PROJECT_OVERVIEW.md`
- **Technical Docs:** `docs/TECHNICAL_DOCUMENTATION.md`
- **Deployment Guide:** `docs/DEPLOYMENT_GUIDE.md`
- **Swagger UI:** `https://talk2data-production.up.railway.app/docs`
