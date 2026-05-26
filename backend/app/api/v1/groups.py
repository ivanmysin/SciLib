"""Groups Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class GroupResponse(BaseModel):
    id: int
    name: str


@router.get("/", response_model=list[GroupResponse])
async def list_groups():
    """List all groups."""
    return []


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int):
    """Get group by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get group not yet implemented"
    )
