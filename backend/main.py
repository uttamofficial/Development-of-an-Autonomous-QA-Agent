"""
FastAPI entrypoint for the QA Agent backend.
"""
import os

# Disable ChromaDB telemetry BEFORE any imports that might use it
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["OTEL_SDK_DISABLED"] = "true"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(
    title="QA Agent API",
    version="1.0.0",
    description="Autonomous QA Agent for Test Case and Script Generation"
)

# CORS middleware (useful for Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "QA Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "api": "/api"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
