import os
from pathlib import Path

# Ensure fast local model loading from cache
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.schemas import ApiResponse
from app.routes.auth_routes import router as auth_router
from app.routes.chat_routes import router as chat_router
from app.routes.document_routes import router as document_router
from app.services.chunking_service import ChunkingService
from app.services.document_metadata_service import DocumentMetadataService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore

# Initialize Singletons
vector_store_instance = VectorStore(settings.indices_dir)
embedding_service_instance = EmbeddingService(settings.embedding_model_name)
chunking_service_instance = ChunkingService(settings.chunk_size, settings.chunk_overlap)
doc_service_instance = DocumentMetadataService(
    vector_store_instance,
    embedding_service_instance,
    chunking_service_instance
)
rag_service_instance = RagService(vector_store_instance, embedding_service_instance)

# FastAPI Application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DocMind: Intelligent AI Document Question-Answering System with RAG",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(auth_router)

# Mount Static Assets & Frontend
frontend_dir = settings.base_dir / "frontend"
static_dir = frontend_dir / "static"
templates_dir = frontend_dir / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/health", response_model=ApiResponse[dict], tags=["System"])
async def health_check():
    """Health check reporting vector store stats and embedding provider status."""
    return ApiResponse[dict](
        success=True,
        message="DocMind Python service is running smoothly.",
        data={
            "status": "UP",
            "version": settings.app_version,
            "embeddingProvider": embedding_service_instance.provider,
            "totalDocuments": len(doc_service_instance.documents),
            "totalChunks": len(vector_store_instance.chunks)
        }
    )

@app.get("/", response_class=HTMLResponse, tags=["Landing"])
async def get_landing():
    """Renders the cinematic public marketing website for DocMind."""
    landing_file = templates_dir / "landing.html"
    if landing_file.exists():
        return HTMLResponse(content=landing_file.read_text(encoding="utf-8"))
    # Fallback to index if landing doesn't exist yet
    index_file = templates_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>DocMind</h1><p>Visit <a href='/app'>/app</a> for the AI workspace or <a href='/docs'>/docs</a> for Swagger UI.</p>")

@app.get("/app", response_class=HTMLResponse, tags=["Application"])
@app.get("/app/", response_class=HTMLResponse, tags=["Application"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Application"])
async def get_app():
    """Renders the full-screen premium dark AI document application."""
    app_file = templates_dir / "app.html"
    if app_file.exists():
        return HTMLResponse(content=app_file.read_text(encoding="utf-8"))
    index_file = templates_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>DocMind App</h1><p>Application template not found. Visit <a href='/docs'>/docs</a>.</p>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
