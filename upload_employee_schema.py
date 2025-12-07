"""
Upload corrected employee_schema to S3
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# S3 Configuration
S3_BUCKET = "talk2data-schemas"
AWS_REGION = "eu-central-1"

# Load the corrected schema from file
with open('src/config/employee_schema.json', 'r', encoding='utf-8') as f:
    employee_schema = json.load(f)

# Upload to S3
s3_client = boto3.client('s3', region_name=AWS_REGION)

username = "raedmokdad"
schema_name = "employee_schema"
s3_key = f"schemas/{username}/{schema_name}.json"

try:
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(employee_schema, indent=2),
        ContentType='application/json'
    )
    print(f"✅ Schema uploaded successfully to s3://{S3_BUCKET}/{s3_key}")
    print(f"\nSchema structure:")
    print(f"  - Tables: {len(employee_schema.get('schema', {}).get('tables', []))}")
    print(f"  - Metrics: {len(employee_schema.get('schema', {}).get('metrics', {}))}")
    print(f"  - Has glossary: {('glossary' in employee_schema.get('schema', {}))}")
except Exception as e:
    print(f"❌ Error uploading schema: {e}")
