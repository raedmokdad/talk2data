"""
Test script to verify table name handling for flat tables
"""
import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

from schema_parser import get_schema_parser_from_data
from llm_sql_generator import generate_multi_table_sql

# Test 1: Load test_orders schema and check with different table names
print("=" * 60)
print("TEST 1: Schema Parser with actual_table_names")
print("=" * 60)

test_schema = {
    "name": "test_orders",
    "database": "test_orders",
    "schema": {
        "tables": [
            {
                "name": "test_orders",
                "role": "flat",
                "grain": "one row per order",
                "columns": {
                    "order_id": "Unique identifier for the order",
                    "customer_name": "Name of the customer",
                    "product": "Product name",
                    "quantity": "Number of items ordered",
                    "price": "Price per item",
                    "total": "Total order amount",
                    "order_date": "Date when the order was placed"
                }
            }
        ]
    }
}

parser = get_schema_parser_from_data(test_schema)
print(f"Schema has {len(parser.tables)} table(s)")
print(f"Schema table name: {list(parser.tables.keys())[0]}")

# Test with actual table name from DB (like c_users_r)
actual_table_name = "c_users_r"
question = "Wie viele Bestellungen gibt es?"

relevant_tables = parser.get_relevant_tables(question, actual_table_names=[actual_table_name])
print(f"\nQuestion: {question}")
print(f"Actual DB table name: {actual_table_name}")
print(f"Relevant tables returned: {relevant_tables}")
print(f"✅ SUCCESS: Schema parser returns actual DB table name" if relevant_tables == [actual_table_name] else "❌ FAILED")

# Test 2: Validate that single table schemas skip validation
print("\n" + "=" * 60)
print("TEST 2: Validate Selected Tables for flat table")
print("=" * 60)

is_valid, error_msg = parser.validate_selected_tables([actual_table_name])
print(f"Validating table name '{actual_table_name}' against schema with table 'test_orders'")
print(f"Is valid: {is_valid}")
print(f"Error message: {error_msg}")
print(f"✅ SUCCESS: Validation skipped for flat table" if is_valid else "❌ FAILED: Validation should be skipped")

# Test 3: Test with employees schema
print("\n" + "=" * 60)
print("TEST 3: Employees Schema Test")
print("=" * 60)

employees_schema = {
    "name": "employees",
    "database": "employees",
    "schema": {
        "tables": [
            {
                "name": "employees",
                "role": "flat",
                "grain": "one row per employee",
                "columns": {
                    "employee_id": "Unique identifier for employee",
                    "first_name": "Employee's first name",
                    "last_name": "Employee's last name",
                    "department": "Department name",
                    "salary": "Annual salary",
                    "hire_date": "Date when employee was hired"
                }
            }
        ]
    }
}

parser2 = get_schema_parser_from_data(employees_schema)
actual_table_name2 = "c_users_r_employees"
question2 = "Wie viele Mitarbeiter gibt es?"

relevant_tables2 = parser2.get_relevant_tables(question2, actual_table_names=[actual_table_name2])
print(f"Question: {question2}")
print(f"Actual DB table name: {actual_table_name2}")
print(f"Relevant tables returned: {relevant_tables2}")
print(f"✅ SUCCESS" if relevant_tables2 == [actual_table_name2] else "❌ FAILED")

# Test 4: Test without actual_table_names (should use schema name)
print("\n" + "=" * 60)
print("TEST 4: Without actual_table_names (backward compatibility)")
print("=" * 60)

relevant_tables3 = parser.get_relevant_tables(question)
print(f"Question: {question}")
print(f"Relevant tables (no actual_table_names): {relevant_tables3}")
print(f"✅ SUCCESS: Uses schema table name" if relevant_tables3 == ["test_orders"] else "❌ FAILED")

# Test 5: Multi-table schema (star schema) should still validate
print("\n" + "=" * 60)
print("TEST 5: Multi-table schema validation")
print("=" * 60)

star_schema = {
    "name": "sales",
    "database": "sales",
    "schema": {
        "tables": [
            {
                "name": "fact_sales",
                "role": "fact",
                "grain": "one row per sale",
                "columns": {"sale_id": "ID", "amount": "Amount"}
            },
            {
                "name": "dim_product",
                "role": "dimension",
                "grain": "one row per product",
                "columns": {"product_id": "ID", "name": "Name"}
            }
        ]
    }
}

parser3 = get_schema_parser_from_data(star_schema)
is_valid_star, error_star = parser3.validate_selected_tables(["fact_sales", "dim_product"])
print(f"Valid tables in star schema: {is_valid_star}")

is_invalid_star, error_invalid = parser3.validate_selected_tables(["fact_sales", "invalid_table"])
print(f"Invalid table in star schema: {is_invalid_star}")
print(f"Error message: {error_invalid}")
print(f"✅ SUCCESS: Star schema still validates correctly" if is_valid_star and not is_invalid_star else "❌ FAILED")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
