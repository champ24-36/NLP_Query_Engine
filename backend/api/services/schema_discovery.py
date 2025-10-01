import sqlalchemy as sa
from sqlalchemy import create_engine, inspect, text, MetaData
from typing import Dict, List, Any, Optional
import re
import logging
from difflib import SequenceMatcher
import pandas as pd

logger = logging.getLogger(__name__)

class SchemaDiscovery:
    """
    Dynamically discovers database schema without hard-coding table or column names.
    Works with variations in naming conventions.
    """
    
    def __init__(self):
        self.engine = None
        self.inspector = None
        self.metadata = None
        
        # Common naming patterns for employee databases
        self.employee_patterns = [
            r'emp(?:loyee)?s?',
            r'staff',
            r'personnel',
            r'workers?',
            r'people'
        ]
        
        self.department_patterns = [
            r'dept(?:artment)?s?',
            r'divisions?',
            r'teams?',
            r'units?'
        ]
        
        self.salary_patterns = [
            r'salary|salaries',
            r'compensation',
            r'pay(?:_?rate)?',
            r'wage',
            r'income'
        ]
    
    def analyze_database(self, connection_string: str) -> Dict[str, Any]:
        """
        Connect to database and automatically discover schema structure.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Dictionary containing discovered schema information
        """
        try:
            # Create engine and inspector
            self.engine = create_engine(connection_string, pool_size=10, max_overflow=20)
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connection successful")
            
            # Discover schema components
            tables_info = self._discover_tables()
            relationships = self._discover_relationships(tables_info)
            semantic_mapping = self._create_semantic_mapping(tables_info)
            
            schema_info = {
                "tables": tables_info,
                "relationships": relationships,
                "semantic_mapping": semantic_mapping,
                "connection_string": connection_string,
                "database_type": self._get_database_type()
            }
            
            logger.info(f"Schema discovery completed: {len(tables_info)} tables, {len(relationships)} relationships")
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Schema analysis failed: {str(e)}")
            raise
    
    def _discover_tables(self) -> Dict[str, Dict]:
        """Discover all tables and their columns with data types and sample data."""
        tables_info = {}
        
        table_names = self.inspector.get_table_names()
        logger.info(f"Found {len(table_names)} tables: {table_names}")
        
        for table_name in table_names:
            try:
                # Get column information
                columns = self.inspector.get_columns(table_name)
                primary_keys = self.inspector.get_pk_constraint(table_name)
                foreign_keys = self.inspector.get_foreign_keys(table_name)
                indexes = self.inspector.get_indexes(table_name)
                
                # Get sample data for context
                sample_data = self._get_sample_data(table_name)
                
                # Classify table purpose
                table_purpose = self._classify_table_purpose(table_name, columns)
                
                tables_info[table_name] = {
                    "columns": {col["name"]: {
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": col["default"]
                    } for col in columns},
                    "primary_keys": primary_keys["constrained_columns"],
                    "foreign_keys": foreign_keys,
                    "indexes": [idx["column_names"] for idx in indexes],
                    "sample_data": sample_data,
                    "purpose": table_purpose,
                    "row_count": self._get_row_count(table_name)
                }
                
            except Exception as e:
                logger.warning(f"Failed to analyze table {table_name}: {str(e)}")
                continue
        
        return tables_info
    
    def _get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict]:
        """Get sample data from table for context understanding."""
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = conn.execute(query)
                
                # Convert to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                sample_data = []
                for row in rows:
                    sample_data.append(dict(zip(columns, row)))
                
                return sample_data
                
        except Exception as e:
            logger.warning(f"Failed to get sample data for {table_name}: {str(e)}")
            return []
    
    def _get_row_count(self, table_name: str) -> int:
        """Get approximate row count for the table."""
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT COUNT(*) as count FROM {table_name}")
                result = conn.execute(query)
                return result.scalar()
        except:
            return 0
    
    def _classify_table_purpose(self, table_name: str, columns: List[Dict]) -> str:
        """Classify the purpose of a table based on name and columns."""
        table_lower = table_name.lower()
        column_names = [col["name"].lower() for col in columns]
        
        # Check for employee table patterns
        for pattern in self.employee_patterns:
            if re.search(pattern, table_lower):
                return "employees"
        
        # Check for department table patterns
        for pattern in self.department_patterns:
            if re.search(pattern, table_lower):
                return "departments"
        
        # Check column names for clues
        if any("name" in col and ("emp" in col or "person" in col or "staff" in col) for col in column_names):
            return "employees"
        
        if any("dept" in col or "division" in col for col in column_names):
            return "departments"
        
        # Look for salary/compensation indicators
        if any(re.search(pattern, " ".join(column_names)) for pattern in self.salary_patterns):
            return "compensation"
        
        return "other"
    
    def _discover_relationships(self, tables_info: Dict) -> List[Dict]:
        """Discover relationships between tables."""
        relationships = []
        
        for table_name, table_info in tables_info.items():
            # Explicit foreign key relationships
            for fk in table_info["foreign_keys"]:
                relationships.append({
                    "type": "foreign_key",
                    "from_table": table_name,
                    "from_columns": fk["constrained_columns"],
                    "to_table": fk["referred_table"],
                    "to_columns": fk["referred_columns"]
                })
        
        # Infer implicit relationships based on naming patterns
        implicit_relationships = self._infer_implicit_relationships(tables_info)
        relationships.extend(implicit_relationships)
        
        return relationships
    
    def _infer_implicit_relationships(self, tables_info: Dict) -> List[Dict]:
        """Infer relationships based on column name patterns."""
        relationships = []
        
        for table1_name, table1_info in tables_info.items():
            for table2_name, table2_info in tables_info.items():
                if table1_name == table2_name:
                    continue
                
                # Look for columns that might reference other tables
                for col1_name in table1_info["columns"]:
                    for col2_name in table2_info["columns"]:
                        # Check if column names suggest a relationship
                        if self._columns_likely_related(col1_name, col2_name, table1_name, table2_name):
                            relationships.append({
                                "type": "inferred",
                                "from_table": table1_name,
                                "from_columns": [col1_name],
                                "to_table": table2_name,
                                "to_columns": [col2_name],
                                "confidence": 0.7
                            })
        
        return relationships
    
    def _columns_likely_related(self, col1: str, col2: str, table1: str, table2: str) -> bool:
        """Check if two columns are likely to be related."""
        col1_lower = col1.lower()
        col2_lower = col2.lower()
        
        # ID patterns
        if (col1_lower.endswith("_id") and col2_lower == "id" and 
            col1_lower.replace("_id", "") in table2.lower()):
            return True
        
        if (col2_lower.endswith("_id") and col1_lower == "id" and 
            col2_lower.replace("_id", "") in table1.lower()):
            return True
        
        # Direct name matches with high similarity
        similarity = SequenceMatcher(None, col1_lower, col2_lower).ratio()
        if similarity > 0.8:
            return True
        
        return False
    
    def _create_semantic_mapping(self, tables_info: Dict) -> Dict[str, Dict]:
        """Create mapping from natural language terms to actual schema elements."""
        mapping = {
            "tables": {},
            "columns": {}
        }
        
        # Map common terms to actual table names
        for table_name, table_info in tables_info.items():
            purpose = table_info["purpose"]
            
            # Add table mappings
            if purpose == "employees":
                for term in ["employee", "employees", "staff", "worker", "person", "people"]:
                    mapping["tables"][term] = table_name
            elif purpose == "departments":
                for term in ["department", "departments", "dept", "division", "team"]:
                    mapping["tables"][term] = table_name
        
        # Map common terms to actual column names
        for table_name, table_info in tables_info.items():
            for col_name in table_info["columns"]:
                col_lower = col_name.lower()
                
                # Salary mappings
                if any(re.search(pattern, col_lower) for pattern in self.salary_patterns):
                    mapping["columns"]["salary"] = f"{table_name}.{col_name}"
                    mapping["columns"]["pay"] = f"{table_name}.{col_name}"
                    mapping["columns"]["compensation"] = f"{table_name}.{col_name}"
                
                # Name mappings
                if "name" in col_lower:
                    mapping["columns"]["name"] = f"{table_name}.{col_name}"
                
                # Date mappings
                if any(term in col_lower for term in ["date", "time", "created", "hired", "join"]):
                    if "hire" in col_lower or "join" in col_lower or "start" in col_lower:
                        mapping["columns"]["hire_date"] = f"{table_name}.{col_name}"
                        mapping["columns"]["start_date"] = f"{table_name}.{col_name}"
        
        return mapping
    
    def _get_database_type(self) -> str:
        """Determine the type of database."""
        if not self.engine:
            return "unknown"
        
        dialect = self.engine.dialect.name.lower()
        return dialect
    
    def map_natural_language_to_schema(self, query: str, schema: Dict) -> Dict[str, Any]:
        """
        Map user's natural language query terms to actual database schema elements.
        
        Args:
            query: Natural language query
            schema: Discovered schema information
            
        Returns:
            Mapping of query terms to schema elements
        """
        query_lower = query.lower()
        mapping = {
            "suggested_tables": [],
            "suggested_columns": [],
            "query_type": self._classify_query_type(query_lower)
        }
        
        # Use semantic mapping to find relevant tables and columns
        semantic_mapping = schema.get("semantic_mapping", {})
        
        # Find relevant tables
        for term, table_name in semantic_mapping.get("tables", {}).items():
            if term in query_lower:
                if table_name not in mapping["suggested_tables"]:
                    mapping["suggested_tables"].append(table_name)
        
        # Find relevant columns
        for term, column_path in semantic_mapping.get("columns", {}).items():
            if term in query_lower:
                if column_path not in mapping["suggested_columns"]:
                    mapping["suggested_columns"].append(column_path)
        
        # If no specific matches, suggest based on query type
        if not mapping["suggested_tables"]:
            mapping["suggested_tables"] = self._suggest_tables_by_query_type(
                mapping["query_type"], schema
            )
        
        return mapping
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of natural language query."""
        query_lower = query.lower()
        
        # Aggregation queries
        if any(word in query_lower for word in ["count", "average", "sum", "total", "max", "min"]):
            return "aggregation"
        
        # List/search queries
        if any(word in query_lower for word in ["list", "show", "find", "get", "who", "which"]):
            return "search"
        
        # Comparison queries
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            return "comparison"
        
        return "general"
    
    def _suggest_tables_by_query_type(self, query_type: str, schema: Dict) -> List[str]:
        """Suggest relevant tables based on query type."""
        tables = schema.get("tables", {})
        
        # For most queries, prioritize employee tables
        employee_tables = [name for name, info in tables.items() 
                          if info.get("purpose") == "employees"]
        
        if employee_tables:
            return employee_tables[:2]  # Return top 2 employee tables
        
        # Fallback to tables with most data
        return sorted(tables.keys(), 
                     key=lambda t: tables[t].get("row_count", 0), 
                     reverse=True)[:2]
