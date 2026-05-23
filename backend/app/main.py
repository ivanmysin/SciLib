"""Scientific Library Backend - FastAPI Application."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import engine, Base
from app.api.v1 import auth, items, collections, groups, search, admin, users, tags, external

logger = structlog.get_logger()
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Scientific Library API",
        description="Private multi-user scientific PDF storage with metadata extraction and hybrid search",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/admin/users", tags=["admin-users"])
    app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
    app.include_router(collections.router, prefix="/api/v1/collections", tags=["collections"])
    app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(tags.router, prefix="/api/v1", tags=["tags"])
    app.include_router(external.router, prefix="/api/v1/external", tags=["external"])

    @app.on_event("startup")
    async def startup():
        """Application startup events."""
        logger.info("Application starting up")
        # Note: In production, migrations should be run separately or via init container

    @app.on_event("shutdown")
    async def shutdown():
        """Application shutdown events."""
        logger.info("Application shutting down")
        await engine.dispose()

    return app


app = create_app()
