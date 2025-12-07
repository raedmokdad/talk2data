"""
Systematic API test for all schemas
"""
import requests

API_URL = "https://talk2data-production.up.railway.app"

tests = [
    {
        "name": "test_orders WITH table_names",
        "question": "Wie viele Bestellungen gibt es?",
        "schema": "test_orders_schema",
        "table_names": ["c_users_r"]
    },
    {
        "name": "employee WITH table_names",
        "question": "Wie viele Mitarbeiter gibt es?",
        "schema": "employee_schema",
        "table_names": ["c_users_r"]
    },
    {
        "name": "test_orders WITHOUT table_names",
        "question": "Wie viele Bestellungen gibt es?",
        "schema": "test_orders_schema",
        "table_names": None
    },
    {
        "name": "employee WITHOUT table_names",
        "question": "Wie viele Mitarbeiter gibt es?",
        "schema": "employee_schema",
        "table_names": None
    }
]

for test in tests:
    print("\n" + "=" * 60)
    print(f"TEST: {test['name']}")
    print("=" * 60)
    
    payload = {
        "question": test["question"],
        "schema_name": test["schema"],
        "username": "raedmokdad"
    }
    
    if test["table_names"]:
        payload["table_names"] = test["table_names"]
    
    try:
        response = requests.post(f"{API_URL}/generate-sql", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            sql = result.get('sql_query', '')
            print(f"✅ SUCCESS")
            print(f"SQL: {sql[:100]}")
        else:
            print(f"❌ FAILED")
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
