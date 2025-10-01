import logging
import re
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
import time
from services.schema_discovery import SchemaDiscovery
from services.document_processor import DocumentProcessor
from services.cache_service import QueryCache

logger = logging.getLogger(__name__)

class QueryEngine:
    """
    Production-ready query engine that processes natural language queries
    and routes them to SQL database or document search based on content.
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string, pool_size=10, max_overflow=20)
        
        # Initialize components
        self.schema_discovery = SchemaDiscovery()
        self.schema = self.schema_discovery.analyze_database(connection_string)
        self.document_processor = DocumentProcessor()
        
        logger.info("Query engine initialized with database schema")
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process natural language query with intelligent routing and caching.
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Query results with metadata
        """
        start_time = time.time()
        
        try:
            # Classify query type
            query_classification = self._classify_query(user_query)
            
            logger.info(f"Processing {query_classification['type']} query: {user_query}")
            
            if query_classification['type'] == 'sql':
                result = self._process_sql_query(user_query, query_classification)
            elif query_classification['type'] == 'document':
                result = self._process_document_query(user_query)
            elif query_classification['type'] == 'hybrid':
                result = self._process_hybrid_query(user_query)
            else:
                result = self._process_general_query(user_query)
            
            # Add performance metrics
            result['complexity'] = self._calculate_query_complexity(user_query, query_classification)
            result['processing_time'] = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return {
                'results': [],
                'query_type': 'error',
                'sources': [],
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify query to determine processing approach.
        
        Returns:
            Classification with confidence scores
        """
        query_lower = query.lower()
        
        # SQL indicators
        sql_indicators = [
            'count', 'average', 'sum', 'total', 'max', 'min',
            'salary', 'department', 'employee', 'staff',
            'hired', 'join date', 'position', 'role'
        ]
        
        # Document search indicators
        document_indicators = [
            'resume', 'cv', 'skills', 'experience',
            'python', 'java', 'programming', 'developer',
            'review', 'performance', 'contract', 'document'
        ]
        
        # Hybrid indicators
        hybrid_indicators = [
            'with skills', 'developers in', 'engineers who',
            'employees with experience', 'staff members with'
        ]
        
        sql_score = sum(1 for indicator in sql_indicators if indicator in query_lower)
        doc_score = sum(1 for indicator in document_indicators if indicator in query_lower)
        hybrid_score = sum(1 for indicator in hybrid_indicators if indicator in query_lower)
        
        # Determine query type
        if hybrid_score > 0 or (sql_score > 0 and doc_score > 0):
            query_type = 'hybrid'
            confidence = min(0.9, (sql_score + doc_score + hybrid_score) * 0.2)
        elif sql_score > doc_score:
            query_type = 'sql'
            confidence = min(0.9, sql_score * 0.2)
        elif doc_score > 0:
            query_type = 'document'
            confidence = min(0.9, doc_score * 0.2)
        else:
            query_type = 'general'
            confidence = 0.5
        
        return {
            'type': query_type,
            'confidence': confidence,
            'sql_score': sql_score,
            'document_score': doc_score,
            'hybrid_score': hybrid_score
        }
    
    def _process_sql_query(self, query: str, classification: Dict) -> Dict[str, Any]:
        """Process queries that should be answered from the database."""
        
        # Map natural language to schema
        schema_mapping = self.schema_discovery.map_natural_language_to_schema(query, self.schema)
        
        # Generate SQL query
        sql_query = self._generate_sql_query(query, schema_mapping)
        
        if not sql_query:
            return {
                'results': [],
                'query_type': 'sql',
                'sources': ['database'],
                'error': 'Could not generate SQL query',
                'sql_query': None
            }
        
        # Execute query with optimization
        optimized_sql = self.optimize_sql_query(sql_query)
        results = self._execute_sql_query(optimized_sql)
        
        return {
            'results': results,
            'query_type': 'sql',
            'sources': ['database'],
            'sql_query': optimized_sql,
            'tables_used': schema_mapping.get('suggested_tables', [])
        }
    
    def _generate_sql_query(self, query: str, schema_mapping: Dict) -> Optional[str]:
        """
        Generate SQL query from natural language using schema mapping.
        This is a simplified implementation - in production, you might use an LLM.
        """
        query_lower = query.lower()
        tables = schema_mapping.get('suggested_tables', [])
        
        if not tables:
            return None
        
        # Simple query patterns
        if any(word in query_lower for word in ['count', 'how many']):
            return self._generate_count_query(query_lower, tables)
        elif any(word in query_lower for word in ['average', 'avg']):
            return self._generate_average_query(query_lower, tables)
        elif any(word in query_lower for word in ['list', 'show', 'find']):
            return self._generate_select_query(query_lower, tables)
        elif 'highest' in query_lower or 'top' in query_lower:
            return self._generate_top_query(query_lower, tables)
        
        # Default select query
        return self._generate_select_query(query_lower, tables)
    
    def _generate_count_query(self, query: str, tables: List[str]) -> str:
        """Generate COUNT queries."""
        main_table = tables[0]
        
        # Basic count
        sql = f"SELECT COUNT(*) as count FROM {main_table}"
        
        # Add WHERE conditions if specific criteria mentioned
        where_conditions = []
        
        if 'department' in query:
            dept_column = self._find_column_by_pattern(main_table, ['dept', 'division'])
            if dept_column and any(dept in query for dept in ['engineering', 'sales', 'marketing', 'hr']):
                for dept in ['engineering', 'sales', 'marketing', 'hr']:
                    if dept in query:
                        where_conditions.append(f"{dept_column} ILIKE '%{dept}%'")
                        break
        
        if 'this year' in query or '2024' in query:
            date_column = self._find_column_by_pattern(main_table, ['hire', 'join', 'start', 'created'])
            if date_column:
                where_conditions.append(f"{date_column} >= '2024-01-01'")
        
        if where_conditions:
            sql += " WHERE " + " AND ".join(where_conditions)
        
        return sql
    
    def _generate_average_query(self, query: str, tables: List[str]) -> str:
        """Generate AVERAGE queries."""
        main_table = tables[0]
        
        # Find salary column
        salary_column = self._find_column_by_pattern(main_table, ['salary', 'pay', 'compensation'])
        
        if not salary_column:
            return f"SELECT COUNT(*) as count FROM {main_table}"
        
        sql = f"SELECT AVG({salary_column}) as average_salary FROM {main_table}"
        
        # Group by department if mentioned
        if 'department' in query or 'dept' in query:
            dept_column = self._find_column_by_pattern(main_table, ['dept', 'division'])
            if dept_column:
                sql = f"SELECT {dept_column}, AVG({salary_column}) as average_salary FROM {main_table} GROUP BY {dept_column}"
        
        return sql
    
    def _generate_select_query(self, query: str, tables: List[str]) -> str:
        """Generate SELECT queries."""
        main_table = tables[0]
        table_info = self.schema.get('tables', {}).get(main_table, {})
        columns = list(table_info.get('columns', {}).keys())
        
        # Select relevant columns
        select_columns = []
        
        # Always include name if available
        name_column = self._find_column_by_pattern(main_table, ['name'])
        if name_column:
            select_columns.append(name_column)
        
        # Include other relevant columns based on query
        if 'salary' in query:
            salary_col = self._find_column_by_pattern(main_table, ['salary', 'pay', 'compensation'])
            if salary_col:
                select_columns.append(salary_col)
        
        if 'department' in query:
            dept_col = self._find_column_by_pattern(main_table, ['dept', 'division'])
            if dept_col:
                select_columns.append(dept_col)
        
        # If no specific columns found, select first few
        if not select_columns:
            select_columns = columns[:3]
        
        sql = f"SELECT {', '.join(select_columns)} FROM {main_table}"
        
        # Add WHERE conditions
        where_conditions = []
        
        if 'hired this year' in query:
            date_column = self._find_column_by_pattern(main_table, ['hire', 'join', 'start'])
            if date_column:
                where_conditions.append(f"{date_column} >= '2024-01-01'")
        
        if where_conditions:
            sql += " WHERE " + " AND ".join(where_conditions)
        
        # Add LIMIT
        sql += " LIMIT 50"
        
        return sql
    
    def _generate_top_query(self, query: str, tables: List[str]) -> str:
        """Generate TOP/highest queries."""
        main_table = tables[0]
        
        # Extract number (default 5)
        number_match = re.search(r'top\s+(\d+)', query)
        limit = int(number_match.group(1)) if number_match else 5
        
        # Find columns
        name_column = self._find_column_by_pattern(main_table, ['name'])
        salary_column = self._find_column_by_pattern(main_table, ['salary', 'pay', 'compensation'])
        
        select_columns = []
        if name_column:
            select_columns.append(name_column)
        if salary_column:
            select_columns.append(salary_column)
        
        if not select_columns:
            select_columns = ['*']
        
        order_column = salary_column if salary_column else list(self.schema['tables'][main_table]['columns'].keys())[0]
        
        sql = f"SELECT {', '.join(select_columns)} FROM {main_table} ORDER BY {order_column} DESC LIMIT {limit}"
        
        return sql
    
    def _find_column_by_pattern(self, table: str, patterns: List[str]) -> Optional[str]:
        """Find column matching naming patterns."""
        table_info = self.schema.get('tables', {}).get(table, {})
        columns = table_info.get('columns', {})
        
        for column_name in columns:
            column_lower = column_name.lower()
            for pattern in patterns:
                if pattern in column_lower:
                    return column_name
        
        return None
    
    def _execute_sql_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query safely and return results."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    row_dict = {}
                    for col, value in zip(columns, row):
                        # Handle different data types
                        if hasattr(value, 'isoformat'):  # datetime
                            row_dict[col] = value.isoformat()
                        else:
                            row_dict[col] = value
                    results.append(row_dict)
                
                logger.info(f"SQL query executed successfully: {len(results)} rows returned")
                return results
                
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            raise
    
    def _process_document_query(self, query: str) -> Dict[str, Any]:
        """Process queries that should be answered from documents."""
        
        # Search documents using semantic similarity
        search_results = self.document_processor.search_documents(query, top_k=5)
        
        return {
            'results': search_results,
            'query_type': 'document',
            'sources': ['documents'],
            'total_documents_searched': len(self.document_processor.document_store)
        }
    
    def _process_hybrid_query(self, query: str) -> Dict[str, Any]:
        """Process queries that need both database and document search."""
        
        # Get database results
        sql_classification = {'type': 'sql', 'confidence': 0.8}
        sql_results = self._process_sql_query(query, sql_classification)
        
        # Get document results
        doc_results = self._process_document_query(query)
        
        # Combine results
        combined_results = {
            'sql_results': sql_results.get('results', []),
            'document_results': doc_results.get('results', [])
        }
        
        return {
            'results': combined_results,
            'query_type': 'hybrid',
            'sources': ['database', 'documents'],
            'sql_query': sql_results.get('sql_query')
        }
    
    def _process_general_query(self, query: str) -> Dict[str, Any]:
        """Process general queries by trying both approaches."""
        
        # Try SQL first
        try:
            sql_classification = {'type': 'sql', 'confidence': 0.5}
            sql_results = self._process_sql_query(query, sql_classification)
            if sql_results.get('results'):
                return sql_results
        except Exception as e:
            logger.warning(f"SQL approach failed for general query: {str(e)}")
        
        # Fallback to document search
        try:
            return self._process_document_query(query)
        except Exception as e:
            logger.error(f"Document search also failed: {str(e)}")
            return {
                'results': [],
                'query_type': 'general',
                'sources': [],
                'error': 'Unable to process query with available methods'
            }
    
    def optimize_sql_query(self, sql: str) -> str:
        """
        Optimize generated SQL query for better performance.
        
        Args:
            sql: Original SQL query
            
        Returns:
            Optimized SQL query
        """
        # Basic optimizations
        optimized = sql.strip()
        
        # Add LIMIT if not present and it's a SELECT without aggregation
        if (optimized.upper().startswith('SELECT') and 
            'LIMIT' not in optimized.upper() and 
            not any(agg in optimized.upper() for agg in ['COUNT', 'AVG', 'SUM', 'MAX', 'MIN', 'GROUP BY'])):
            optimized += ' LIMIT 100'
        
        # Add indexes hint if available (simplified)
        if 'ORDER BY' in optimized.upper():
            # In a real implementation, you'd check for existing indexes
            pass
        
        return optimized
    
    def _calculate_query_complexity(self, query: str, classification: Dict) -> str:
        """Calculate query complexity for performance metrics."""
        query_lower = query.lower()
        
        # Count complexity indicators
        complexity_score = 0
        
        if any(word in query_lower for word in ['join', 'group by', 'having']):
            complexity_score += 2
        
        if any(word in query_lower for word in ['count', 'avg', 'sum']):
            complexity_score += 1
        
        if len(query.split()) > 10:
            complexity_score += 1
        
        if classification['type'] == 'hybrid':
            complexity_score += 2
        
        if complexity_score >= 4:
            return 'high'
        elif complexity_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate query for safety and feasibility.
        
        Returns:
            Validation result with warnings/errors
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        query_upper = query.upper()
        
        # Check for dangerous SQL operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                validation['is_valid'] = False
                validation['errors'].append(f'Dangerous operation detected: {keyword}')
        
        # Check for potential SQL injection patterns
        injection_patterns = [
            r"[';]--",
            r"UNION\s+SELECT",
            r"OR\s+1\s*=\s*1",
            r"AND\s+1\s*=\s*1"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_upper):
                validation['is_valid'] = False
                validation['errors'].append('Potential SQL injection detected')
                break
        
        # Check query length
        if len(query) > 1000:
            validation['warnings'].append('Query is very long, consider simplifying')
        
        # Check for overly broad queries
        if re.search(r'SELECT\s+\*.*LIMIT\s+[5-9]\d{2,}', query_upper):
            validation['warnings'].append('Large result set requested, consider adding filters')
        
        return validation
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """
        Generate query suggestions based on schema and common patterns.
        
        Args:
            partial_query: Partial query text
            
        Returns:
            List of suggested completions
        """
        suggestions = []
        partial_lower = partial_query.lower().strip()
        
        # Schema-based suggestions
        tables = list(self.schema.get('tables', {}).keys())
        
        # Basic query starters
        if not partial_lower:
            suggestions.extend([
                'How many employees do we have?',
                'Average salary by department',
                'List all employees',
                'Show me employees with Python skills',
                'Top 5 highest paid employees'
            ])
        
        # Table-specific suggestions
        elif any(table.lower() in partial_lower for table in tables):
            suggestions.extend([
                f'{partial_query} in Engineering department',
                f'{partial_query} hired this year',
                f'{partial_query} with salary > 100000'
            ])
        
        # Column-specific suggestions based on discovered schema
        for table_name, table_info in self.schema.get('tables', {}).items():
            columns = table_info.get('columns', {})
            
            if 'count' in partial_lower:
                suggestions.append(f'Count of {table_name}')
            
            # Salary-related suggestions
            salary_columns = [col for col in columns if any(term in col.lower() 
                            for term in ['salary', 'pay', 'compensation'])]
            if salary_columns and ('salary' in partial_lower or 'pay' in partial_lower):
                suggestions.extend([
                    f'Average {salary_columns[0]} by department',
                    f'Employees with {salary_columns[0]} > 100000'
                ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get query engine performance statistics."""
        return {
            'database_connected': self.engine is not None,
            'tables_discovered': len(self.schema.get('tables', {})),
            'relationships_found': len(self.schema.get('relationships', [])),
            'documents_indexed': len(self.document_processor.document_store),
            'embeddings_cached': len(self.document_processor.embeddings_cache)
        }
