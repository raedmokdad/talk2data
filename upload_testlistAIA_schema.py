"""
Upload testlistAIA_schema to S3
"""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# S3 Configuration
S3_BUCKET = "smart-forecast"
AWS_REGION = "us-east-1"

# Load the schema from file
with open('src/config/testlistAIA_schema.json', 'r', encoding='utf-8') as f:
    testlistAIA_schema = json.load(f)

# Upload to S3
s3_client = boto3.client('s3', region_name=AWS_REGION)

username = "rmokdad"
schema_name = "testlistAIA_schema"
s3_key = f"schemas/{username}/{schema_name}.json"

try:
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(testlistAIA_schema, indent=2),
        ContentType='application/json'
    )
    print(f"✅ Schema successfully uploaded to s3://{S3_BUCKET}/{s3_key}")
except Exception as e:
    print(f"❌ Error uploading schema: {e}")
