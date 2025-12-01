import unittest
import logging
from src.llm_sql_generator import generate_multi_table_sql

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class TestAllSchemas(unittest.TestCase):
    """
    Comprehensive test suite for all 10 schemas with 10 questions each (100 total).
    Questions range from simple to complex.
    """

    # ========== RETAIL STAR SCHEMA ==========
    def test_retail_01_simple(self):
        """RT1: Total sales in 2015"""
        sql = generate_multi_table_sql("Show total sales in 2015", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)
        self.assertIn("fact_sales", sql)

    def test_retail_02_filter(self):
        """RT2: Sales in Berlin stores"""
        sql = generate_multi_table_sql("Show sales in Berlin stores", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_store", sql)

    def test_retail_03_kpi(self):
        """RT3: Net sales"""
        sql = generate_multi_table_sql("What is the net sales?", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)

    def test_retail_04_aggregation(self):
        """RT4: Sales by product category"""
        sql = generate_multi_table_sql("Show sales by product category", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_product", sql)

    def test_retail_05_join(self):
        """RT5: Discount amount by store region"""
        sql = generate_multi_table_sql("Show discount amount by store region", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)

    def test_retail_06_kpi_complex(self):
        """RT6: Return rate by store type"""
        sql = generate_multi_table_sql("What is the return rate by store type?", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)

    def test_retail_07_filter_value(self):
        """RT7: Sales for product SKU XYZ789"""
        sql = generate_multi_table_sql("Show sales for product SKU XYZ789", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)

    def test_retail_08_complex(self):
        """RT8: Monthly sales trend by region"""
        sql = generate_multi_table_sql("Show monthly sales trend by region", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)

    def test_retail_09_missing_data(self):
        """RT9: Should fail - asking for customer data"""
        try:
            sql = generate_multi_table_sql("Show customer purchase history", schema_name="retial_star_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_retail_10_complex_join(self):
        """RT10: Average discount rate by store and quarter"""
        sql = generate_multi_table_sql("Average discount rate by store and quarter", schema_name="retial_star_schema")
        self.assertIsNotNone(sql)

    # ========== HEALTHCARE SCHEMA ==========
    def test_healthcare_01_simple(self):
        """HC1: Total visits in 2024"""
        sql = generate_multi_table_sql("Show total patient visits in 2024", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)
        self.assertIn("fact_patient_visit", sql)

    def test_healthcare_02_filter(self):
        """HC2: Visits in Cardiology department"""
        sql = generate_multi_table_sql("How many visits in Cardiology department?", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_department", sql)

    def test_healthcare_03_kpi(self):
        """HC3: Average visit cost"""
        sql = generate_multi_table_sql("What is the average visit cost?", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)

    def test_healthcare_04_join(self):
        """HC4: Emergency visits by doctor specialty"""
        sql = generate_multi_table_sql("Show emergency visits by doctor specialty", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_doctor", sql)

    def test_healthcare_05_aggregation(self):
        """HC5: Monthly treatment costs"""
        sql = generate_multi_table_sql("Show monthly treatment costs", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)

    def test_healthcare_06_complex(self):
        """HC6: Top 5 doctors by patient count"""
        sql = generate_multi_table_sql("Who are the top 5 doctors by patient count?", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)
        self.assertIn("LIMIT", sql.upper())

    def test_healthcare_07_filter_value(self):
        """HC7: Visits for patient P12345"""
        sql = generate_multi_table_sql("Show visits for patient P12345", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)

    def test_healthcare_08_kpi_complex(self):
        """HC8: Emergency rate by department"""
        sql = generate_multi_table_sql("What is the emergency rate by department?", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)

    def test_healthcare_09_missing_data(self):
        """HC9: Should fail - asking for profit"""
        try:
            sql = generate_multi_table_sql("Show me profit by department", schema_name="healthcare_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_healthcare_10_complex_join(self):
        """HC10: Average visit duration by doctor and insurance type"""
        sql = generate_multi_table_sql("Average visit duration by doctor and insurance type", schema_name="healthcare_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_patient", sql)

    # ========== E-COMMERCE SCHEMA ==========
    def test_ecommerce_01_simple(self):
        """EC1: Total orders in 2024"""
        sql = generate_multi_table_sql("Show total orders in 2024", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    def test_ecommerce_02_filter(self):
        """EC2: Orders from Germany"""
        sql = generate_multi_table_sql("How many orders from Germany?", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_customer", sql)

    def test_ecommerce_03_kpi(self):
        """EC3: Net revenue"""
        sql = generate_multi_table_sql("What is the net revenue?", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    def test_ecommerce_04_aggregation(self):
        """EC4: Sales by product category"""
        sql = generate_multi_table_sql("Show sales by product category", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)
        self.assertIn("dim_product", sql)

    def test_ecommerce_05_join(self):
        """EC5: Orders with PayPal payment"""
        sql = generate_multi_table_sql("Show orders paid with PayPal", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    def test_ecommerce_06_kpi_complex(self):
        """EC6: Return rate by brand"""
        sql = generate_multi_table_sql("What is the return rate by brand?", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    def test_ecommerce_07_filter_value(self):
        """EC7: Orders for customer C98765"""
        sql = generate_multi_table_sql("Show orders for customer C98765", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    def test_ecommerce_08_complex(self):
        """EC8: Top 10 products by revenue"""
        sql = generate_multi_table_sql("Top 10 products by revenue", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    def test_ecommerce_09_missing_data(self):
        """EC9: Should fail - asking for inventory"""
        try:
            sql = generate_multi_table_sql("Show inventory levels", schema_name="ecommerce_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_ecommerce_10_complex_join(self):
        """EC10: Average order value by loyalty tier and quarter"""
        sql = generate_multi_table_sql("Average order value by loyalty tier and quarter", schema_name="ecommerce_schema")
        self.assertIsNotNone(sql)

    # ========== MANUFACTURING SCHEMA ==========
    def test_manufacturing_01_simple(self):
        """MF1: Total units produced"""
        sql = generate_multi_table_sql("Show total units produced", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_02_filter(self):
        """MF2: Production on machine M001"""
        sql = generate_multi_table_sql("Show production on machine M001", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_03_kpi(self):
        """MF3: Defect rate"""
        sql = generate_multi_table_sql("What is the defect rate?", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_04_aggregation(self):
        """MF4: Production by shift"""
        sql = generate_multi_table_sql("Show production by shift", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_05_join(self):
        """MF5: Defective units by product line"""
        sql = generate_multi_table_sql("Show defective units by product line", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_06_kpi_complex(self):
        """MF6: Efficiency by machine type"""
        sql = generate_multi_table_sql("What is the efficiency by machine type?", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_07_filter_value(self):
        """MF7: Production during night shift"""
        sql = generate_multi_table_sql("Show production during night shift", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_08_complex(self):
        """MF8: Total cost by product and month"""
        sql = generate_multi_table_sql("Total production cost by product and month", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    def test_manufacturing_09_missing_data(self):
        """MF9: Should fail - asking for profit margin"""
        try:
            sql = generate_multi_table_sql("Show profit margin", schema_name="manufacturing_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_manufacturing_10_complex_join(self):
        """MF10: Average production time per unit by machine and week"""
        sql = generate_multi_table_sql("Average production time per unit by machine and week", schema_name="manufacturing_schema")
        self.assertIsNotNone(sql)

    # ========== LOGISTICS SCHEMA ==========
    def test_logistics_01_simple(self):
        """LG1: Total shipments"""
        sql = generate_multi_table_sql("Show total number of shipments", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_02_filter(self):
        """LG2: Shipments to Paris"""
        sql = generate_multi_table_sql("Show shipments to Paris", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_03_kpi(self):
        """LG3: On-time delivery rate"""
        sql = generate_multi_table_sql("What is the on-time delivery rate?", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_04_aggregation(self):
        """LG4: Deliveries by carrier"""
        sql = generate_multi_table_sql("Show deliveries by carrier", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_05_join(self):
        """LG5: Average weight by vehicle type"""
        sql = generate_multi_table_sql("Average shipment weight by vehicle type", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_06_kpi_complex(self):
        """LG6: Cost per km by carrier"""
        sql = generate_multi_table_sql("Cost per kilometer by carrier", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_07_filter_value(self):
        """LG7: Shipments from warehouse W123"""
        sql = generate_multi_table_sql("Show shipments from warehouse W123", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_08_complex(self):
        """LG8: Monthly delivery cost by country"""
        sql = generate_multi_table_sql("Monthly delivery cost by country", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    def test_logistics_09_missing_data(self):
        """LG9: Should fail - asking for customer satisfaction"""
        try:
            sql = generate_multi_table_sql("Show customer satisfaction scores", schema_name="logistics_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_logistics_10_complex_join(self):
        """LG10: Late deliveries by carrier and month"""
        sql = generate_multi_table_sql("Show late deliveries by carrier and month", schema_name="logistics_schema")
        self.assertIsNotNone(sql)

    # ========== FINANCE SCHEMA ==========
    def test_finance_01_simple(self):
        """FN1: Total transactions"""
        sql = generate_multi_table_sql("Show total number of transactions", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_02_filter(self):
        """FN2: Transactions in Q1 2024"""
        sql = generate_multi_table_sql("Show transactions in Q1 2024", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_03_kpi(self):
        """FN3: Total transaction volume"""
        sql = generate_multi_table_sql("What is the total transaction volume?", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_04_aggregation(self):
        """FN4: Transactions by branch"""
        sql = generate_multi_table_sql("Show transactions by branch", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_05_join(self):
        """FN5: Transactions by account type"""
        sql = generate_multi_table_sql("Show transactions by account type", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_06_kpi_complex(self):
        """FN6: Fraud rate by region"""
        sql = generate_multi_table_sql("What is the fraud rate by region?", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_07_filter_value(self):
        """FN7: Transactions for account ACC12345"""
        sql = generate_multi_table_sql("Show transactions for account ACC12345", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_08_complex(self):
        """FN8: Fee revenue by customer segment and quarter"""
        sql = generate_multi_table_sql("Fee revenue by customer segment and quarter", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    def test_finance_09_missing_data(self):
        """FN9: Should fail - asking for profit"""
        try:
            sql = generate_multi_table_sql("Show profit margin", schema_name="finance_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_finance_10_complex_join(self):
        """FN10: Average transaction amount by age group and transaction type"""
        sql = generate_multi_table_sql("Average transaction amount by age group and transaction type", schema_name="finance_schema")
        self.assertIsNotNone(sql)

    # ========== EDUCATION SCHEMA ==========
    def test_education_01_simple(self):
        """ED1: Total enrollments"""
        sql = generate_multi_table_sql("Show total enrollments", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_02_filter(self):
        """ED2: Enrollments in Computer Science"""
        sql = generate_multi_table_sql("Show enrollments in Computer Science department", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_03_kpi(self):
        """ED3: Pass rate"""
        sql = generate_multi_table_sql("What is the overall pass rate?", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_04_aggregation(self):
        """ED4: Students by major"""
        sql = generate_multi_table_sql("Show student count by major", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_05_join(self):
        """ED5: Average grade by instructor"""
        sql = generate_multi_table_sql("Average grade by instructor", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_06_kpi_complex(self):
        """ED6: Pass rate by course"""
        sql = generate_multi_table_sql("Pass rate by course", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_07_filter_value(self):
        """ED7: Grades for student S54321"""
        sql = generate_multi_table_sql("Show grades for student S54321", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_08_complex(self):
        """ED8: Tuition revenue by semester and department"""
        sql = generate_multi_table_sql("Tuition revenue by semester and department", schema_name="education_schema")
        self.assertIsNotNone(sql)

    def test_education_09_missing_data(self):
        """ED9: Should fail - asking for employment rate"""
        try:
            sql = generate_multi_table_sql("Show employment rate after graduation", schema_name="education_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_education_10_complex_join(self):
        """ED10: Average attendance rate by scholarship type and academic year"""
        sql = generate_multi_table_sql("Average attendance rate by scholarship type and academic year", schema_name="education_schema")
        self.assertIsNotNone(sql)

    # ========== TELECOM SCHEMA ==========
    def test_telecom_01_simple(self):
        """TC1: Total calls"""
        sql = generate_multi_table_sql("Show total number of calls", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_02_filter(self):
        """TC2: Calls in January 2024"""
        sql = generate_multi_table_sql("Show calls in January 2024", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_03_kpi(self):
        """TC3: Total revenue"""
        sql = generate_multi_table_sql("What is the total call revenue?", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_04_aggregation(self):
        """TC4: Data usage by plan"""
        sql = generate_multi_table_sql("Show data usage by plan", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_05_join(self):
        """TC5: Calls by tower city"""
        sql = generate_multi_table_sql("Show calls by tower city", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_06_kpi_complex(self):
        """TC6: Roaming rate by contract type"""
        sql = generate_multi_table_sql("Roaming rate by contract type", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_07_filter_value(self):
        """TC7: Calls for customer CUST999"""
        sql = generate_multi_table_sql("Show calls for customer CUST999", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_08_complex(self):
        """TC8: Average call duration by day of week and plan"""
        sql = generate_multi_table_sql("Average call duration by day of week and plan", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    def test_telecom_09_missing_data(self):
        """TC9: Should fail - asking for profit"""
        try:
            sql = generate_multi_table_sql("Show profit by plan", schema_name="telecom_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_telecom_10_complex_join(self):
        """TC10: SMS count by customer contract type and month"""
        sql = generate_multi_table_sql("SMS count by customer contract type and month", schema_name="telecom_schema")
        self.assertIsNotNone(sql)

    # ========== REAL ESTATE SCHEMA ==========
    def test_realestate_01_simple(self):
        """RE1: Total rentals"""
        sql = generate_multi_table_sql("Show total number of rentals", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_02_filter(self):
        """RE2: Rentals in Munich"""
        sql = generate_multi_table_sql("Show rentals in Munich", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_03_kpi(self):
        """RE3: Total revenue"""
        sql = generate_multi_table_sql("What is the total rental revenue?", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_04_aggregation(self):
        """RE4: Rentals by property type"""
        sql = generate_multi_table_sql("Show rentals by property type", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_05_join(self):
        """RE5: Average rent by neighborhood"""
        sql = generate_multi_table_sql("Average rent by neighborhood", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_06_kpi_complex(self):
        """RE6: Renewal rate by property type"""
        sql = generate_multi_table_sql("Lease renewal rate by property type", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_07_filter_value(self):
        """RE7: Rentals for property PROP777"""
        sql = generate_multi_table_sql("Show rentals for property PROP777", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_08_complex(self):
        """RE8: Monthly rent by city and bedrooms"""
        sql = generate_multi_table_sql("Average monthly rent by city and number of bedrooms", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    def test_realestate_09_missing_data(self):
        """RE9: Should fail - asking for maintenance costs"""
        try:
            sql = generate_multi_table_sql("Show maintenance costs", schema_name="realestate_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_realestate_10_complex_join(self):
        """RE10: Security deposits by agent and quarter"""
        sql = generate_multi_table_sql("Total security deposits by agent and quarter", schema_name="realestate_schema")
        self.assertIsNotNone(sql)

    # ========== HOSPITALITY SCHEMA ==========
    def test_hospitality_01_simple(self):
        """HT1: Total bookings"""
        sql = generate_multi_table_sql("Show total number of bookings", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_02_filter(self):
        """HT2: Bookings in Vienna"""
        sql = generate_multi_table_sql("Show bookings in Vienna", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_03_kpi(self):
        """HT3: Total revenue"""
        sql = generate_multi_table_sql("What is the total booking revenue?", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_04_aggregation(self):
        """HT4: Bookings by room type"""
        sql = generate_multi_table_sql("Show bookings by room type", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_05_join(self):
        """HT5: Average stay by hotel star rating"""
        sql = generate_multi_table_sql("Average length of stay by hotel star rating", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_06_kpi_complex(self):
        """HT6: Cancellation rate by guest country"""
        sql = generate_multi_table_sql("Cancellation rate by guest country", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_07_filter_value(self):
        """HT7: Bookings for guest G11111"""
        sql = generate_multi_table_sql("Show bookings for guest G11111", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_08_complex(self):
        """HT8: Room revenue by hotel and month"""
        sql = generate_multi_table_sql("Room revenue by hotel and month", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)

    def test_hospitality_09_missing_data(self):
        """HT9: Should fail - asking for occupancy rate"""
        try:
            sql = generate_multi_table_sql("Show occupancy rate", schema_name="hospitality_schema")
            self.fail("Should have raised ValueError")
        except ValueError:
            pass

    def test_hospitality_10_complex_join(self):
        """HT10: Average discount by loyalty status and holiday periods"""
        sql = generate_multi_table_sql("Average discount by loyalty status during holidays", schema_name="hospitality_schema")
        self.assertIsNotNone(sql)


if __name__ == '__main__':
    # Run tests with summary
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAllSchemas)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Calculate metrics per schema
    schemas = {
        "Retail": 10,
        "Healthcare": 10,
        "E-Commerce": 10,
        "Manufacturing": 10,
        "Logistics": 10,
        "Finance": 10,
        "Education": 10,
        "Telecom": 10,
        "Real Estate": 10,
        "Hospitality": 10
    }
    
    # Calculate metrics
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*70)
    print("SCHEMA-SPECIFIC RESULTS:")
    print("="*70)
    
    # Group results by schema (every 10 tests)
    test_results = []
    for test in result.failures + result.errors:
        test_results.append((test[0].id(), False))
    
    schema_names = list(schemas.keys())
    for idx, schema_name in enumerate(schema_names):
        start = idx * 10
        end = start + 10
        schema_passed = 10  # Default all pass
        
        # Count failures in this range
        for test_id, _ in test_results:
            test_method = test_id.split('.')[-1]
            # Extract test number
            if test_method.startswith('test_'):
                parts = test_method.split('_')
                if len(parts) >= 2:
                    prefix = parts[1]
                    # Match schema prefix
                    expected_prefix = {
                        "Retail": "retail",
                        "Healthcare": "healthcare",
                        "E-Commerce": "ecommerce",
                        "Manufacturing": "manufacturing",
                        "Logistics": "logistics",
                        "Finance": "finance",
                        "Education": "education",
                        "Telecom": "telecom",
                        "Real Estate": "realestate",
                        "Hospitality": "hospitality"
                    }[schema_name]
                    
                    if prefix == expected_prefix:
                        schema_passed -= 1
        
        schema_pct = (schema_passed / 10 * 100)
        print(f"{schema_name:15} : {schema_passed:2}/10 passed ({schema_pct:5.1f}%)")
    
    print("="*70)
    print(f"OVERALL RESULTS: {passed}/{total} passed ({percentage:.1f}%)")
    print("="*70)
