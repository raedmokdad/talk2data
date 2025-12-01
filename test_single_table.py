import os
from src.llm_sql_generator import generate_multi_table_sql

os.environ.setdefault('OPENAI_API_KEY', 'dummy-key-for-testing')

print("Testing Single-Table Schema (employee_schema)")
print("=" * 70)

test_questions = [
    "Show all employees in the IT department",
    "What is the average salary by department?",
    "List employees hired after 2020",
    "Who are the top 5 highest paid employees?",
    "Show employees with performance rating above 4.0"
]

for question in test_questions:
    print(f"\nQuestion: {question}")
    print("-" * 70)
    try:
        sql = generate_multi_table_sql(question, schema_name="employee_schema")
        if sql:
            print("✓ Generated SQL:")
            print(sql)
        else:
            print("✗ No SQL generated")
    except Exception as e:
        print(f"✗ Error: {e}")
