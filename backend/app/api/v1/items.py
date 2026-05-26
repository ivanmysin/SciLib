"""Items Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class ItemResponse(BaseModel):
    id: int
    title: str
    item_type: str


@router.get("/", response_model=list[ItemResponse])
async def list_items():
    """List all items."""
    return []


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get item by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get item not yet implemented"
    )
