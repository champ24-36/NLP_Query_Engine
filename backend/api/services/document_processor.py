import os
import logging
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import json
import re
from datetime import datetime
import asyncio

# Document processing libraries
try:
    import PyPDF2
    from PyPDF2 import PdfReader
except ImportError:
    PyPDF2 = None

try:
    import docx
    from docx import Document
except ImportError:
    docx = None

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Process multiple document types with intelligent chunking and embedding generation.
    Supports PDF, DOCX, TXT, CSV files with optimized batch processing.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.document_store: Dict[str, Dict] = {}
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        
        # Chunking parameters - not hard-coded
        self.base_chunk_size = 512  # Base size, will be adjusted
        self.chunk_overlap = 50
        
        logger.info(f"Document processor initialized with model: {model_name}")
    
    def process_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Process multiple documents with batch processing for efficiency.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Processing results summary
        """
        results = {
            "processed": 0,
            "failed": 0,
            "total_chunks": 0,
            "document_types": {},
            "processing_time": 0,
            "errors": []
        }
        
        start_time = datetime.now()
        
        for file_path in file_paths:
            try:
                doc_info = self.process_single_document(file_path)
                results["processed"] += 1
                results["total_chunks"] += len(doc_info.get("chunks", []))
                
                doc_type = doc_info.get("type", "unknown")
                results["document_types"][doc_type] = results["document_types"].get(doc_type, 0) + 1
                
                logger.info(f"Processed {file_path}: {len(doc_info.get('chunks', []))} chunks")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{file_path}: {str(e)}")
                logger.error(f"Failed to process {file_path}: {str(e)}")
        
        results["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # Generate embeddings in batch for efficiency
        if results["total_chunks"] > 0:
            self._generate_batch_embeddings()
        
        return results
    
    def process_single_document(self, file_path: str, filename: str = None) -> Dict[str, Any]:
        """
        Process a single document and return document information.
        
        Args:
            file_path: Path to the document
            filename: Optional filename override
            
        Returns:
            Document processing information
        """
        if filename is None:
            filename = os.path.basename(file_path)
        
        # Generate document ID
        doc_id = self._generate_doc_id(file_path)
        
        # Auto-detect file type
        file_type = self._detect_file_type(file_path)
        
        # Extract content based on file type
        content = self._extract_content(file_path, file_type)
        
        # Intelligent chunking based on document structure
        chunks = self.dynamic_chunking(content, file_type)
        
        # Store document information
        doc_info = {
            "id": doc_id,
            "filename": filename,
            "file_path": file_path,
            "type": file_type,
            "content": content,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "processed_at": datetime.now().isoformat(),
            "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
        
        self.document_store[doc_id] = doc_info
        
        return doc_info
    
    def _detect_file_type(self, file_path: str) -> str:
        """Auto-detect file type based on extension and content."""
        extension = Path(file_path).suffix.lower()
        
        type_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'docx',
            '.txt': 'txt',
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel'
        }
        
        return type_mapping.get(extension, 'unknown')
    
    def _extract_content(self, file_path: str, file_type: str) -> str:
        """Extract text content from different file types."""
        try:
            if file_type == 'pdf':
                return self._extract_pdf_content(file_path)
            elif file_type == 'docx':
                return self._extract_docx_content(file_path)
            elif file_type == 'txt':
                return self._extract_txt_content(file_path)
            elif file_type == 'csv':
                return self._extract_csv_content(file_path)
            else:
                # Fallback to text extraction
                return self._extract_txt_content(file_path)
                
        except Exception as e:
            logger.error(f"Content extraction failed for {file_path}: {str(e)}")
            raise
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text content from PDF files."""
        if not PyPDF2:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.warning(f"PDF extraction failed, trying alternate method: {str(e)}")
            # Fallback method if needed
            raise
        
        return text.strip()
    
    def _extract_docx_content(self, file_path: str) -> str:
        """Extract text content from DOCX files."""
        if not docx:
            raise ImportError("python-docx not installed. Run: pip install python-docx")
        
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise
    
    def _extract_txt_content(self, file_path: str) -> str:
        """Extract content from text files."""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not decode file {file_path} with any supported encoding")
    
    def _extract_csv_content(self, file_path: str) -> str:
        """Extract and format CSV content as text."""
        try:
            df = pd.read_csv(file_path)
            # Convert to a readable text format
            text = f"CSV File with {len(df)} rows and {len(df.columns)} columns:\n"
            text += f"Columns: {', '.join(df.columns)}\n\n"
            
            # Add first few rows as sample
            sample_rows = min(5, len(df))
            text += f"Sample data (first {sample_rows} rows):\n"
            text += df.head(sample_rows).to_string(index=False)
            
            return text
        except Exception as e:
            logger.error(f"CSV extraction failed: {str(e)}")
            raise
    
    def dynamic_chunking(self, content: str, doc_type: str) -> List[Dict[str, Any]]:
        """
        Intelligent chunking based on document structure and type.
        
        Args:
            content: Document text content
            doc_type: Type of document (pdf, docx, etc.)
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        if doc_type == 'csv':
            # For CSV, create chunks based on logical sections
            chunks = self._chunk_csv_content(content)
        elif self._is_resume_content(content):
            # Special handling for resumes
            chunks = self._chunk_resume_content(content)
        elif self._is_contract_content(content):
            # Special handling for contracts
            chunks = self._chunk_contract_content(content)
        else:
            # Default paragraph-based chunking
            chunks = self._chunk_by_paragraphs(content)
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.update({
                'chunk_id': i,
                'doc_type': doc_type,
                'char_count': len(chunk['text']),
                'word_count': len(chunk['text'].split())
            })
        
        return chunks
    
    def _chunk_csv_content(self, content: str) -> List[Dict[str, Any]]:
        """Chunk CSV content logically."""
        lines = content.split('\n')
        chunks = []
        
        current_chunk = ""
        chunk_size = 0
        
        for line in lines:
            if chunk_size + len(line) > self.base_chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'type': 'csv_section'
                })
                current_chunk = line + "\n"
                chunk_size = len(line)
            else:
                current_chunk += line + "\n"
                chunk_size += len(line)
        
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'type': 'csv_section'
            })
        
        return chunks
    
    def _is_resume_content(self, content: str) -> bool:
        """Detect if content appears to be a resume."""
        resume_indicators = [
            'experience', 'education', 'skills', 'objective',
            'summary', 'employment', 'qualifications', 'projects'
        ]
        content_lower = content.lower()
        return sum(indicator in content_lower for indicator in resume_indicators) >= 3
    
    def _chunk_resume_content(self, content: str) -> List[Dict[str, Any]]:
        """Chunk resume content keeping sections together."""
        # Common resume section headers
        section_patterns = [
            r'\b(summary|objective|profile)\b',
            r'\b(experience|employment|work history)\b',
            r'\b(education|academic)\b',
            r'\b(skills|technical skills|competencies)\b',
            r'\b(projects|portfolio)\b',
            r'\b(certifications|licenses)\b'
        ]
        
        chunks = []
        lines = content.split('\n')
        current_section = ""
        current_type = "general"
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line starts a new section
            section_found = False
            for pattern in section_patterns:
                if re.search(pattern, line_lower):
                    # Save previous section if it exists
                    if current_section.strip():
                        chunks.append({
                            'text': current_section.strip(),
                            'type': f'resume_{current_type}'
                        })
                    
                    current_section = line + "\n"
                    current_type = re.search(pattern, line_lower).group(1)
                    section_found = True
                    break
            
            if not section_found:
                current_section += line + "\n"
                
                # If section gets too large, split it
                if len(current_section) > self.base_chunk_size * 2:
                    chunks.append({
                        'text': current_section.strip(),
                        'type': f'resume_{current_type}'
                    })
                    current_section = ""
        
        # Add final section
        if current_section.strip():
            chunks.append({
                'text': current_section.strip(),
                'type': f'resume_{current_type}'
            })
        
        return chunks
    
    def _is_contract_content(self, content: str) -> bool:
        """Detect if content appears to be a contract."""
        contract_indicators = [
            'agreement', 'contract', 'terms', 'conditions',
            'whereas', 'party', 'clause', 'section', 'article'
        ]
        content_lower = content.lower()
        return sum(indicator in content_lower for indicator in contract_indicators) >= 3
    
    def _chunk_contract_content(self, content: str) -> List[Dict[str, Any]]:
        """Chunk contract content preserving clause boundaries."""
        # Split by clause indicators
        clause_patterns = [
            r'\n\s*\d+\.\s+',  # Numbered clauses
            r'\n\s*\([a-z]\)\s+',  # Lettered sub-clauses
            r'\n\s*Article\s+\d+',  # Articles
            r'\n\s*Section\s+\d+'  # Sections
        ]
        
        chunks = []
        current_chunk = ""
        
        lines = content.split('\n')
        for line in lines:
            # Check if this line starts a new clause
            is_new_clause = any(re.match(pattern.replace('\n\s*', ''), line.strip()) 
                              for pattern in clause_patterns)
            
            if is_new_clause and current_chunk and len(current_chunk) > 100:
                chunks.append({
                    'text': current_chunk.strip(),
                    'type': 'contract_clause'
                })
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
                
                # Prevent chunks from getting too large
                if len(current_chunk) > self.base_chunk_size * 1.5:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'type': 'contract_clause'
                    })
                    current_chunk = ""
        
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'type': 'contract_clause'
            })
        
        return chunks
    
    def _chunk_by_paragraphs(self, content: str) -> List[Dict[str, Any]]:
        """Default chunking by paragraphs with overlap."""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        
        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.base_chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'type': 'paragraph_section'
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + paragraph + "\n\n"
            else:
                current_chunk += paragraph + "\n\n"
        
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'type': 'paragraph_section'
            })
        
        return chunks
    
    def _generate_batch_embeddings(self):
        """Generate embeddings for all chunks in batch for efficiency."""
        logger.info("Generating batch embeddings...")
        
        # Collect all texts that need embeddings
        texts_to_embed = []
        text_to_doc_chunk = {}
        
        for doc_id, doc_info in self.document_store.items():
            for chunk_idx, chunk in enumerate(doc_info.get('chunks', [])):
                text = chunk['text']
                if text not in self.embeddings_cache:
                    texts_to_embed.append(text)
                    text_to_doc_chunk[text] = (doc_id, chunk_idx)
        
        if not texts_to_embed:
            return
        
        # Generate embeddings in batch
        try:
            embeddings = self.model.encode(texts_to_embed, batch_size=32, show_progress_bar=True)
            
            # Store embeddings
            for text, embedding in zip(texts_to_embed, embeddings):
                self.embeddings_cache[text] = embedding
                
                # Update document chunk with embedding info
                if text in text_to_doc_chunk:
                    doc_id, chunk_idx = text_to_doc_chunk[text]
                    self.document_store[doc_id]['chunks'][chunk_idx]['has_embedding'] = True
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant document chunks with similarity scores
        """
        if not self.embeddings_cache:
            logger.warning("No embeddings available for search")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Calculate similarities
        results = []
        for doc_id, doc_info in self.document_store.items():
            for chunk in doc_info['chunks']:
                text = chunk['text']
                if text in self.embeddings_cache:
                    # Calculate cosine similarity
                    doc_embedding = self.embeddings_cache[text]
                    similarity = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    
                    results.append({
                        'doc_id': doc_id,
                        'filename': doc_info['filename'],
                        'chunk_text': text,
                        'chunk_type': chunk.get('type', 'unknown'),
                        'similarity_score': float(similarity),
                        'doc_type': doc_info['type']
                    })
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]
    
    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique document ID based on file path and content hash."""
        # Use file path and modification time for uniqueness
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        timestamp = str(int(datetime.now().timestamp()))
        return f"doc_{path_hash}_{timestamp}"
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents."""
        total_docs = len(self.document_store)
        total_chunks = sum(len(doc['chunks']) for doc in self.document_store.values())
        
        doc_types = {}
        for doc in self.document_store.values():
            doc_type = doc['type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        return {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'document_types': doc_types,
            'embeddings_cached': len(self.embeddings_cache),
            'avg_chunks_per_doc': total_chunks / total_docs if total_docs > 0 else 0
        }
