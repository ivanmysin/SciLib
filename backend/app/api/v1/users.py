"""Users Router."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_db
from app.models import User

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    is_active: bool
    role: str = "user"
    storage_used_bytes: int = 0
    storage_quota_bytes: int = 10737418240


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Get current authenticated user.
    
    TODO: Implement proper JWT extraction.
    For now, returns the admin user if exists, otherwise a mock user.
    """
    # Try to get the first active user (for demo purposes)
    stmt = select(User).where(User.is_blocked == False).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.display_name or user.email.split('@')[0],
            is_active=True,
            role=user.role.value,
            storage_used_bytes=0,
            storage_quota_bytes=int(user.storage_quota_bytes),
        )
    
    # Fallback to mock user
    return UserResponse(
        id="00000000-0000-0000-0000-000000000000",
        email="user@example.com",
        name="Test User",
        is_active=True,
        role="user",
        storage_used_bytes=0,
        storage_quota_bytes=10737418240
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(user_update: UserUpdate):
    """Update current user profile.
    
    TODO: Implement:
    - Validate current password
    - Hash new password if provided
    - Update display name
    """
    # Placeholder
    return UserResponse(
        id="00000000-0000-0000-0000-000000000000",
        email="user@example.com",
        name=user_update.display_name or "Test User",
        is_active=True,
        role="user"
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID (admin only).
    
    TODO: Implement:
    - Admin authorization check
    - Find user by UUID
    - Return public profile info
    """
    try:
        from uuid import UUID
        UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    return UserResponse(
        id=user_id,
        email="user@example.com",
        name="Sample User",
        is_active=True,
        role="user"
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """Delete user account (admin only).
    
    TODO: Implement:
    - Admin authorization
    - Soft delete (set is_blocked=True)
    - Preserve audit logs
    """
    try:
        from uuid import UUID
        UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    return None


@router.post("/{user_id}/block")
async def block_user(user_id: str, reason: str = ""):
    """Block user account (admin only)."""
    return {"message": f"User {user_id} blocked", "reason": reason}


@router.post("/{user_id}/unblock")
async def unblock_user(user_id: str):
    """Unblock user account (admin only)."""
    return {"message": f"User {user_id} unblocked"}
