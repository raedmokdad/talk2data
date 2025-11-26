from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import json
import pathlib
import logging
from src.llm_table_selector import select_tables

logger = logging.getLogger(__name__)

@dataclass
class TableRelationship:
    """ A relationship between 2 tables"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    join_type: str = "LEFT JOIN"  # default: left join
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
    
    def __init__(self, schema_name:str):
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
        tables_list = self.schema_data.get("schema", {}).get("tables", {})
        for table in tables_list:
            self.tables[table["name"]] = table
            
            
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
       # forward check
        for rel in self.relationships:
            if rel.from_table in connected_tables  and rel.to_table == target_table:
                return rel
            
        #reverse check
            if rel.to_table in connected_tables and rel.from_table == target_table:
                return TableRelationship(
                    from_table=rel.to_table,
                    from_column=rel.to_column,
                    to_table=rel.from_table,
                    to_column=rel.from_column,
                    join_type=rel.join_type,
                    description=rel.description
                )
        return None
    
    
    def find_join_path(self, required_tables: List[str]) -> Optional[JoinPath]:
        """ Find the best joins between tables"""
        if not required_tables:
            return None
        
        fact_table = self._find_fact_table(required_tables)
        if not fact_table:
            return None
        
        remaining_tables = [table for table in required_tables if table != fact_table]  
        connected_tables: Set[str] = {fact_table}  
        join_path = JoinPath(tables = [fact_table], relationships=[])
        
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
    
    
    def get_relevant_tables(self, question: str) -> List[str]:
        """
        Uses LLM to identify which tables are needed to answer the question.
        If LLM return no valid values -> use all tables
        """
        schema_summary = self.get_schema_summary()
        tables = select_tables(question, schema_summary)
        
        # Validate that returned tables exist in schema
        valid_tables = [t for t in tables if t in self.tables]
        
        if not valid_tables:
            logger.warning(f"LLM returned no valid tables, using all tables as fallback")
            return list(self.tables.keys())
        
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




_schema_parser_instance: Optional[SchemaParser] = None 


def get_schema_parser(schema_name: str = "retial_star_schema") -> SchemaParser:
    """
    Returns the singleton instance of SchemaParser.
    """
    global _schema_parser_instance
    
    if _schema_parser_instance is None:
        _schema_parser_instance = SchemaParser(schema_name)
        _schema_parser_instance.load_star_schema()
    
    return _schema_parser_instance
                    
            
        
        
        
                                                     
        
        
        