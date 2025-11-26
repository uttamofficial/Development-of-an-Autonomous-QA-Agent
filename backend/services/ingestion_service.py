"""
Service for ingesting and processing uploaded documents.
"""
import os
from pathlib import Path
from typing import List, Dict
from uuid import uuid4

from backend.core.config import get_settings
from backend.core.parsers import parse_file
from backend.core.chunking import chunk_text
from backend.core.vector_store import VectorStore


class IngestionService:
    """Handles document ingestion and storage."""

    def __init__(self):
        """Initialize the ingestion service."""
        self.settings = get_settings()

        # Ensure directories exist
        os.makedirs(self.settings.uploaded_docs_path, exist_ok=True)
        os.makedirs(self.settings.html_path, exist_ok=True)

        # Initialize vector store
        self.vector_store = VectorStore(
            db_path=self.settings.vector_db_path,
            collection_name=self.settings.chroma_collection_name,
            embedding_model_name=self.settings.embedding_model_name
        )

        # Track processed files
        self.processed_files: List[str] = []

    def save_support_document(self, file_content: bytes, filename: str) -> str:
        """Save uploaded support document into uploaded_docs folder."""
        safe_filename = self._sanitize_filename(filename)
        file_path = os.path.join(self.settings.uploaded_docs_path, safe_filename)

        with open(file_path, 'wb') as f:
            f.write(file_content)

        return file_path

    def save_checkout_html(self, file_content: bytes, filename: str = "checkout.html") -> str:
        """Save checkout.html to data/html folder."""
        file_path = os.path.join(self.settings.html_path, "checkout.html")

        with open(file_path, 'wb') as f:
            f.write(file_content)

        return file_path

    def process_and_store_document(self, file_path: str, doc_type: str = "support_doc") -> Dict:
        """Parse, chunk, and insert document into vector DB."""

        filename = os.path.basename(file_path)

        # Parse document
        try:
            text_content = parse_file(file_path)
        except Exception as e:
            return {"success": False, "filename": filename, "error": str(e)}

        # Chunk
        chunks = chunk_text(
            text_content,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )

        if not chunks:
            return {
                "success": False,
                "filename": filename,
                "error": "No content extracted from document"
            }

        # Prepare docs
        docs_to_store = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{filename}_{i}_{uuid4().hex[:8]}"
            docs_to_store.append({
                "id": doc_id,
                "text": chunk,
                "metadata": {
                    "source_document": filename,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })

        # Store in DB
        try:
            self.vector_store.add_documents(docs_to_store)
            self.processed_files.append(file_path)
            return {
                "success": True,
                "filename": filename,
                "num_chunks": len(chunks),
                "doc_type": doc_type
            }
        except Exception as e:
            return {"success": False, "filename": filename, "error": str(e)}

    def build_knowledge_base(self) -> Dict:
        """Ingest all documents + checkout.html into vector DB."""

        results = {
            "total_documents": 0,
            "total_chunks": 0,
            "support_docs": [],
            "html_files": [],
            "errors": []
        }

        # Process uploaded support docs
        support_docs_path = Path(self.settings.uploaded_docs_path)
        if support_docs_path.exists():
            for file_path in support_docs_path.iterdir():
                if file_path.is_file():
                    result = self.process_and_store_document(str(file_path), "support_doc")
                    if result["success"]:
                        results["total_documents"] += 1
                        results["total_chunks"] += result["num_chunks"]
                        results["support_docs"].append({
                            "filename": result["filename"],
                            "chunks": result["num_chunks"]
                        })
                    else:
                        results["errors"].append(result)

        # Process checkout.html
        html_path = Path(self.settings.html_path) / "checkout.html"
        if html_path.exists():
            result = self.process_and_store_document(str(html_path), "html_structure")
            if result["success"]:
                results["total_documents"] += 1
                results["total_chunks"] += result["num_chunks"]
                results["html_files"].append({
                    "filename": result["filename"],
                    "chunks": result["num_chunks"]
                })
            else:
                results["errors"].append(result)

        return results

    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename."""
        filename = os.path.basename(filename)
        invalid_chars = '<>:"/\\|?*'

        for ch in invalid_chars:
            filename = filename.replace(ch, "_")

        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename
