"""Admin Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class SystemStatus(BaseModel):
    version: str
    database_connected: bool
    redis_connected: bool


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status."""
    return SystemStatus(
        version="0.1.0",
        database_connected=False,
        redis_connected=False,
    )


@router.post("/reset")
async def reset_system():
    """Reset system (admin only)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="System reset not yet implemented"
    )
