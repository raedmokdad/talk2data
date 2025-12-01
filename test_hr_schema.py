import unittest
import logging
from src.llm_sql_generator import generate_multi_table_sql

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestHRSchema(unittest.TestCase):
    """
    Tests for the HR Schema to verify the generalized prompt works across domains.
    """

    def setUp(self):
        self.schema_name = "hr_schema"

    def test_01_simple_join(self):
        """Test: Total hours worked by department IT in 2024"""
        question = "Show me total hours worked by department IT in 2024"
        print(f"\nTest 1: {question}")
        
        try:
            sql = generate_multi_table_sql(question, schema_name=self.schema_name)
            print(f"Generated SQL:\n{sql}")
            
            self.assertIn("SUM(fact_employee_daily.hours_worked)", sql)
            self.assertIn("dim_department", sql)
            self.assertIn("IT", sql)
            self.assertIn("2024", sql)
            
        except Exception as e:
            self.fail(f"SQL generation failed: {e}")

    def test_02_kpi_usage(self):
        """Test: Who is the most productive employee?"""
        question = "Who is the most productive employee?"
        print(f"\nTest 2: {question}")
        
        try:
            sql = generate_multi_table_sql(question, schema_name=self.schema_name)
            print(f"Generated SQL:\n{sql}")
            
            # Should use the productivity formula: tasks / hours
            self.assertIn("SUM(fact_employee_daily.tasks_completed)", sql)
            self.assertIn("SUM(fact_employee_daily.hours_worked)", sql)
            self.assertIn("ORDER BY", sql)
            
        except Exception as e:
            self.fail(f"SQL generation failed: {e}")

    def test_03_filter_value(self):
        """Test: Show hours worked by employees in department 'Finance'"""
        question = "Show hours worked by employees in department 'Finance'"
        print(f"\nTest 3: {question}")
        
        try:
            sql = generate_multi_table_sql(question, schema_name=self.schema_name)
            print(f"Generated SQL:\n{sql}")
            
            self.assertIn("dim_department.department_name", sql)
            self.assertIn("'Finance'", sql)
            self.assertIn("fact_employee_daily", sql)
            
        except Exception as e:
            self.fail(f"SQL generation failed: {e}")

    def test_04_missing_retail_concept(self):
        """Test: Show me the sales revenue (Should Fail)"""
        question = "Show me the sales revenue"
        print(f"\nTest 4: {question}")
        
        try:
            sql = generate_multi_table_sql(question, schema_name=self.schema_name)
            print(f"Generated SQL: {sql}")
            self.fail("Should have raised ValueError for missing data")
        except ValueError as e:
            print(f"Caught expected error: {e}")
            self.assertTrue("Required data not available" in str(e) or "No matching tables" in str(e))

    def test_05_missing_inventory_concept(self):
        """Test: What is the inventory level? (Should Fail)"""
        question = "What is the inventory level?"
        print(f"\nTest 5: {question}")
        
        try:
            sql = generate_multi_table_sql(question, schema_name=self.schema_name)
            print(f"Generated SQL: {sql}")
            self.fail("Should have raised ValueError for missing data")
        except ValueError as e:
            print(f"Caught expected error: {e}")
            self.assertTrue("Required data not available" in str(e) or "No matching tables" in str(e))

    def test_06_kpi_and_filter(self):
        """Test: Show me the absenteeism rate for employee E123"""
        question = "Show me the absenteeism rate for employee E123"
        print(f"\nTest 6: {question}")
        
        try:
            sql = generate_multi_table_sql(question, schema_name=self.schema_name)
            print(f"Generated SQL:\n{sql}")
            
            # Should use absenteeism formula
            self.assertIn("is_absent", sql)
            self.assertIn("E123", sql)
            
        except Exception as e:
            self.fail(f"SQL generation failed: {e}")

if __name__ == '__main__':
    unittest.main()
