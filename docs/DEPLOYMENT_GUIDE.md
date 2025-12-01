# Deployment Guide - Talk2Data

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- Docker (optional, for containerized deployment)
- AWS Account (for S3 and Cognito)
- OpenAI API Key
- Railway Account (for cloud deployment)

---

## 💻 Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/raedmokdad/talk2data.git
cd talk2data
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements include:**
- fastapi
- uvicorn[standard]
- streamlit
- openai
- boto3
- PyJWT
- python-dotenv
- pydantic
- requests

### Step 4: Configure Environment Variables

Create `.env` file in project root:

```bash
# .env
# OpenAI API
OPENAI_API_KEY=sk-proj-your-key-here

# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=smart-forecast

# AWS Cognito
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_1WET5qWMS
COGNITO_APP_CLIENT_ID=6dst32npudvcr207ufsacfavui
COGNITO_APP_CLIENT_SECRET=your-client-secret

# API Configuration
PORT=8000
API_URL=http://localhost:8000
```

### Step 5: Run Services

**Terminal 1 - FastAPI Backend:**
```bash
python api_service.py
```
API will be available at: http://localhost:8000

**Terminal 2 - Streamlit Frontend:**
```bash
streamlit run streamlit_app_auth.py
```
UI will be available at: http://localhost:8501

### Step 6: Test the System

Open browser: http://localhost:8501
1. Create account or login with Cognito
2. Select schema: `retial_star_schema`
3. Ask question: "Show total sales by store"
4. SQL should be generated successfully

---

## 🐳 Docker Deployment

### Build Images

**API Service:**
```bash
docker build -t talk2data-api -f Dockerfile .
```

**Streamlit Service:**
```bash
docker build -t talk2data-streamlit -f Dockerfile.streamlit .
```

### Run Containers

**API Container:**
```bash
docker run -d \
  --name talk2data-api \
  -p 8000:8000 \
  --env-file .env \
  talk2data-api
```

**Streamlit Container:**
```bash
docker run -d \
  --name talk2data-streamlit \
  -p 8501:8501 \
  --env-file .env \
  -e API_URL=http://talk2data-api:8000 \
  talk2data-streamlit
```

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PORT=8000
    restart: unless-stopped
    
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    env_file:
      - .env
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

**Stop services:**
```bash
docker-compose down
```

---

## ☁️ Railway Deployment

### Prerequisites

1. Railway account: https://railway.app
2. GitHub repository connected
3. Railway CLI installed (optional)

### Method 1: GitHub Integration (Recommended)

#### Step 1: Connect Repository

1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `raedmokdad/talk2data`
5. Railway will auto-detect Dockerfile

#### Step 2: Configure Environment Variables

In Railway dashboard, go to project → Variables:

```
OPENAI_API_KEY=sk-proj-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=smart-forecast
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_...
COGNITO_APP_CLIENT_ID=...
COGNITO_APP_CLIENT_SECRET=...
```

#### Step 3: Deploy

Railway automatically deploys on every push to `main` branch.

**Manual Deployment:**
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Railway will:
1. Detect changes
2. Build Docker image from Dockerfile
3. Deploy to production
4. Provide public URL: `https://your-app.up.railway.app`

#### Step 4: Configure Custom Domain (Optional)

1. Go to project → Settings → Domains
2. Click "Generate Domain" or add custom domain
3. Update DNS records if using custom domain

### Method 2: Railway CLI

#### Install Railway CLI

```bash
npm install -g @railway/cli
```

#### Login

```bash
railway login
```

#### Initialize Project

```bash
railway init
```

#### Link to Existing Project

```bash
railway link
```

#### Deploy

```bash
railway up
```

#### Open Deployed App

```bash
railway open
```

---

## 🔧 Configuration Management

### Environment-Specific Configs

**Development (.env.development):**
```bash
API_URL=http://localhost:8000
DEBUG=True
LOG_LEVEL=DEBUG
```

**Production (.env.production):**
```bash
API_URL=https://talk2data-production.up.railway.app
DEBUG=False
LOG_LEVEL=INFO
```

### Loading Config

```python
from dotenv import load_dotenv
import os

# Load environment-specific config
env = os.getenv('ENVIRONMENT', 'development')
load_dotenv(f'.env.{env}')

API_URL = os.getenv('API_URL')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

---

## 📊 Monitoring & Logging

### Railway Logs

View logs in Railway dashboard:
```bash
# Or via CLI
railway logs
```

### Application Logging

Configure logging in `api_service.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Health Check Monitoring

Set up monitoring service to ping:
```
GET https://talk2data-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy"
}
```

---

## 🔐 Security Configuration

### AWS IAM Setup

Create IAM user with minimal permissions:

