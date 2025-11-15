import unittest
import sys
from pathlib import Path

from sql_validator import SQLValidator


class TestSQLValidator(unittest.TestCase):
    def setUp(self):
        self.test_schema = {
            "table": "test_table",
            "columns": {
                "id": "INTEGER",
                "name": "TEXT",
                "value": "DECIMAL"
            }
        }
        self.validator = SQLValidator(self.test_schema)
        
    
    def test_valid_query(self):
        sql = "SELECT id, name FROM test_table LIMIT 10"
        result = self.validator.validate(sql)
        self.assertTrue(result["ok"])
        
    def test_missing_limit(self):
        sql = "SELECT id, name FROM test_table"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # Check that either single error or multiple violations detected
        if result["error_code"] == "MULTIPLE_VIOLATIONS":
            self.assertIn("Query must contain a Limit Clause", result["error_message"])
        else:
            self.assertEqual(result["error_code"], "MISSING_LIMIT")
        
    def test_union_injection(self):
        sql = "SELECT name FROM test_table UNION SELECT password FROM users LIMIT 10;"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # Check that either single error or multiple violations detected
        if result["error_code"] == "MULTIPLE_VIOLATIONS":
            self.assertIn("UNION-based SQL injection", result["error_message"])
        else:
            self.assertEqual(result["error_code"], "DANGEROUS_PATTERN")
        
    def test_forbidden_delete(self):
        sql = "DELETE FROM test_table;"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # Check that either single error or multiple violations detected
        if result["error_code"] == "MULTIPLE_VIOLATIONS":
            self.assertIn("Security violation", result["error_message"])
        else:
            self.assertEqual(result["error_code"], "FORBIDDEN_COMMAND")
        
    def test_forbidden_function(self):
        sql = "SELECT id, SUBSTRING(name, 1, 5) FROM test_table LIMIT 10"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # Check that either single error or multiple violations detected
        if result["error_code"] == "MULTIPLE_VIOLATIONS":
            self.assertIn("Function restriction", result["error_message"])
        else:
            self.assertEqual(result["error_code"], "FORBIDDEN_FUNCTION")
        
    def test_wrong_table(self):
        sql = "SELECT id  FROM wrong_table LIMIT 10"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # Check that either single error or multiple violations detected  
        if result["error_code"] == "MULTIPLE_VIOLATIONS":
            self.assertIn("Schema violation", result["error_message"])
        else:
            self.assertEqual(result["error_code"], "SCHEMA_VIOLATION")
        
    def test_case_insensitive_forbidden_command(self):
        sql = "dElEtE fRoM test_table LIMIT 5"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # Check that either single error or multiple violations detected
        if result["error_code"] == "MULTIPLE_VIOLATIONS":
            self.assertIn("Security violation", result["error_message"])
        else:
            self.assertEqual(result["error_code"], "FORBIDDEN_COMMAND")
        
    
    def test_complex_injection_with_comments(self):
        sql = "SELECT id FROM test_table WHERE name = ''; /* OR 1=1 */ -- LIMIT 10"
        result = self.validator.validate(sql)
        self.assertFalse(result["ok"])
        # This SQL has multiple violations, so it should return MULTIPLE_VIOLATIONS
        self.assertEqual(result["error_code"], "MULTIPLE_VIOLATIONS")
        # Check the error contains comment-related violations
        error_msg = result["error_message"]
        self.assertTrue(
            "comment" in error_msg.lower() or "injection" in error_msg.lower(),
            f"Expected comment or injection error, got: {error_msg}"
        )
    
    
if __name__ == '__main__':
    unittest.main()