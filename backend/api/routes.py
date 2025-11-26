"""
API routes for the QA Agent.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os

from backend.services.ingestion_service import IngestionService
from backend.services.rag_service import RAGService
from backend.services.selenium_service import SeleniumService
from backend.models.test_case import TestCaseRequest, TestCaseResponse, TestCase

router = APIRouter()
ingestion_service = IngestionService()

# Lazy initialization for RAG service (uses dummy local LLM - no API key needed)
_rag_service = None

def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

# Lazy initialization for Selenium service (uses dummy local LLM - no API key needed)
_selenium_service = None

def get_selenium_service() -> SeleniumService:
    """Get or create Selenium service instance."""
    global _selenium_service
    if _selenium_service is None:
        _selenium_service = SeleniumService()
    return _selenium_service


@router.post("/upload-docs")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload multiple support documents.
    
    Args:
        files: List of uploaded files
        
    Returns:
        Dictionary with upload results
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = {
        "uploaded": [],
        "failed": []
    }
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            
            # Save file
            file_path = ingestion_service.save_support_document(content, file.filename)
            
            results["uploaded"].append({
                "filename": file.filename,
                "saved_path": file_path
            })
        except Exception as e:
            results["failed"].append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "message": f"Processed {len(results['uploaded'])} files",
        "results": results
    }


@router.post("/upload-html")
async def upload_html(file: UploadFile = File(...)):
    """
    Upload checkout.html file.
    
    Args:
        file: Uploaded HTML file
        
    Returns:
        Dictionary with upload result
    """
    try:
        # Read file content
        content = await file.read()
        
        # Save file
        file_path = ingestion_service.save_checkout_html(content, file.filename)
        
        return {
            "message": "HTML file uploaded successfully",
            "filename": "checkout.html",
            "saved_path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading HTML: {str(e)}")


@router.post("/build-knowledge-base")
async def build_knowledge_base():
    """
    Build knowledge base from all uploaded documents and checkout.html.
    
    This will:
    1. Parse all documents in data/uploaded_docs
    2. Parse checkout.html in data/html
    3. Chunk all content
    4. Store chunks in vector database
    
    Returns:
        Dictionary with summary of knowledge base building
    """
    try:
        summary = ingestion_service.build_knowledge_base()
        
        return {
            "message": "Knowledge base built successfully",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building knowledge base: {str(e)}"
        )


@router.post("/generate-test-cases", response_model=TestCaseResponse)
async def generate_test_cases(request: TestCaseRequest):
    """
    Generate test cases using RAG.
    
    Args:
        request: TestCaseRequest with user query
        
    Returns:
        TestCaseResponse with list of generated test cases
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        rag_service = get_rag_service()
        test_cases = rag_service.generate_test_cases(request.query)
        
        return TestCaseResponse(test_cases=test_cases)
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating test cases: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/generate-selenium-script")
async def generate_selenium_script(test_case: TestCase):
    """
    Generate Selenium script for a test case.
    
    Args:
        test_case: TestCase object (sent in request body)
        
    Returns:
        Dictionary with generated Python script
    """
    try:
        selenium_service = get_selenium_service()
        script = selenium_service.generate_selenium_script(test_case)
        
        return {
            "script": script
        }
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Selenium script: {str(e)}"
        )
