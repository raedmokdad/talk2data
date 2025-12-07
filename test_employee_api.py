"""
Test employee schema API call
"""
import requests

API_URL = "https://talk2data-production.up.railway.app"

payload = {
    "question": "Zähle alle Zeilen in der employees Tabelle",
    "schema_name": "employee_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_r"]  # Actual table name from DuckDB
}

print("Testing employee schema...")
print(f"Question: {payload['question']}")
print(f"Schema: {payload['schema_name']}")
print(f"Table names: {payload['table_names']}")

try:
    response = requests.post(
        f"{API_URL}/generate-sql",
        json=payload,
        timeout=30
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
