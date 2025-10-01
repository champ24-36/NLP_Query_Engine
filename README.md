# NLP Query Engine for Employee Data

A dynamic natural language query system that automatically discovers database schemas and handles both structured employee data and unstructured documents without hard-coding table names, column names, or relationships.

## Features

###  **Dynamic Schema Discovery**
- Automatically detects table names, columns, and relationships
- Handles naming variations (employee/employees/staff, salary/compensation/pay)
- Works with any reasonable employee database structure
- No hard-coding required

###  **Natural Language Processing**
- Intelligent query classification (SQL, Document search, Hybrid)
- Semantic mapping from natural language to database schema
- Support for complex queries with aggregations and joins
- Query optimization and performance monitoring

###  **Multi-Format Document Processing**
- PDF, DOCX, TXT, CSV file support
- Intelligent chunking based on document structure
- Special handling for resumes, contracts, and reviews
- Batch processing with progress tracking

###  **Production-Ready Features**
- Query caching with intelligent invalidation
- Connection pooling for database efficiency
- Async operations for better concurrency
- Real-time performance metrics
- Error handling and recovery

###  **Modern Web Interface**
- React-based responsive UI
- Real-time progress indicators
- Schema visualization
- Query history and suggestions
- Export functionality

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL/MySQL database (SQLite for demo)
- 8GB RAM recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nlp-query-engine
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database connection details
   ```

### Running the Application

#### Option 1: Docker Compose (Recommended)
```bash
docker-compose up --build
```

#### Option 2: Manual Setup
1. **Start Backend**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Usage Guide

### 1. Database Connection
1. Navigate to "Connect Data" tab
2. Enter your database connection string:
   ```
   postgresql://username:password@localhost:5432/database_name
   ```
3. Click "Connect & Analyze" to discover schema
4. View discovered tables, columns, and relationships

### 2. Document Upload
1. In the "Connect Data" tab, use the Document Upload section
2. Drag and drop files or click to browse
3. Supports: PDF, DOCX, TXT, CSV files
4. Monitor progress in real-time
5. View processing statistics

### 3. Natural Language Queries
1. Switch to "Query Data" tab
2. Enter natural language queries like:
   - "How many employees do we have?"
   - "Average salary by department"
   - "Show me Python developers"
   - "Employees with machine learning skills earning over 100k"
3. View results in tables, cards, or hybrid format
4. Export results as needed

## Architecture

### Backend Components

#### Schema Discovery (`services/schema_discovery.py`)
```python
class SchemaDiscovery:
    def analyze_database(self, connection_string: str) -> dict
    def map_natural_language_to_schema(self, query: str, schema: dict) -> dict
```

#### Document Processor (`services/document_processor.py`)
```python
class DocumentProcessor:
    def process_documents(self, file_paths: list) -> dict
    def dynamic_chunking(self, content: str, doc_type: str) -> list
```

#### Query Engine (`services/query_engine.py`)
```python
class QueryEngine:
    def process_query(self, user_query: str) -> dict
    def optimize_sql_query(self, sql: str) -> str
```

#### Cache Service (`services/cache_service.py`)
```python
class QueryCache:
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: int = None)
```

### Frontend Components

- **DatabaseConnector**: Handle database connections and schema visualization
- **DocumentUploader**: File upload with progress tracking
- **QueryInterface**: Natural language query input and suggestions
- **ResultsDisplay**: Adaptive results rendering based on query type

## API Endpoints

### Database Management
- `POST /api/connect-database` - Connect and analyze database
- `GET /api/schema` - Get discovered schema information

### Document Processing
- `POST /api/upload-documents` - Upload and process documents
- `GET /api/ingestion-status/{job_id}` - Check processing status

## API Endpoints

### Database Management
- `POST /api/connect-database` - Connect and analyze database
- `GET /api/schema` - Get discovered schema information

### Document Processing
- `POST /api/upload-documents` - Upload and process documents
- `GET /api/ingestion-status/{job_id}` - Check processing status

### Query Processing
- `POST /api/query` - Process natural language query
- `GET /api/query/history` - Get query history
- `GET /api/metrics` - Get system performance metrics

## Supported Database Schemas

The system automatically adapts to different schema variations:

### Schema Variation 1 (Traditional)
```sql
employees (emp_id, full_name, dept_id, position, annual_salary, join_date, office_location)
departments (dept_id, dept_name, manager_id)
```

### Schema Variation 2 (Modern)
```sql
staff (id, name, department, role, compensation, hired_on, city, reports_to)
documents (doc_id, staff_id, type, content, uploaded_at)
```

### Schema Variation 3 (Enterprise)
```sql
personnel (person_id, employee_name, division, title, pay_rate, start_date)
divisions (division_code, division_name, head_id)
```

## Query Examples

### Basic Queries
- "How many employees do we have?"
- "Average salary by department"
- "List employees hired this year"
- "Who reports to John Smith?"

### Complex Queries
- "Top 5 highest paid employees in each department"
- "Employees with Python skills earning over 100k"
- "Show me performance reviews for engineers hired last year"
- "Which departments have the highest turnover?"

### Document Queries
- "Find resumes with machine learning experience"
- "Show contracts expiring this year"
- "Developers with React.js skills"

### Hybrid Queries
- "Engineering employees with Python skills in their resume"
- "High-performing staff with leadership experience"

## Performance Optimizations

### Query Caching
- Intelligent TTL-based caching
- Cache hit rate monitoring
- Automatic cache invalidation
- Most accessed query tracking

### Database Optimizations
- Connection pooling (10 connections, 20 overflow)
- Query optimization with LIMIT clauses
- Index-aware query generation
- Prepared statement usage

### Document Processing
- Batch embedding generation (32 batch size)
- Efficient chunking strategies
- Memory-optimized processing
- Progress tracking

### Concurrent Processing
- Async I/O operations
- Background task processing
- Non-blocking query execution
- Real-time status updates

## Testing

### Unit Tests
```bash
cd backend
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Performance Tests
```bash
pytest tests/performance/ -v --benchmark-only
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32

# Cache
CACHE_TTL_SECONDS=300
CACHE_MAX_SIZE=1000

# Files
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=/tmp/uploads

# Performance
ASYNC_WORKERS=4
MAX_CONCURRENT_QUERIES=10
```

