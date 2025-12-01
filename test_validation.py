import sys
sys.path.insert(0, 'src')
from llm_sql_generator import generate_multi_table_sql

test_questions = [
    ("What were the total sales in January 2015?", True),
    ("How many customers visited in February 2015?", False),
    ("Which stores had the highest sales during promotional periods?", True),
    ("Show me sales by product category in 2015", True),
    ("How many transactions occurred in December 2014?", True),
    ("What is the average sales amount per store in Q1 2015?", True),
    ("Show employee performance metrics", False),
    ("Which products sold best during holidays?", True),
    ("Compare sales between stores in Germany and France", True),
    ("What is the inventory level for product SKU 12345?", False),
]

print("="*70)
print("SYSTEM VALIDATION TEST - MULTIPLE QUESTIONS")
print("="*70)

passed = 0
failed = 0

for i, (question, should_succeed) in enumerate(test_questions, 1):
    print(f"\n{'='*70}")
    print(f"Test {i}: {question}")
    print(f"Expected: {'Success' if should_succeed else 'Error'}")
    print("-"*70)
    
    try:
        result = generate_multi_table_sql(question, schema_name='retial_star_schema')
        
        if should_succeed:
            print("✓ PASS - Query generated:")
            print(result)
            passed += 1
        else:
            print("✗ FAIL - Query was generated but should have failed!")
            print(result)
            failed += 1
            
    except ValueError as e:
        if not should_succeed:
            print(f"✓ PASS - Error correctly detected:")
            print(f"   {e}")
            passed += 1
        else:
            print(f"✗ FAIL - Unexpected error:")
            print(f"   {e}")
            failed += 1
    except Exception as e:
        print(f"✗ FAIL - Unexpected exception: {type(e).__name__}: {e}")
        failed += 1

print(f"\n{'='*70}")
print(f"TEST RESULTS: {passed}/{len(test_questions)} passed, {failed}/{len(test_questions)} failed")
print("="*70)
