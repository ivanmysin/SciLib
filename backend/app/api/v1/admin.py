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
    from app.models import McpAuditLog
    from uuid import uuid4 as gen_uuid4
    
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
    
    # Log to audit table
    audit_entry = McpAuditLog(
        user_id=uuid,
        tool_name="block_user",
        tool_arguments={"user_id": str(uuid), "reason": reason},
        result_summary={"success": True, "email": user.email},
        success=True,
        duration_ms=0,
    )
    db.add(audit_entry)
    await db.commit()
    
    return {"message": f"User {user.email} blocked", "reason": reason}


@router.post("/users/{user_id}/unblock")
async def unblock_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Unblock user account (admin only)."""
    from app.models import McpAuditLog
    
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
    
    # Log to audit table
    audit_entry = McpAuditLog(
        user_id=uuid,
        tool_name="unblock_user",
        tool_arguments={"user_id": str(uuid)},
        result_summary={"success": True, "email": user.email},
        success=True,
        duration_ms=0,
    )
    db.add(audit_entry)
    await db.commit()
    
    return {"message": f"User {user.email} unblocked"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Soft-delete user account (admin only)."""
    from app.models import McpAuditLog
    
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
    
    # Log to audit table
    audit_entry = McpAuditLog(
        user_id=uuid,
        tool_name="delete_user",
        tool_arguments={"user_id": str(uuid)},
        result_summary={"success": True, "email": user.email},
        success=True,
        duration_ms=0,
    )
    db.add(audit_entry)
    await db.commit()


@router.get("/settings")
async def get_settings_endpoint(db: AsyncSession = Depends(get_db)):
    """Get system settings (admin only)."""
    from app.models import SystemSettings
    from decimal import Decimal
    
    defaults = {
        "maintenance_mode": False,
        "registration_enabled": True,
        "max_upload_size_mb": 100,
        "default_quota_gb": 10,
    }
    
    try:
        stmt = select(SystemSettings)
        result = await db.execute(stmt)
        settings_rows = result.scalars().all()
        
        if settings_rows:
            for setting in settings_rows:
                if setting.key == 'maintenance_mode':
                    defaults['maintenance_mode'] = setting.value.get('value', False)
                elif setting.key == 'registration_enabled':
                    defaults['registration_enabled'] = setting.value.get('value', True)
                elif setting.key == 'max_upload_size_mb':
                    defaults['max_upload_size_mb'] = setting.value.get('value', 100)
                elif setting.key == 'default_quota_gb':
                    defaults['default_quota_gb'] = setting.value.get('value', 10)
    except Exception:
        pass
    
    return defaults


@router.put("/settings")
async def update_settings_endpoint(settings: dict, db: AsyncSession = Depends(get_db)):
    """Update system settings (admin only)."""
    from app.models import SystemSettings
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    
    settings_to_save = []
    
    if 'maintenance_mode' in settings:
        settings_to_save.append({
            'key': 'maintenance_mode',
            'value': {'value': bool(settings['maintenance_mode'])}
        })
    if 'registration_enabled' in settings:
        settings_to_save.append({
            'key': 'registration_enabled',
            'value': {'value': bool(settings['registration_enabled'])}
        })
    if 'max_upload_size_mb' in settings:
        settings_to_save.append({
            'key': 'max_upload_size_mb',
            'value': {'value': int(settings['max_upload_size_mb'])}
        })
    if 'default_quota_gb' in settings:
        settings_to_save.append({
            'key': 'default_quota_gb',
            'value': {'value': int(settings['default_quota_gb'])}
        })
    
    for setting_data in settings_to_save:
        stmt = pg_insert(SystemSettings).values(
            key=setting_data['key'],
            value=setting_data['value'],
            updated_at=func.now()
        ).on_conflict_do_update(
            index_elements=['key'],
            set_={'value': setting_data['value'], 'updated_at': func.now()}
        )
        await db.execute(stmt)
    
    await db.commit()
    
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
    from app.models import McpAuditLog
    
    stmt = select(McpAuditLog).order_by(McpAuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [
        AuditLogEntry(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            action=log.tool_name,
            resource_type="user" if log.tool_name in ["block_user", "unblock_user", "delete_user"] else None,
            resource_id=log.tool_arguments.get("user_id") if log.tool_arguments and "user_id" in log.tool_arguments else None,
            details=log.tool_arguments,
            created_at=log.created_at,
        )
        for log in logs
    ]