**Policy for S3:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::smart-forecast/schemas/*",
        "arn:aws:s3:::smart-forecast"
      ]
    }
  ]
}
```

**Policy for Cognito:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:InitiateAuth",
        "cognito-idp:GetUser",
        "cognito-idp:SignUp",
        "cognito-idp:ConfirmSignUp"
      ],
      "Resource": "arn:aws:cognito-idp:us-east-1:*:userpool/us-east-1_*"
    }
  ]
}
```

### JWT Token Security

In production, enable signature verification:

```python
# src/s3_service.py
def get_current_user(credentials):
    token = credentials.credentials
    
    # Get Cognito public key
    jwks_url = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    
    # Verify signature
    payload = jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],
        options={"verify_signature": True}
    )
    
    return extract_username(payload)
```

---

## 🧪 Testing in Production

### Smoke Tests

```bash
# Test health
curl https://talk2data-production.up.railway.app/health

# Test root
curl https://talk2data-production.up.railway.app/

# Test authenticated endpoint (with token)
curl -X POST https://talk2data-production.up.railway.app/generate-sql \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show total sales", "schema_name": "retial_star_schema"}'
```

### Load Testing

Use Apache Bench or hey:

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 https://talk2data-production.up.railway.app/health
```

---

## 🔄 Continuous Deployment

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service api
```

### Deployment Strategy

**Zero-Downtime Deployment:**
1. Railway builds new image
2. Starts new container
3. Health check passes
4. Routes traffic to new container
5. Shuts down old container

---

## 📈 Scaling

### Horizontal Scaling (Railway)

Railway auto-scales based on:
- CPU usage > 80%
- Memory usage > 80%
- Request queue length

**Manual scaling:**
```bash
railway scale --replicas 3
```

### Vertical Scaling

Upgrade Railway plan for:
- More CPU cores
- More RAM
- Higher network bandwidth

---

## 🚨 Troubleshooting

### Common Issues

#### Issue 1: ModuleNotFoundError

**Problem:**
```
ModuleNotFoundError: No module named 'boto3'
```

**Solution:**
```bash
pip install -r requirements.txt
```

#### Issue 2: JWT Token Invalid

**Problem:**
```
401 Unauthorized: Invalid token
```

**Solution:**
- Check token hasn't expired
- Verify Cognito configuration
- Check token format: `Bearer <token>`

#### Issue 3: S3 Access Denied

**Problem:**
```
500 Internal Server Error: Access Denied
```

**Solution:**
- Verify AWS credentials in .env
- Check IAM permissions
- Verify S3 bucket name

#### Issue 4: OpenAI API Error

**Problem:**
```
500: OpenAI API error
```

**Solution:**
- Check API key is valid
- Verify account has credits
- Check rate limits

### Debug Mode

Enable debug logging:

```python
# api_service.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Railway Logs

```bash
railway logs --tail
```

---

## 🔄 Database Connector Setup (For Mo)

### PostgreSQL Connector

**Install dependencies:**
```bash
pip install psycopg2-binary sqlalchemy
```

**Create connector:**
```python
# src/postgres_connector.py
import psycopg2
from typing import Dict, List

class PostgresConnector:
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def execute_query(self, sql: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(sql)
        
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
```

**Environment variables:**
```bash
# .env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Testing Database Connection

```python
# test_db_connector.py
from postgres_connector import PostgresConnector

conn = PostgresConnector(os.getenv('DATABASE_URL'))
result = conn.execute_query("SELECT 1")
print(result)  # Should print: [{'?column?': 1}]
```

---

## 📦 Backup & Recovery

### S3 Schema Backup

```bash
# Backup all schemas
aws s3 sync s3://smart-forecast/schemas ./backups/schemas

# Restore schemas
aws s3 sync ./backups/schemas s3://smart-forecast/schemas
```

### Database Backup (For Mo)

```bash
# PostgreSQL backup
pg_dump -h localhost -U user -d talk2data > backup.sql

# Restore
psql -h localhost -U user -d talk2data < backup.sql
```

---

## 🎯 Performance Optimization

### 1. Enable Caching

```python
# Cache schema parser
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_schema(schema_name: str):
    return get_schema_parser(schema_name)
```

### 2. Connection Pooling

```python
# For database connections (Mo's task)
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### 3. Async Operations

```python
# Use async for I/O operations
import asyncio
from aiohttp import ClientSession

async def async_openai_call():
    async with ClientSession() as session:
        async with session.post(url, json=data) as response:
            return await response.json()
```

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check Railway logs for errors
- Monitor API response times
- Verify health endpoint

**Weekly:**
- Review OpenAI API usage and costs
- Check AWS S3 storage usage
- Update dependencies if needed

**Monthly:**
- Rotate AWS access keys
- Review and optimize schemas
- Performance optimization review

### Getting Help

**Documentation:**
- Project Overview: `docs/PROJECT_OVERVIEW.md`
- Technical Docs: `docs/TECHNICAL_DOCUMENTATION.md`
- API Docs: `docs/API_DOCUMENTATION.md`

**Community:**
- GitHub Issues: https://github.com/raedmokdad/talk2data/issues
- Email: raed.mokdad@example.com

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally
- [ ] Environment variables configured
- [ ] AWS credentials verified
- [ ] OpenAI API key valid
- [ ] Dependencies updated (`pip list --outdated`)
- [ ] .gitignore includes .env
- [ ] Documentation updated

### Deployment

- [ ] Code pushed to GitHub main branch
- [ ] Railway build successful
- [ ] Health check returns 200 OK
- [ ] Smoke tests passing
- [ ] Logs show no errors

### Post-Deployment

- [ ] Test all endpoints with real data
- [ ] Verify JWT authentication works
- [ ] Test schema CRUD operations
- [ ] Monitor logs for 30 minutes
- [ ] Set up monitoring alerts
- [ ] Document any issues

---

## 🎉 Success!

Your Talk2Data system should now be fully deployed and operational!

**Next Steps:**
1. Test with real queries
2. Onboard users
3. Monitor performance
4. Gather feedback
5. Iterate and improve

For questions or issues, refer to the documentation or open a GitHub issue.
