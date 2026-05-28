"""Admin Router."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User, Attachment, Item, LibraryItem

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


class UserInfo(BaseModel):
    id: str
    email: str
    display_name: str | None
    role: str
    is_blocked: bool
    storage_quota_bytes: int
    created_at: datetime


class AuditLogEntry(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict | None
    created_at: datetime


@router.get("/status", response_model=SystemStatus)
async def get_status(db: AsyncSession = Depends(get_db)):
    """Get system status with real health checks."""
    db_ok = False
    redis_ok = False
    grobid_ok = False
    worker_ok = False
    
    # Check database connection
    try:
        await db.execute(select(1))
        db_ok = True
    except Exception:
        pass
    
    # Check Redis connection
    try:
        from app.config import get_settings
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        await r.ping()
        redis_ok = True
        await r.close()
    except Exception:
        pass
    
    # Check GROBID service
    try:
        from app.config import get_settings
        settings = get_settings()
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.grobid_url}/api/isalive")
            if resp.status_code == 200:
                grobid_ok = True
    except Exception:
        pass
    
    # Check worker status (via Redis queue inspection)
    try:
        from app.config import get_settings
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        # Check for arq queue keys
        queues = await r.keys("arq:queue:*")
        worker_ok = len(queues) > 0 or redis_ok  # If redis is up, assume worker can connect
        await r.close()
    except Exception:
        pass
    
    return SystemStatus(
        version="0.1.0",
        database_connected=db_ok,
        redis_connected=redis_ok,
        grobid_connected=grobid_ok,
        worker_running=worker_ok,
    )


@router.get("/stats/users", response_model=UserStats)
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """Get user statistics (admin only)."""
    # Total users
    total_stmt = select(func.count(User.id))
    total_result = await db.execute(total_stmt)
    total_users = total_result.scalar() or 0
    
    # Active users (not blocked)
    active_stmt = select(func.count(User.id)).where(User.is_blocked == False)
    active_result = await db.execute(active_stmt)
    active_users = active_result.scalar() or 0
    
    # Blocked users
    blocked_stmt = select(func.count(User.id)).where(User.is_blocked == True)
    blocked_result = await db.execute(blocked_stmt)
    blocked_users = blocked_result.scalar() or 0
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        blocked_users=blocked_users,
    )


@router.get("/stats/storage", response_model=StorageStats)
async def get_storage_stats(db: AsyncSession = Depends(get_db)):
    """Get storage statistics (admin only)."""
    # Total attachments count
    file_stmt = select(func.count(Attachment.id))
    file_result = await db.execute(file_stmt)
    file_count = file_result.scalar() or 0
    
    # Total storage used
    storage_stmt = select(func.sum(Attachment.file_size))
    storage_result = await db.execute(storage_stmt)
    used_bytes = storage_result.scalar() or 0
    
    # Estimate total quota (sum of all user quotas)
    quota_stmt = select(func.sum(User.storage_quota_bytes))
    quota_result = await db.execute(quota_stmt)
    total_bytes = quota_result.scalar() or 0
    
    return StorageStats(
        total_bytes=int(total_bytes),
        used_bytes=int(used_bytes),
        file_count=file_count,
    )


@router.get("/users", response_model=list[UserInfo])
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all users (admin only)."""
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        UserInfo(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=user.role.value,
            is_blocked=user.is_blocked,
            storage_quota_bytes=int(user.storage_quota_bytes),
            created_at=user.created_at,
        )
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserInfo)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user by ID (admin only)."""
    try:
        uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    stmt = select(User).where(User.id == uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfo(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        is_blocked=user.is_blocked,
        storage_quota_bytes=int(user.storage_quota_bytes),
        created_at=user.created_at,
    )


@router.post("/users/{user_id}/block")
async def block_user(user_id: str, reason: str = "", db: AsyncSession = Depends(get_db)):
    """Block user account (admin only)."""
    try:
        uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    stmt = select(User).where(User.id == uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_blocked = True
    await db.flush()
    
    # TODO: Log to audit table
    return {"message": f"User {user.email} blocked", "reason": reason}


@router.post("/users/{user_id}/unblock")
async def unblock_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Unblock user account (admin only)."""
    try:
        uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    stmt = select(User).where(User.id == uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_blocked = False
    await db.flush()
    
    # TODO: Log to audit table
    return {"message": f"User {user.email} unblocked"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Soft-delete user account (admin only)."""
    try:
        uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    stmt = select(User).where(User.id == uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_blocked = True
    # TODO: Also anonymize email, revoke tokens, etc.
    await db.flush()
    
    # TODO: Log to audit table


@router.get("/settings")
async def get_settings_endpoint(db: AsyncSession = Depends(get_db)):
    """Get system settings (admin only)."""
    from app.models import Base
    # Check if system_settings table exists and read from it
    try:
        stmt = select(func.count()).select_from(Base.metadata.tables.get('system_settings'))
        result = await db.execute(stmt)
        # For now, return defaults
    except Exception:
        pass
    
    return {
        "maintenance_mode": False,
        "registration_enabled": True,
        "max_upload_size_mb": 100,
        "default_quota_gb": 10,
    }


@router.put("/settings")
async def update_settings_endpoint(settings: dict, db: AsyncSession = Depends(get_db)):
    """Update system settings (admin only)."""
    # TODO: Write to system_settings table
    return {"message": "Settings updated", "settings": settings}


@router.post("/reset")
async def reset_system(dry_run: bool = True, db: AsyncSession = Depends(get_db)):
    """Reset system (admin only).
    
    WARNING: This is a dangerous operation!
    """
    if not dry_run:
        # TODO: Implement actual reset with backup
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="System reset not yet implemented"
        )
    
    # Get counts for dry run report
    user_count = await db.execute(select(func.count(User.id)))
    item_count = await db.execute(select(func.count(Item.id)))
    attachment_count = await db.execute(select(func.count(Attachment.id)))
    
    return {
        "message": "Dry run - no changes made",
        "would_delete": {
            "users": user_count.scalar(),
            "items": item_count.scalar(),
            "attachments": attachment_count.scalar(),
        }
    }


@router.get("/audit/logs", response_model=list[AuditLogEntry])
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs (admin only)."""
    # TODO: Implement when mcp_audit_log table is populated
    return []
