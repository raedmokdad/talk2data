from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import json
import pathlib
import logging
from src.llm_table_selector import select_tables

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

@dataclass
class TableRelationship:
    """ A relationship between 2 tables"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    join_type: str = "LEFT JOIN"
    description: str = ""
    
    def to_sql_join(self, from_alias: str = None, to_alias:str=None):
        """ Generate Join """
        from_table = from_alias if from_alias else self.from_table
        to_table = to_alias if to_alias else self.to_table
        return f"{self.join_type}  {to_table} ON {from_table}.{self.from_column} = {to_table}.{self.to_column}"
    
@dataclass
class JoinPath:
    """ Generate Join between multiple tables"""
    tables: List[str] = field(default_factory=list)
    relationships: List[TableRelationship] = field(default_factory=list)
    total_cost: int = 0
    
    def to_sql(self):
        
        """Generate complete SQL JOIN chain"""
        if not self.relationships:
            return ""
        return "\n".join([rel.to_sql_join() for rel in self.relationships])
    
    
class SchemaParser:
    """ PArses Starschema and manages table realtionships"""
    
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        self.schema_data : Optional[Dict] = None
        self.relationships: List[TableRelationship] = []
        self.synonyms: Dict = {}
        self.kpis: Dict = {}
        self.tables: Dict = {}
        self.notes: List[str] = []
        self.examples: List[Dict] = []
        self.glossary: Dict = {}
        
        
    def load_star_schema(self) -> Dict:
        if self.schema_data is not None:
            return self.schema_data
        
        script_dir = pathlib.Path(__file__).parent
        schema_file = f"{self.schema_name}.json"
        path = script_dir / "config" / schema_file
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.schema_data = json.loads(f.read())
                self._parse_tables()
                self._parse_relationships()
                self._parse_synonyms()
                self._parse_kpis()
                self._parse_notes()        
                self._parse_examples()     
                self._parse_glossary()
                logger.info(f"Loaded schema: {schema_file}")
                return self.schema_data
        except FileNotFoundError:
            logger.error(f"Schema file not found: {path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise
        
    def _parse_tables(self):
        """ get tables """
        if not self.schema_data:
            return
        
        # Check for star schema format (multiple tables)
        tables_list = self.schema_data.get("schema", {}).get("tables", [])
        if tables_list:
            for table in tables_list:
                self.tables[table["name"]] = table
        
        # Check for single-table format
        elif "table" in self.schema_data:
            table_name = self.schema_data.get("table")
            self.tables[table_name] = {
                "name": table_name,
                "role": "table",
                "grain": "one row per record",
                "columns": self.schema_data.get("columns", {}),
                "notes": self.schema_data.get("notes", [])
            }
            
            
    def _parse_notes(self):
        if not self.schema_data:
            return
        self.notes = self.schema_data.get("schema", {}).get("notes", [])
        
    def _parse_synonyms(self):
        if not self.schema_data:
            return
        self.synonyms = self.schema_data.get("synonyms", {})
        
    def _parse_kpis(self):
        if not self.schema_data:
            return
        self.kpis = self.schema_data.get("kpis", {})
        
    def _parse_examples(self):
        if not self.schema_data:
            return
        self.examples = self.schema_data.get("examples", [])
        
    def _parse_glossary(self):
        if not self.schema_data:
            return
        self.glossary = self.schema_data.get("glossary", {})
        
        
    def _parse_relationships(self):
        if not self.schema_data:
            return
        
        relations_list = self.schema_data.get("schema", {}).get("relationships",[])
        
        for rel in relations_list:
            from_info = rel.get("from", "").split(".")
            to_info = rel.get("to","").split(".")
            join_type = rel.get("join_type", "LEFT JOIN")
            description = rel.get("description", "")  
            if len(from_info) !=2 or len(to_info) !=2:
                logger.warning(f"Invalid relationship format: {rel}")
                continue
            
            relationship = TableRelationship(
                from_table= from_info[0],
                from_column= from_info[1],
                to_table= to_info[0],
                to_column= to_info[1],
                join_type= join_type,
                description= description
            )
            
            self.relationships.append(relationship) 
            
            
    def _find_fact_table(self, tables: List[str]) -> Optional[str]:
        for table in tables:
            if table.startswith("fact_"):
                return table
            table_ref = self.tables.get(table, {})
            if table_ref.get("role") == "fact":
                return table
        return None
    
    
    def _find_relationship(self, connected_tables: Set[str], target_table: str) -> Optional[TableRelationship]:

        for rel in self.relationships:
            if rel.from_table in connected_tables  and rel.to_table == target_table:
                return rel
            

            if rel.to_table in connected_tables and rel.from_table == target_table:
                return TableRelationship(
                    from_table=rel.to_table,
                    from_column=rel.to_column,
                    to_table=rel.from_table,
                    to_column=rel.from_column,
                    join_type="INNER JOIN",
                    description=rel.description
                )
        return None
    
    
    def find_join_path(self, required_tables: List[str]) -> Optional[JoinPath]:
        """ Find the best joins between tables"""
        if not required_tables:
            return None
        
        start_table = self._find_fact_table(required_tables)
        if not start_table:
            start_table = required_tables[0]
        
        
        remaining_tables = [table for table in required_tables if table != start_table]  
        connected_tables: Set[str] = {start_table}  
        join_path = JoinPath(tables = [start_table], relationships=[])
        
        if not remaining_tables:
            return join_path
        
        while remaining_tables:
            found_connection = False
            for target in remaining_tables[:]:
                rel = self._find_relationship(connected_tables,target)
                if rel:
                    join_path.relationships.append(rel)
                    join_path.tables.append(target)
                    connected_tables.add(target)
                    remaining_tables.remove(target)
                    found_connection = True
                    break
                
            if not found_connection:
                return None
        return join_path
    
    
    def validate_selected_tables(self, selected_tables: List[str]) -> Tuple[bool, str]:
        """
        Validates if all selected tables exist in the schema.
        For flat tables (single table schemas), validation is skipped since actual DB table name may differ.
        """
        if not selected_tables:
            return False, "No tables were selected for the query"
        
        # For flat tables with single table, skip validation
        if len(self.tables) == 1:
            return True, ""
        
        missing_tables = [t for t in selected_tables if t not in self.tables]
        
        if missing_tables:
            available_tables = ", ".join(self.tables.keys())
            missing = ", ".join(missing_tables)
            return False, f"Cannot generate query: Tables '{missing}' do not exist in schema. Available tables: {available_tables}"
        
        return True, ""
    
    def validate_sql_columns(self, sql_query: str) -> Tuple[bool, str]:
        """
        Validates if columns used in SQL exist in the schema.
        """
        import re
        
        # Extract table.column references (e.g., dim_product.sku, fact_sales.sales_amount)
        column_pattern = r'(\w+)\.(\w+)'
        matches = re.findall(column_pattern, sql_query)
        
        invalid_columns = []
        
        for table_name, column_name in matches:
          
            if table_name.upper() in ['SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER']:
                continue
            
          
            if table_name not in self.tables:
                continue  # Table validation is done elsewhere
            
          
            table_columns = self.tables[table_name].get('columns', {})
            if column_name not in table_columns:
                invalid_columns.append(f"{table_name}.{column_name}")
        
        if invalid_columns:
            invalid_str = ", ".join(invalid_columns)
            
            available_info = []
            for table_name in set(m[0] for m in matches if m[0] in self.tables):
                cols = list(self.tables[table_name].get('columns', {}).keys())
                available_info.append(f"{table_name}: {', '.join(cols[:5])}...")
            
            available_str = "; ".join(available_info)
            return False, f"Invalid columns in query: {invalid_str}. Check available columns: {available_str}"
        
        return True, ""
    
  
    def get_relevant_tables(self, question: str, actual_table_names: List[str] = None) -> List[str]:
        """
        Uses LLM to identify which tables are needed to answer the question.
        For flat tables (single CSV), uses actual_table_names from database instead of schema names.
        If LLM return no valid values -> raise error
        """
        # For flat tables with single table, use actual DB table name
        if len(self.tables) == 1 and actual_table_names:
            return actual_table_names
        
        schema_summary = self.get_schema_summary()
        tables = select_tables(question, schema_summary)
        

        valid_tables = [t for t in tables if t in self.tables]
        invalid_tables = [t for t in tables if t not in self.tables]
        
        if invalid_tables:
            logger.warning(f"LLM suggested non-existent tables: {invalid_tables}")
        
        if not valid_tables:
            available_tables = ", ".join(self.tables.keys())
            raise ValueError(f"Cannot answer question: No matching tables found in schema. The question may require data not available in this schema. Available tables: {available_tables}")
        
        return valid_tables
    
    
    def get_schema_summary(self) -> str:
        """
        Creates a schema description for LLM prompts.
        """
        summary = []
        for k,v in self.tables.items():
            role = v.get("role", "")
            grain = v.get("grain", "")
            cols = v.get("columns", {})
            
            table_line = f"Table: {k} ({role})"
            grain_line = f"- Grain: {grain}"
            
            column_names = list(cols.keys())
            columns_line = f"- Columns: {', '.join(column_names)}"
            
            summary.append(f"{table_line}\n{grain_line}\n{columns_line}\n")
        
        
        return "\n".join(summary)
    
    def get_kpis_summary(self) -> str:
        """
        Creates KPI definitions for LLM prompts.
        """
        if not self.kpis:
            return ""
        
        kpi_lines = []
        for kpi_name, kpi_def in self.kpis.items():
            formula = kpi_def.get("formula", "")
            desc = kpi_def.get("description", "")
            keywords = kpi_def.get("keywords", [])
            
            kpi_line = f"- {kpi_name}: {formula}"
            if desc:
                kpi_line += f" ({desc})"
            if keywords:
                kpi_line += f" [Keywords: {', '.join(keywords)}]"
            
            kpi_lines.append(kpi_line)
        
        return "Available KPIs:\n" + "\n".join(kpi_lines) if kpi_lines else ""
    
    def get_synonyms_summary(self) -> str:
        """
        Creates synonym/glossary definitions for LLM prompts.
        """
        if not self.synonyms:
            return ""
        
        syn_lines = []
        for term, mapping in list(self.synonyms.items())[:10]:
            col = mapping.get("column", "")
            table = mapping.get("table", "")
            syn_lines.append(f"- '{term}' → {table}.{col}")
        
        return "Term Glossary:\n" + "\n".join(syn_lines) if syn_lines else ""




 


def get_schema_parser(schema_name: str = "retial_star_schema") -> SchemaParser:
    """
    Returns a new instance of SchemaParser
    """

    parser = SchemaParser(schema_name)
    parser.load_star_schema()
    
    return parser


def get_schema_parser_from_data(schema_data: Dict) -> SchemaParser:
    """ Create SchemaParser from Dictionary """
    schema_name = schema_data.get("name", "user_schema")
    parser = SchemaParser(schema_name)
    parser.schema_data = schema_data
    
    parser._parse_tables()
    parser._parse_relationships()
    parser._parse_synonyms()
    parser._parse_kpis()
    parser._parse_notes()
    parser._parse_examples()
    parser._parse_glossary()
    logger.info(f"Loaded schema from dict: {schema_name}")
    return parser
                    
            
        
        
        
                                                     
        
        
        