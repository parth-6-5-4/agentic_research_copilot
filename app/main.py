"""
Agentic Research Copilot - FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import research_router, runs_router, feedback_router, export_router
from app.db import init_db
from app.core import settings, logger
from app.tools import check_ollama, chroma_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Agentic Research Copilot...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Check Ollama availability
    ollama_status = await check_ollama()
    if ollama_status["available"]:
        logger.info(f"Ollama connected: {ollama_status['model']}")
    else:
        logger.warning(
            f"Ollama not available at {ollama_status['base_url']}. "
            "Run 'ollama serve' to enable LLM features."
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Agentic Research Copilot",
    description="""
    An AI-powered research assistant that:
    - Takes a research objective
    - Searches academic sources (arXiv, Semantic Scholar, Wikipedia)
    - Synthesizes a structured report with citations
    - Identifies gaps and contradictions
    
    Optimized for local execution on MacBook Pro M2 (8GB RAM).
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research_router)
app.include_router(runs_router)
app.include_router(feedback_router)
app.include_router(export_router)


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "name": "Agentic Research Copilot",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    ollama_status = await check_ollama()
    
    try:
        chroma = chroma_stats()
    except Exception:
        chroma = {"error": "ChromaDB not initialized"}
    
    return {
        "status": "healthy",
        "components": {
            "ollama": ollama_status,
            "chromadb": chroma,
            "database": "connected",
        },
        "config": {
            "model": settings.ollama_model,
            "context_window": settings.ollama_num_ctx,
            "embedding_model": settings.embedding_model,
        }
    }
