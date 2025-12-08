"""Test S3 Access"""
import boto3
from dotenv import load_dotenv
import os

load_dotenv(override=True)

from src.constants import S3_SCHEMA_PREFIX

bucket = os.getenv('S3_BUCKET')
region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
prefix = f'{S3_SCHEMA_PREFIX}/rmokdad/'

print(f"Bucket: {bucket}")
print(f"Region: {region}")
print(f"Prefix: {prefix}")
print(f"AWS_ACCESS_KEY_ID: {'SET' if os.getenv('AWS_ACCESS_KEY_ID') else 'NOT SET'}")
print(f"AWS_SECRET_ACCESS_KEY: {'SET' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'NOT SET'}")
print("\nTesting S3 access...")

try:
    s3 = boto3.client('s3', region_name=region)
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if 'Contents' in response:
        files = [obj['Key'] for obj in response['Contents']]
        print(f"\n✅ Success! Found {len(files)} files:")
        for f in files:
            print(f"  - {f}")
    else:
        print(f"\n⚠️ No files found under {bucket}/{prefix}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
