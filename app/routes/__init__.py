from app.routes.document_routes import router as document_router
from app.routes.chat_routes import router as chat_router
from app.routes.auth_routes import router as auth_router

__all__ = ["document_router", "chat_router", "auth_router"]