### Configuration File (`config.yml`)
```yaml
database:
  connection_string: ${DATABASE_URL}
  pool_size: 10
  max_overflow: 20

embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 32
  device: "cpu"

cache:
  ttl_seconds: 300
  max_size: 1000
  cleanup_interval: 3600

processing:
  max_file_size_mb: 10
  chunk_size: 512
  chunk_overlap: 50
  supported_formats: ["pdf", "docx", "txt", "csv"]
```

## Deployment

### Production Checklist
- [ ] Set secure database credentials
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies
- [ ] Set resource limits
- [ ] Enable security headers
- [ ] Configure rate limiting

### Docker Production
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Health Checks
- Database connectivity: `GET /health`
- Schema discovery status
- Document processing capacity
- Cache performance metrics

## Security Considerations

### Query Validation
- SQL injection prevention
- Dangerous operation detection
- Query complexity limits
- Input sanitization

### File Upload Security
- File type validation
- Size limitations
- Virus scanning (recommended)
- Secure temporary storage

### API Security
- Request rate limiting
- CORS configuration
- Input validation
- Error message sanitization

## Performance Benchmarks

### Target Performance
- 95% of queries under 2 seconds
- Support for 10+ concurrent users
- 1000+ documents processing capability
- <500ms average response time for cached queries

### Optimization Strategies
- Database query optimization
- Efficient embedding computation
- Smart caching strategies
- Async processing pipelines

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database service
pg_isready -h localhost -p 5432

# Verify credentials
psql -h localhost -U username -d database_name
```

#### Document Processing Failures
- Check file permissions and disk space
- Verify supported file formats
- Monitor memory usage during processing
- Check embedding model download

#### Frontend Connection Issues
- Verify API URL configuration
- Check CORS settings
- Monitor network requests in browser
- Validate backend service health

### Debug Mode
```bash
# Backend debug mode
uvicorn main:app --reload --log-level debug

# Frontend debug mode
REACT_APP_DEBUG=true npm start
```

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Run tests before committing
5. Submit pull request

### Code Style
- Python: Black formatting, PEP 8 compliance
- JavaScript: ESLint configuration
- SQL: Standard formatting
- Documentation: Clear docstrings and comments

### Testing Requirements
- Unit test coverage >80%
- Integration tests for critical paths
- Performance benchmarks
- Documentation updates

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Documentation
- API Documentation: http://localhost:8000/docs
- Schema Discovery Guide
- Query Examples Repository
- Performance Tuning Guide

### Community
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Wiki: Project Wiki

### Commercial Support
For enterprise support, custom features, or consulting services, please contact: [recruiter email]

## Changelog

### v1.0.0 (Current)
- Dynamic schema discovery
- Multi-format document processing
- Natural language query interface
- Production-ready performance optimizations
- Comprehensive web interface
- Docker containerization
- Extensive test coverage

### Planned Features (v1.1.0)
- Advanced analytics dashboard
- Custom embedding models
- Automated report generation
- Enhanced security features
- Multi-language support
- Advanced visualization options

---

**Note**: This implementation focuses on functionality and robustness over visual aesthetics. The system is designed to handle real-world scenarios with proper error handling, performance optimization, and scalability considerations.
