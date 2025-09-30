import sqlalchemy as sa
from sqlalchemy import create_engine, inspect, MetaData, text
from typing import Dict, List, Tuple, Optional
import logging
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class SchemaDiscovery:
    """
    Dynamically discovers and analyzes database schema.
    Works with any SQL database structure without hard-coding.
    """
    
    def __init__(self):
        self.engine = None
        self.metadata = None
        self.schema_info = {}
        
        # Common naming patterns for employee-related entities
        self.entity_patterns = {
            'employee': ['employee', 'emp', 'staff', 'personnel', 'worker'],
            'department': ['department', 'dept', 'division', 'team'],
            'salary': ['salary', 'compensation', 'pay', 'wage'],
            'position': ['position', 'role', 'title', 'job'],
            'manager': ['manager', 'supervisor', 'lead', 'boss'],
            'date': ['date', 'time', 'when', 'day'],
        }
    
    def analyze_database(self, connection_string: str) -> Dict:
        """
        Connect to database and discover complete schema.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Dictionary containing tables, columns, relationships, and metadata
        """
        try:
            logger.info(f"Connecting to database...")
            self.engine = create_engine(connection_string, pool_pre_ping=True)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            
            inspector = inspect(self.engine)
            
            tables_info = []
            relationships = []
            
            # Analyze each table
            for table_name in inspector.get_table_names():
                table_info = self._analyze_table(inspector, table_name)
                tables_info.append(table_info)
            
            # Discover relationships
            relationships = self._discover_relationships(inspector, tables_info)
            
            # Infer implicit relationships
            implicit_relationships = self._infer_relationships(tables_info)
            relationships.extend(implicit_relationships)
            
            self.schema_info = {
                'tables': tables_info,
                'relationships': relationships,
                'connection_string': connection_string,
                'database_type': self.engine.dialect.name
            }
            
            logger.info(f"Schema discovery complete: {len(tables_info)} tables, {len(relationships)} relationships")
            return self.schema_info
            
        except Exception as e:
            logger.error(f"Schema discovery failed: {str(e)}")
            raise
    
    def _analyze_table(self, inspector, table_name: str) -> Dict:
        """Analyze a single table to extract metadata."""
        columns = []
        primary_keys = []
        foreign_keys = []
        
        # Get column information
        for col in inspector.get_columns(table_name):
            col_info = {
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': col.get('default'),
            }
            columns.append(col_info)
        
        # Get primary keys
        pk = inspector.get_pk_constraint(table_name)
        if pk and pk.get('constrained_columns'):
            primary_keys = pk['constrained_columns']
        
        # Get foreign keys
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append({
                'columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            })
        
        # Get row count (sample for large tables)
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
        except:
            row_count = None
        
        # Classify table purpose
        table_purpose = self._classify_table_purpose(table_name, columns)
        
        return {
            'name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'row_count': row_count,
            'purpose': table_purpose
        }
    
    def _classify_table_purpose(self, table_name: str, columns: List[Dict]) -> str:
        """Classify what type of entity this table represents."""
        table_lower = table_name.lower()
        col_names = [c['name'].lower() for c in columns]
        
        # Check for employee-related tables
        for pattern in self.entity_patterns['employee']:
            if pattern in table_lower:
                return 'employee'
        
        # Check for department tables
        for pattern in self.entity_patterns['department']:
            if pattern in table_lower:
                return 'department'
        
        # Check column names for hints
        if any('salary' in col or 'compensation' in col for col in col_names):
            return 'compensation'
        
        if 'document' in table_lower or 'file' in table_lower:
            return 'document'
        
        return 'other'
    
    def _discover_relationships(self, inspector, tables_info: List[Dict]) -> List[Dict]:
        """Discover explicit foreign key relationships."""
        relationships = []
        
        for table in tables_info:
            for fk in table['foreign_keys']:
                relationships.append({
                    'from_table': table['name'],
                    'from_columns': fk['columns'],
                    'to_table': fk['referred_table'],
                    'to_columns': fk['referred_columns'],
                    'type': 'explicit'
                })
        
        return relationships
    
    def _infer_relationships(self, tables_info: List[Dict]) -> List[Dict]:
        """Infer implicit relationships based on naming conventions."""
        relationships = []
        table_map = {t['name']: t for t in tables_info}
        
        for table in tables_info:
            for col in table['columns']:
                col_name = col['name'].lower()
                
                # Look for columns ending in _id that might reference other tables
                if col_name.endswith('_id'):
                    potential_table = col_name[:-3]  # Remove '_id'
                    
                    # Check for plural forms
                    for other_table in table_map.keys():
                        if (potential_table in other_table.lower() or 
                            other_table.lower() in potential_table):
                            
                            # Avoid duplicating explicit relationships
                            existing = any(
                                r['from_table'] == table['name'] and 
                                col['name'] in r['from_columns']
                                for r in relationships
                            )
                            
                            if not existing:
                                relationships.append({
                                    'from_table': table['name'],
                                    'from_columns': [col['name']],
                                    'to_table': other_table,
                                    'to_columns': table_map[other_table]['primary_keys'],
                                    'type': 'inferred'
                                })
        
        return relationships
    
    def map_natural_language_to_schema(self, query: str, schema: Dict = None) -> Dict:
        """
        Map natural language terms to actual database schema elements.
        
        Args:
            query: User's natural language query
            schema: Optional schema dict (uses self.schema_info if not provided)
            
        Returns:
            Dictionary mapping natural language terms to schema elements
        """
        if schema is None:
            schema = self.schema_info
        
        query_lower = query.lower()
        mappings = {
            'tables': [],
            'columns': [],
            'filters': [],
            'aggregations': []
        }
        
        # Map table references
        for table in schema['tables']:
            table_name_lower = table['name'].lower()
            
            # Check if table name or its purpose is mentioned
            if table_name_lower in query_lower or table['purpose'] in query_lower:
                mappings['tables'].append(table['name'])
            
            # Check for entity pattern matches
            for entity_type, patterns in self.entity_patterns.items():
                if any(pattern in query_lower for pattern in patterns):
                    if table['purpose'] == entity_type or any(
                        pattern in table_name_lower for pattern in patterns
                    ):
                        if table['name'] not in mappings['tables']:
                            mappings['tables'].append(table['name'])
        
        # Map column references
        for table in schema['tables']:
            if table['name'] in mappings['tables'] or not mappings['tables']:
                for col in table['columns']:
                    col_name_lower = col['name'].lower()
                    
                    # Direct mention
                    if col_name_lower in query_lower:
                        mappings['columns'].append({
                            'table': table['name'],
                            'column': col['name'],
                            'type': col['type']
                        })
                    
                    # Pattern matching for common synonyms
                    for entity_type, patterns in self.entity_patterns.items():
                        if any(pattern in query_lower for pattern in patterns):
                            if any(pattern in col_name_lower for pattern in patterns):
                                mappings['columns'].append({
                                    'table': table['name'],
                                    'column': col['name'],
                                    'type': col['type']
                                })
        
        # Detect aggregation operations
        agg_keywords = {
            'count': ['count', 'how many', 'number of', 'total'],
            'average': ['average', 'avg', 'mean'],
            'sum': ['sum', 'total', 'combined'],
            'max': ['maximum', 'max', 'highest', 'most'],
            'min': ['minimum', 'min', 'lowest', 'least']
        }
        
        for agg_type, keywords in agg_keywords.items():
            if any(kw in query_lower for kw in keywords):
                mappings['aggregations'].append(agg_type)
        
        # Detect comparison filters
        comparison_patterns = [
            (r'over (\d+)', 'gt'),
            (r'above (\d+)', 'gt'),
            (r'more than (\d+)', 'gt'),
            (r'under (\d+)', 'lt'),
            (r'below (\d+)', 'lt'),
            (r'less than (\d+)', 'lt'),
            (r'equals? (\d+)', 'eq'),
        ]
        
        for pattern, op in comparison_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                mappings['filters'].append({
                    'operator': op,
                    'value': matches[0]
                })
        
        return mappings
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict]:
        """Get sample rows from a table for context understanding."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return rows
        except Exception as e:
            logger.error(f"Failed to get sample data from {table_name}: {str(e)}")
            return []
    
    def get_column_statistics(self, table_name: str, column_name: str) -> Dict:
        """Get statistics for a specific column."""
        try:
            with self.engine.connect() as conn:
                # Check if column is numeric
                result = conn.execute(text(
                    f"SELECT MIN({column_name}), MAX({column_name}), "
                    f"AVG({column_name}), COUNT(DISTINCT {column_name}) "
                    f"FROM {table_name}"
                ))
                stats = result.fetchone()
                
                return {
                    'min': stats[0],
                    'max': stats[1],
                    'avg': stats[2],
                    'distinct_count': stats[3]
                }
        except:
            # Column might not be numeric
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(
                        f"SELECT COUNT(DISTINCT {column_name}) FROM {table_name}"
                    ))
                    return {'distinct_count': result.scalar()}
            except:
                return {}
