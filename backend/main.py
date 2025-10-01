from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import time
import os
from datetime import datetime
import json
import uuid

# Import our services
from api.routes.ingestion import router as ingestion_router
from api.routes.query import router as query_router  
from api.routes.schema import router as schema_router
from services.schema_discovery import SchemaDiscovery
from services.document_processor import DocumentProcessor
from services.query_engine import QueryEngine
from services.cache_service import QueryCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NLP Query Engine",
    description="Dynamic NLP Query Engine for Employee Data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
class AppState:
    def __init__(self):
        self.query_engine: Optional[QueryEngine] = None
        self.document_processor = DocumentProcessor()
        self.schema_discovery = SchemaDiscovery()
        self.cache = QueryCache()
        self.ingestion_jobs: Dict[str, Dict] = {}
        self.connected_database = False
        self.schema_info: Dict = {}

app_state = AppState()

# Pydantic models
class DatabaseConnection(BaseModel):
    connection_string: str

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    results: Any
    query_type: str
    performance_metrics: Dict
    sources: List[str]
    sql_query: Optional[str] = None

# Middleware for performance tracking
@app.middleware("http")
async def performance_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log performance metrics
    logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_connected": app_state.connected_database,
        "documents_indexed": len(app_state.document_processor.document_store)
    }

# Database connection endpoint
@app.post("/api/connect-database")
async def connect_database(connection: DatabaseConnection):
    try:
        logger.info(f"Connecting to database...")
        
        # Discover schema
        schema_info = app_state.schema_discovery.analyze_database(
            connection.connection_string
        )
        
        # Initialize query engine with discovered schema
        app_state.query_engine = QueryEngine(connection.connection_string)
        app_state.connected_database = True
        app_state.schema_info = schema_info
        
        logger.info(f"Database connected successfully. Found {len(schema_info.get('tables', {}))} tables")
        
        return {
            "status": "success",
            "message": "Database connected and schema discovered",
            "schema": schema_info,
            "tables_count": len(schema_info.get('tables', {})),
            "relationships_count": len(schema_info.get('relationships', []))
        }
        
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Database connection failed: {str(e)}")

# Document upload endpoint
@app.post("/api/upload-documents")
async def upload_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    job_id = str(uuid.uuid4())
    
    # Initialize job tracking
    app_state.ingestion_jobs[job_id] = {
        "status": "processing",
        "total_files": len(files),
        "processed_files": 0,
        "failed_files": 0,
        "start_time": datetime.now().isoformat(),
        "files": []
    }
    
    # Process files in background
    background_tasks.add_task(process_documents_background, job_id, files)
    
    return {
        "job_id": job_id,
        "status": "started",
        "total_files": len(files),
        "message": f"Processing {len(files)} documents"
    }

async def process_documents_background(job_id: str, files: List[UploadFile]):
    """Background task to process uploaded documents"""
    job = app_state.ingestion_jobs[job_id]
    
    try:
        processed_files = []
        
        for file in files:
            try:
                # Read file content
                content = await file.read()
                
                # Save temporary file
                temp_path = f"/tmp/{file.filename}"
                with open(temp_path, "wb") as f:
                    f.write(content)
                
                # Process document
                doc_info = app_state.document_processor.process_single_document(
                    temp_path, file.filename
                )
                
                processed_files.append({
                    "filename": file.filename,
                    "status": "success",
                    "chunks": len(doc_info.get("chunks", [])),
                    "type": doc_info.get("type", "unknown")
                })
                
                job["processed_files"] += 1
                
                # Cleanup temp file
                os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"Failed to process {file.filename}: {str(e)}")
                processed_files.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
                job["failed_files"] += 1
        
        # Update job status
        job.update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            "files": processed_files
        })
        
        logger.info(f"Document processing job {job_id} completed. "
                   f"Processed: {job['processed_files']}, Failed: {job['failed_files']}")
                   
    except Exception as e:
        logger.error(f"Document processing job {job_id} failed: {str(e)}")
        job.update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })

# Get ingestion status
@app.get("/api/ingestion-status/{job_id}")
async def get_ingestion_status(job_id: str):
    if job_id not in app_state.ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return app_state.ingestion_jobs[job_id]

# Query endpoint
@app.post("/api/query")
async def process_query(query_request: QueryRequest) -> QueryResponse:
    if not app_state.query_engine:
        raise HTTPException(status_code=400, detail="Database not connected")
    
    start_time = time.time()
    
    try:
        # Check cache first
        cache_key = f"query:{hash(query_request.query)}"
        cached_result = app_state.cache.get(cache_key)
        
        if cached_result:
            performance_metrics = {
                "response_time": time.time() - start_time,
                "cache_hit": True,
                "query_complexity": "cached"
            }
            
            return QueryResponse(
                results=cached_result["results"],
                query_type=cached_result["query_type"],
                performance_metrics=performance_metrics,
                sources=cached_result["sources"],
                sql_query=cached_result.get("sql_query")
            )
        
        # Process query
        result = app_state.query_engine.process_query(query_request.query)
        
        # Cache the result
        app_state.cache.set(cache_key, result)
        
        performance_metrics = {
            "response_time": time.time() - start_time,
            "cache_hit": False,
            "query_complexity": result.get("complexity", "medium")
        }
        
        return QueryResponse(
            results=result["results"],
            query_type=result["query_type"],
            performance_metrics=performance_metrics,
            sources=result["sources"],
            sql_query=result.get("sql_query")
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# Get query history
@app.get("/api/query/history")
async def get_query_history():
    return app_state.cache.get_recent_queries()

# Get current schema
@app.get("/api/schema")
async def get_schema():
    if not app_state.connected_database:
        raise HTTPException(status_code=400, detail="Database not connected")
    
    return {
        "schema": app_state.schema_info,
        "stats": {
            "tables": len(app_state.schema_info.get('tables', {})),
            "relationships": len(app_state.schema_info.get('relationships', [])),
            "documents_indexed": len(app_state.document_processor.document_store)
        }
    }

# Get system metrics
@app.get("/api/metrics")
async def get_metrics():
    return {
        "database_connected": app_state.connected_database,
        "documents_indexed": len(app_state.document_processor.document_store),
        "cache_size": app_state.cache.size(),
        "cache_hit_rate": app_state.cache.hit_rate(),
        "active_jobs": len([j for j in app_state.ingestion_jobs.values() if j["status"] == "processing"])
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
