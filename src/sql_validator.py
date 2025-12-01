import re
from typing import Dict, Any

class SQLValidator:
    
    def __init__(self, schema: Dict[str,Any] = None):
        self.schema = schema  
        
        self.pattern_labels = {
            r";\s*(DROP|DELETE|UPDATE|ALTER|INSERT)": 
                "Command chaining with destructive SQL",

            r"--\s": 
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

        
        }
        
        self.forbidden_commands = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
            "MERGE", "EXEC", "CALL", "GRANT", "REVOKE"
        ]
        
        self.allowed_functions = [
            "SUM", "AVG", "COUNT", "MIN", "MAX",
            "DATE", "DATE_TRUNC", "YEAR", "MONTH", "DAY", "NOW", "CURRENT_DATE", "DATEDIFF", "DATE_ADD", "DATE_SUB",
            "UPPER", "LOWER", "SUBSTR", "LENGTH", "TRIM", "CONCAT", "REPLACE", "LEFT", "RIGHT",         
            "ROUND", "ABS", "CEIL", "FLOOR", "COALESCE", "IFNULL", "NULLIF",
            "CAST", "CONVERT"
        ]
        
   
    
    def _check_forbidden_commands(self, sql: str):

            pattern = r"\b(" + "|".join(self.forbidden_commands)+r")\b"
            match = re.search(pattern ,sql, re.IGNORECASE)
            if match:
                forbidden_command = match.group(1).upper()
                error_message = f"Forbidden SQL operation detected: {forbidden_command}"
                return False, error_message, forbidden_command
            return True, "OK", None
        
    def _check_dangerous_pattern(self, sql):
 
            for pattern, label in self.pattern_labels.items():
               if re.search(pattern ,sql, re.IGNORECASE):
                    return False, label, pattern
            return True, "OK", None
        
    def _check_limit(self, sql: str):
            """Check if LIMIT clause is present, but skip for aggregate queries"""
            sql_upper = sql.upper()
            
            # Remove extra spaces and normalize
            sql_normalized = ' '.join(sql_upper.split())
            
            # Skip LIMIT check for queries with aggregation functions (with or without spaces)
            aggregation_patterns = [
                r'SUM\s*\(',
                r'COUNT\s*\(',
                r'AVG\s*\(',
                r'MIN\s*\(',
                r'MAX\s*\(',
                r'GROUP\s+BY',
                r'HAVING\s+',
                r'DISTINCT\s+COUNT',
            ]
            
            has_aggregation = any(re.search(pattern, sql_normalized) for pattern in aggregation_patterns)
            
            # If query has aggregation, LIMIT is optional
            if has_aggregation:
                return True, "OK", None
            
            # For regular SELECT queries, require LIMIT
            if 'LIMIT' not in sql_upper:
                return False, "Query must contain a Limit Clause", None
            return True, "OK", None
        
    def _check_functions(self, sql):


            ignored_keywords = {"IN", "AND", "OR", "NOT", "LIKE", "AS", "VALUES", "FROM", "JOIN"}

            potential_functions = re.findall(r'\b([a-zA-Z_]+)\s*\(', sql, re.IGNORECASE)
            if not potential_functions:
                return True, "OK", None
            for func in potential_functions:
                if func.upper() in ignored_keywords:
                    continue

                if func.upper() not in self.allowed_functions:
                    error_message = f"Forbidden SQL function detected: {func}"
                    return False, error_message, func 
            return True, "OK", None
        
    def _check_schema_lock(self, sql):
            return True, "OK", None
        
    def _check_basic_syntax(self, sql):
            sql_upper = sql.strip().upper()
            if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
                error_message = f"Query must start with SELECT or WITH"
                return False, error_message, None
            return True, "OK", None
        

    def _fail(self, code, message, invalid_token,sql) -> Dict[str,Any]:
            return {
                "ok": False,
                "error_code": code,
                "error_message": message,
                "invalid_token": invalid_token,
                "sql": sql,
                "fixed": False
            }
        

    def validate(self, sql: str) -> Dict[str, Any]:

        errors = []
        

        ok, msg, token = self._check_forbidden_commands(sql)
        if not ok:
            errors.append(f"Security violation: {msg}")
        
        ok, msg, token = self._check_dangerous_pattern(sql)
        if not ok:
            errors.append(f"Injection risk: {msg}")
        

        
        ok, msg, token = self._check_functions(sql)
        if not ok:
            errors.append(f"Function restriction: {msg}")
        

        ok, msg, token = self._check_limit(sql)
        if not ok:
            errors.append(f"Missing requirement: {msg}")
        
        ok, msg, token = self._check_basic_syntax(sql)
        if not ok:
            errors.append(f"Syntax error: {msg}")
        

        if errors:
            combined_message = "; ".join(errors)
            return self._fail("MULTIPLE_VIOLATIONS", combined_message, None, sql)
        

        return {
            "ok": True,
            "error_code": None,
            "error_message": None,
            "invalid_token": None,
            "sql": sql,
            "fixed": False
        }
