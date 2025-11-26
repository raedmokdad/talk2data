import re
from typing import Dict, Any

class SQLValidator:
    """Validates SQL queries and returns error messages"""
    
    def __init__(self, schema: Dict[str,Any] = None):
        self.schema = schema  # Optional - only used for security checks
        
        self.pattern_labels = {
            r";\s*(DROP|DELETE|UPDATE|ALTER|INSERT)": 
                "Command chaining with destructive SQL",

            r"--": 
                "Inline SQL comment (possible injection)",

            r"/\*[\s\S]*?\*/": 
                "Block SQL comment (possible injection)",

            r"\bUNION\s+SELECT\b": 
                "UNION-based SQL injection attempt",

            r"\bOR\s+1\s*=\s*1\b": 
                "Boolean-based SQL injection (OR 1=1)",

            r"\bEXEC\b": 
                "EXEC call detected (dangerous procedure execution)",

            r";\s*EXEC\b": 
                "Command chaining with EXEC (dangerous)",

            r"\bxp_": 
                "Extended stored procedure call (SQL Server attack)",

            r"\bINFORMATION_SCHEMA\b": 
                "Schema enumeration attempt (probing metadata)",

            r"\bCAST\s*\(": 
                "CAST() function detected (possible injection chain)",

            r"\bCONVERT\s*\(": 
                "CONVERT() function detected (possible injection chain)",

        
        }
        
        self.forbidden_commands = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
            "MERGE", "REPLACE", "EXEC", "CALL", "GRANT", "REVOKE"
        ]
        
        self.allowed_functions = [
            "SUM", "AVG", "COUNT", "MIN", "MAX",
            "DATE", "DATE_TRUNC", "COALESCE", "YEAR", "MONTH"
        ]
        
    # -------------------------
    # Checks 
    #------------------------
    
    def _check_forbidden_commands(self, sql: str):
            """ Check for forbidden commands in sql and return Error if one is found"""
            pattern = r"\b(" + "|".join(self.forbidden_commands)+r")\b"
            match = re.search(pattern ,sql, re.IGNORECASE)
            if match:
                forbidden_command = match.group(1).upper()
                error_message = f"Forbidden SQL operation detected: {forbidden_command}"
                return False, error_message, forbidden_command
            return True, "OK", None
        
    def _check_dangerous_pattern(self, sql):
            """ Check for dangerous patterns in SQL and return Error if one is found"""
            for pattern, label in self.pattern_labels.items():
               if re.search(pattern ,sql, re.IGNORECASE):
                    return False, label, pattern
            return True, "OK", None
        
    def _check_limit(self, sql: str):
            """ Ensure that query includes LIMIT Clause"""
            if 'LIMIT' not in sql.upper():
                return False, "Query must contain a Limit Clause", None
            return True, "OK", None
        
    def _check_functions(self, sql):
            """
                Finds all functions used in the query and checks if they are in the allowed list.
            """
            potential_functions = re.findall(r'\b([a-zA-Z_]+)\s*\(', sql, re.IGNORECASE)
            if not potential_functions:
                return True, "OK", None
            for func in potential_functions:
                if func.upper() not in self.allowed_functions:
                    error_message = f"Forbidden SQL function detected: {func}"
                    return False, error_message, func 
            return True, "OK", None
        
    def _check_schema_lock(self, sql):
            """ Check if query references table name"""
            #if self.table not in sql:
            # #   error_message = f"Query must reference table {self.table}"
            #    return False, error_message, None
            return True, "OK", None
        
    def _check_basic_syntax(self, sql):
            """ Check if query starts with SELECT"""
            if not sql.strip().upper().startswith("SELECT"):
                error_message = f"Query must start with SELECT"
                return False, error_message, None
            return True, "OK", None
        
    # Error  Message
    def _fail(self, code, message, invalid_token,sql) -> Dict[str,Any]:
            return {
                "ok": False,
                "error_code": code,
                "error_message": message,
                "invalid_token": invalid_token,
                "sql": sql,
                "fixed": False
            }
        
    #---------------------------
    # Validation
    #----------------------
    def validate(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query and collect ALL errors for comprehensive feedback
        
        Returns:
            Dict with validation result. If errors found, includes all violations.
        """
        errors = []
        
        # Run all checks and collect errors
        ok, msg, token = self._check_forbidden_commands(sql)
        if not ok:
            errors.append(f"Security violation: {msg}")
        
        ok, msg, token = self._check_dangerous_pattern(sql)
        if not ok:
            errors.append(f"Injection risk: {msg}")
        
       # ok, msg, token = self._check_schema_lock(sql)
       # if not ok:
       #     errors.append(f"Schema violation: {msg}")
        
        ok, msg, token = self._check_functions(sql)
        if not ok:
            errors.append(f"Function restriction: {msg}")
        
        # LIMIT check disabled for multi-table queries (may have subqueries)
        # ok, msg, token = self._check_limit(sql)
        # if not ok:
        #     errors.append(f"Missing requirement: {msg}")
        
        ok, msg, token = self._check_basic_syntax(sql)
        if not ok:
            errors.append(f"Syntax error: {msg}")
        
        # If any errors found, return combined feedback
        if errors:
            combined_message = "; ".join(errors)
            return self._fail("MULTIPLE_VIOLATIONS", combined_message, None, sql)
        
        # All checks passed
        return {
            "ok": True,
            "error_code": None,
            "error_message": None,
            "invalid_token": None,
            "sql": sql,
            "fixed": False
        }
