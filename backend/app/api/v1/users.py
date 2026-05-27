"""Users Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional

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
async def get_current_user():
    """Get current authenticated user.
    
    TODO: Implement:
    - Extract user from JWT token
    - Query database for user details
    - Include storage usage stats
    """
    # Placeholder - mock user
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
