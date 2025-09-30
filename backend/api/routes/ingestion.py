from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import logging

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)

@router.post("/database")
async def ingest_database(connection_string: str):
    """
    Connect to database and discover schema.
    This endpoint is handled in main.py as /api/connect-database
    """
    pass

@router.post("/documents")
async def ingest_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Upload and process multiple documents.
    This endpoint is handled in main.py as /api/upload-documents
    """
    pass

@router.get("/status")
async def get_ingestion_status(job_id: str = None):
    """
    Get status of document processing jobs.
    This endpoint is handled in main.py as /api/ingestion-status/{job_id}
    """
    pass
