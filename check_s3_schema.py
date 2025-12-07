"""
Download and check employee_schema from S3
"""
import boto3
import json
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = "talk2data-schemas"
AWS_REGION = "eu-central-1"

s3_client = boto3.client('s3', region_name=AWS_REGION)

username = "raedmokdad"
schema_name = "employee_schema"
s3_key = f"schemas/{username}/{schema_name}.json"

print(f"Downloading schema from S3...")
print(f"Bucket: {S3_BUCKET}")
print(f"Key: {s3_key}")
print("=" * 60)

try:
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
    schema_data = json.loads(response['Body'].read().decode('utf-8'))
    
    print("\n✅ Schema downloaded successfully!")
    print("\nSchema structure:")
    print(json.dumps(schema_data, indent=2))
    
    # Analyze structure
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    
    if "schema" in schema_data:
        print("✅ Has 'schema' key")
        schema = schema_data["schema"]
        
        if "tables" in schema:
            tables = schema["tables"]
            print(f"✅ Has 'tables': {len(tables)} table(s)")
            if tables:
                table = tables[0]
                print(f"   - Table name: {table.get('name', 'N/A')}")
                print(f"   - Role: {table.get('role', 'N/A')}")
                print(f"   - Columns: {len(table.get('columns', {}))}")
        else:
            print("❌ Missing 'tables' key")
            
        if "metrics" in schema:
            metrics = schema["metrics"]
            print(f"✅ Has 'metrics': {len(metrics)} metric(s)")
            for name, metric in metrics.items():
                print(f"   - {name}: {metric.get('formula', 'N/A')}")
        else:
            print("❌ Missing 'metrics' key")
            
        if "glossary" in schema:
            print(f"✅ Has 'glossary': {len(schema['glossary'])} entries")
        else:
            print("⚠️ Missing 'glossary' key")
    else:
        print("❌ Missing 'schema' key - OLD FORMAT!")
        if "table" in schema_data:
            print(f"   Found old format with 'table': {schema_data.get('table')}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
