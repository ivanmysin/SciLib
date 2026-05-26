"""Users Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    """Get current authenticated user."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get current user not yet implemented"
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get user not yet implemented"
    )
