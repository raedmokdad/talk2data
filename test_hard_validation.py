import os
from src.llm_sql_generator import generate_multi_table_sql
from src.schema_parser import get_schema_parser

os.environ.setdefault('OPENAI_API_KEY', 'dummy-key-for-testing')

print("=" * 70)
print("HARD VALIDATION TEST - EDGE CASES & TRICKY QUESTIONS")
print("=" * 70)

schema_parser = get_schema_parser("retial_star_schema")

test_cases = [
    # Edge Case 1: Ambiguous column names
    {
        "question": "Show me all revenue for 2015",
        "expected": "error",
        "reason": "No 'revenue' column exists (only sales_amount)"
    },
    
    # Edge Case 2: Wrong table concept
    {
        "question": "Which customers made the most purchases?",
        "expected": "error",
        "reason": "No customer table or customer columns"
    },
    
    # Edge Case 3: Non-existent metrics
    {
        "question": "What is the profit margin by store?",
        "expected": "error",
        "reason": "No profit or margin columns"
    },
    
    # Edge Case 4: Should work - uses existing columns
    {
        "question": "Show total sales_amount by store in 2015",
        "expected": "success",
        "reason": "sales_amount exists in fact_sales"
    },
    
    # Edge Case 5: Complex aggregation with existing data
    {
        "question": "What is the daily average sales quantity per store?",
        "expected": "success",
        "reason": "sales_quantity, store, date all exist"
    },
    
    # Edge Case 6: Completely wrong domain
    {
        "question": "Show me all orders shipped to customers",
        "expected": "error",
        "reason": "No orders, shipping, or customer data"
    },
    
    # Edge Case 7: Typo in column name concept
    {
        "question": "What are the total discounts given in January 2015?",
        "expected": "success",
        "reason": "discount_amount exists in fact_sales"
    },
    
    # Edge Case 8: Mix of valid and invalid concepts
    {
        "question": "Compare revenue and profit by product category",
        "expected": "error",
        "reason": "category exists, but 'revenue' and 'profit' don't"
    },
    
    # Edge Case 9: Asking for specific IDs/SKUs (valid)
    {
        "question": "Show all sales for product SKU ABC123",
        "expected": "success",
        "reason": "sku column exists in dim_product"
    },
    
    # Edge Case 10: Time-based with non-existent metric
    {
        "question": "Show weekly conversion rates for Q1 2015",
        "expected": "error",
        "reason": "No conversion rate data"
    },
    
    # Edge Case 11: Valid multi-table JOIN
    {
        "question": "List all products sold in stores located in Berlin",
        "expected": "success",
        "reason": "product, store, city columns exist"
    },
    
    # Edge Case 12: Asking for aggregation on non-existent field
    {
        "question": "What is the average customer satisfaction score?",
        "expected": "error",
        "reason": "No satisfaction or rating columns"
    },
    
    # Edge Case 13: Valid boolean field
    {
        "question": "How many sales were made on holidays vs non-holidays?",
        "expected": "success",
        "reason": "is_holiday exists in dim_date"
    },
    
    # Edge Case 14: Complex nested concept
    {
        "question": "Show employee sales performance by region",
        "expected": "error",
        "reason": "No employee data"
    },
    
    # Edge Case 15: Boundary test with dates
    {
        "question": "Show sales for stores that opened after January 1, 2014",
        "expected": "success",
        "reason": "open_date exists in dim_store"
    }
]

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 70}")
    print(f"Test {i}: {test['question']}")
    print(f"Expected: {test['expected'].upper()}")
    print(f"Reason: {test['reason']}")
    print("-" * 70)
    
    try:
        sql = generate_multi_table_sql(test['question'], schema_name="retial_star_schema")
        
        if test['expected'] == 'success' and sql:
            print(f"✓ PASS - Query generated:")
            print(sql)
            passed += 1
        elif test['expected'] == 'success' and not sql:
            print(f"✗ FAIL - Expected success but got None")
            failed += 1
        elif test['expected'] == 'error' and sql:
            print(f"✗ FAIL - Expected error but query was generated:")
            print(sql)
            failed += 1
        else:
            print(f"? UNEXPECTED - SQL is None but expected success")
            failed += 1
            
    except Exception as e:
        error_msg = str(e)
        if test['expected'] == 'error':
            print(f"✓ PASS - Error correctly detected:")
            print(f"   {error_msg}")
            passed += 1
        else:
            print(f"✗ FAIL - Unexpected error:")
            print(f"   {error_msg}")
            failed += 1

print(f"\n{'=' * 70}")
print(f"TEST RESULTS: {passed}/{len(test_cases)} passed, {failed}/{len(test_cases)} failed")
print("=" * 70)
