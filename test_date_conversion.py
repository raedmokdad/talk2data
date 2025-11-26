"""
Test: Date Conversion in SQL Generation
Verifies that the system automatically converts German dates to ISO format.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm_sql_generator import generate_multi_table_sql
from src.sql_validator import SQLValidator
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

def test_date_conversion():
    """Test that German dates are converted to ISO format in SQL"""
    
    validator = None  # Not needed for this test
    
    test_cases = [
        {
            "question": "Wie viel Umsatz am 15. Januar 2023?",
            "expected_date": "2023-01-15",
            "description": "German date format: DD. Month YYYY"
        },
        {
            "question": "Verkäufe am 01.03.2023",
            "expected_date": "2023-03-01",
            "description": "German date format: DD.MM.YYYY"
        },
        {
            "question": "Umsatz im Januar 2023",
            "expected_date": "2023-01",
            "description": "Month and year only"
        },
        {
            "question": "Was war der Umsatz am 25 Dezember 2023?",
            "expected_date": "2023-12-25",
            "description": "German date without period"
        }
    ]
    
    print("=" * 80)
    print("DATE CONVERSION TEST")
    print("=" * 80)
    print("\nTesting automatic date conversion from German to ISO format...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Question: {test['question']}")
        print(f"Expected date in SQL: {test['expected_date']}")
        
        try:
            sql = generate_multi_table_sql(test['question'], "retial_star_schema", validator)
            
            # Check if expected date appears in SQL
            if test['expected_date'] in sql:
                print(f"✅ PASSED - ISO date found in SQL")
                print(f"Generated SQL:\n{sql}\n")
            else:
                print(f"❌ FAILED - Expected date '{test['expected_date']}' not found in SQL")
                print(f"Generated SQL:\n{sql}\n")
                
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
        
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_date_conversion()
