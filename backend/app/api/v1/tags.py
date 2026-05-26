"""Tags Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class TagResponse(BaseModel):
    id: int
    name: str
    color: str


@router.get("/", response_model=list[TagResponse])
async def list_tags():
    """List all tags."""
    return []


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: int):
    """Get tag by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get tag not yet implemented"
    )
