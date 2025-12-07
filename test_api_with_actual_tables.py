"""
Test API with actual table names to verify the fix works end-to-end
"""
import requests
import json

API_URL = "https://talk2data-production.up.railway.app"

print("=" * 60)
print("TEST: API mit actual_table_names für flat table")
print("=" * 60)

# Simuliere was Streamlit sendet: CSV wurde als "c_users_r" registriert
# aber Schema definiert "test_orders"
payload = {
    "question": "Wie viele Bestellungen gibt es insgesamt?",
    "schema_name": "test_orders_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_r"]  # Actual table name from DuckDB
}

print(f"\n📤 Sende Request:")
print(f"   Question: {payload['question']}")
print(f"   Schema: {payload['schema_name']}")
print(f"   Table Names: {payload['table_names']}")

try:
    response = requests.post(
        f"{API_URL}/generate-sql",
        json=payload,
        timeout=30
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"\nGenerated SQL:")
        print(f"   {result.get('sql_query', 'N/A')}")
        print(f"\nConfidence: {result.get('confidence', 0):.2f}")
        print(f"Validation Passed: {result.get('validation_passed', False)}")
        print(f"Processing Time: {result.get('processing_time', 0):.3f}s")
        
        # Check if SQL uses actual table name
        sql = result.get('sql_query', '')
        if 'c_users_r' in sql:
            print(f"\n✅ SQL verwendet tatsächlichen Tabellennamen 'c_users_r'")
        else:
            print(f"\n⚠️ SQL verwendet NICHT 'c_users_r': {sql}")
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {response.text}")
        
except requests.exceptions.Timeout:
    print("\n❌ Request timeout")
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 60)
print("TEST 2: Employees Schema")
print("=" * 60)

payload2 = {
    "question": "Wie viele Mitarbeiter gibt es?",
    "schema_name": "employee_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_employees"]  # Different actual table name
}

print(f"\n📤 Sende Request:")
print(f"   Question: {payload2['question']}")
print(f"   Schema: {payload2['schema_name']}")
print(f"   Table Names: {payload2['table_names']}")

try:
    response = requests.post(
        f"{API_URL}/generate-sql",
        json=payload2,
        timeout=30
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"\nGenerated SQL:")
        print(f"   {result.get('sql_query', 'N/A')}")
        
        sql = result.get('sql_query', '')
        if 'c_users_employees' in sql:
            print(f"\n✅ SQL verwendet tatsächlichen Tabellennamen 'c_users_employees'")
        else:
            print(f"\n⚠️ SQL verwendet NICHT 'c_users_employees': {sql}")
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 60)
