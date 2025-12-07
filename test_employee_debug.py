"""
Test what schema the API is using
"""
import requests

API_URL = "https://talk2data-production.up.railway.app"

# Test 1: Simple column check
print("=" * 60)
print("TEST 1: Check if 'employee_id' column exists")
print("=" * 60)

payload1 = {
    "question": "SELECT employee_id FROM employees LIMIT 1",
    "schema_name": "employee_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_r"]
}

try:
    response = requests.post(f"{API_URL}/generate-sql", json=payload1, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Check what the LLM thinks is in the schema
print("\n" + "=" * 60)
print("TEST 2: Ask for all columns")
print("=" * 60)

payload2 = {
    "question": "Zeige mir alle Spalten aus der Tabelle",
    "schema_name": "employee_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_r"]
}

try:
    response = requests.post(f"{API_URL}/generate-sql", json=payload2, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Direct COUNT(*)
print("\n" + "=" * 60)
print("TEST 3: Simple COUNT(*)")
print("=" * 60)

payload3 = {
    "question": "Wie viele Mitarbeiter gibt es?",
    "schema_name": "employee_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_r"]
}

# Test 4: Test updated schema
print("\n" + "=" * 60)
print("TEST 4: After schema update")
print("=" * 60)

payload4 = {
    "question": "Wie viele Mitarbeiter gibt es?",
    "schema_name": "employee_schema",
    "username": "raedmokdad",
    "table_names": ["c_users_r"]
}

try:
    response = requests.post(f"{API_URL}/generate-sql", json=payload4, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

try:
    response = requests.post(f"{API_URL}/generate-sql", json=payload3, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SQL: {result.get('sql_query', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
