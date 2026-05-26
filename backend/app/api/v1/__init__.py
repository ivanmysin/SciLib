"""API v1 Router Module."""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .items import router as items_router
from .collections import router as collections_router
from .groups import router as groups_router
from .search import router as search_router
from .admin import router as admin_router
from .tags import router as tags_router
from .external import router as external_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(items_router, prefix="/items", tags=["Items"])
router.include_router(collections_router, prefix="/collections", tags=["Collections"])
router.include_router(groups_router, prefix="/groups", tags=["Groups"])
router.include_router(search_router, prefix="/search", tags=["Search"])
router.include_router(admin_router, prefix="/admin", tags=["Admin"])
router.include_router(tags_router, prefix="/tags", tags=["Tags"])
router.include_router(external_router, prefix="/external", tags=["External"])

__all__ = ["router"]
