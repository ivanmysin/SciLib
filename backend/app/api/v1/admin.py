"""Admin Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SystemStatus(BaseModel):
    version: str
    database_connected: bool
    redis_connected: bool
    grobid_connected: bool
    worker_running: bool


class UserStats(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int


class StorageStats(BaseModel):
    total_bytes: int
    used_bytes: int
    file_count: int


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status.
    
    TODO: Implement health checks:
    - Database connection test
    - Redis ping
    - GROBID service check
    - Worker queue status
    """
    return SystemStatus(
        version="0.1.0",
        database_connected=False,
        redis_connected=False,
        grobid_connected=False,
        worker_running=False,
    )


@router.get("/stats/users", response_model=UserStats)
async def get_user_stats():
    """Get user statistics (admin only)."""
    return UserStats(
        total_users=0,
        active_users=0,
        blocked_users=0
    )


@router.get("/stats/storage", response_model=StorageStats)
async def get_storage_stats():
    """Get storage statistics (admin only)."""
    return StorageStats(
        total_bytes=0,
        used_bytes=0,
        file_count=0
    )


@router.post("/reset")
async def reset_system(dry_run: bool = True):
    """Reset system (admin only).
    
    WARNING: This is a dangerous operation!
    
    TODO: Implement with extreme caution:
    - Require admin authentication
    - Support dry-run mode
    - Create backup before reset
    - Log all actions to audit table
    """
    if not dry_run:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="System reset not yet implemented"
        )
    
    return {"message": "Dry run - no changes made"}


@router.get("/settings")
async def get_settings():
    """Get system settings (admin only)."""
    return {
        "maintenance_mode": False,
        "registration_enabled": True,
        "max_upload_size_mb": 100,
        "default_quota_gb": 10
    }


@router.put("/settings")
async def update_settings(settings: dict):
    """Update system settings (admin only)."""
    # Placeholder
    return {"message": "Settings updated", "settings": settings}
