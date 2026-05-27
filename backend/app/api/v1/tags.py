"""Tags Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter()


class TagResponse(BaseModel):
    id: str
    name: str
    color: str = "#3b82f6"
    item_count: int = 0


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"


@router.get("/", response_model=List[TagResponse])
async def list_tags(limit: int = 100, offset: int = 0):
    """List all tags for the current user.
    
    TODO: Implement:
    - Query tags from database
    - Include item count per tag
    - Support pagination
    """
    return []


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(tag: TagCreate):
    """Create a new tag.
    
    TODO: Implement:
    - Validate color format (#RRGGBB)
    - Check for duplicate names
    - Store in database
    """
    # Validate hex color
    color = tag.color or "#3b82f6"
    if not color.startswith("#") or len(color) != 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid color format. Use #RRGGBB"
        )
    
    return TagResponse(
        id="00000000-0000-0000-0000-000000000000",
        name=tag.name,
        color=color,
        item_count=0
    )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str):
    """Get tag by ID.
    
    TODO: Implement database lookup with item count.
    """
    try:
        UUID(tag_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tag ID format"
        )
    
    return TagResponse(
        id=tag_id,
        name="Sample Tag",
        color="#3b82f6",
        item_count=5
    )


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, tag: TagCreate):
    """Update an existing tag."""
    try:
        UUID(tag_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tag ID format"
        )
    
    return TagResponse(
        id=tag_id,
        name=tag.name,
        color=tag.color or "#3b82f6",
        item_count=0
    )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str):
    """Delete a tag (does not remove from items)."""
    try:
        UUID(tag_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tag ID format"
        )
    
    return None


@router.get("/{tag_id}/items")
async def get_tagged_items(tag_id: str, limit: int = 50, offset: int = 0):
    """Get all items with this tag."""
    return []
