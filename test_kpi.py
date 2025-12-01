import os
from src.llm_sql_generator import generate_multi_table_sql

os.environ.setdefault('OPENAI_API_KEY', 'dummy-key-for-testing')

print("Testing KPI and Synonym Support")
print("=" * 70)

test_questions = [
    "What is the net sales for January 2015?",
    "Show me the Bruttoumsatz by store",
    "What is the average discount rate?",
    "Show Umsatz pro Filiale for Q1 2015"
]

for question in test_questions:
    print(f"\nQuestion: {question}")
    print("-" * 70)
    try:
        sql = generate_multi_table_sql(question, schema_name="retial_star_schema")
        if sql:
            print("✓ Generated SQL:")
            print(sql)
        else:
            print("✗ No SQL generated")
    except Exception as e:
        print(f"✗ Error: {e}")
