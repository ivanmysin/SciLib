"""Items Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter()


class ItemResponse(BaseModel):
    id: str
    title: str
    item_type: str
    doi: Optional[str] = None
    authors: List[str] = []
    publication_year: Optional[int] = None


class ItemCreate(BaseModel):
    title: str
    item_type: str = "journalArticle"
    doi: Optional[str] = None
    authors: List[str] = []
    abstract: Optional[str] = None


@router.get("/", response_model=List[ItemResponse])
async def list_items(
    limit: int = 20,
    offset: int = 0,
):
    """List all items with pagination.
    
    TODO: Implement database query with:
    - Pagination support
    - Filtering by type/year
    - Sorting options
    """
    # Placeholder - return empty list
    return []


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """Create a new item.
    
    TODO: Implement item creation:
    - Validate DOI if provided
    - Fetch metadata from CrossRef if DOI present
    - Store in database
    - Trigger PDF processing if attachment provided
    """
    # Placeholder implementation
    return ItemResponse(
        id="00000000-0000-0000-0000-000000000000",
        title=item.title,
        item_type=item.item_type,
        doi=item.doi,
        authors=item.authors,
        publication_year=None
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get item by ID.
    
    TODO: Implement database lookup:
    - Find item by UUID
    - Include related attachments
    - Include collections/tags
    """
    # Validate UUID format
    try:
        UUID(item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID format"
        )
    
    # Placeholder - return mock data
    return ItemResponse(
        id=item_id,
        title="Sample Item",
        item_type="journalArticle",
        doi="10.1234/example",
        authors=["Author One", "Author Two"],
        publication_year=2024
    )


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item: ItemCreate):
    """Update an existing item.
    
    TODO: Implement item update:
    - Verify item exists
    - Update fields
    - Re-process if DOI changed
    """
    # Placeholder
    return ItemResponse(
        id=item_id,
        title=item.title,
        item_type=item.item_type,
        doi=item.doi,
        authors=item.authors,
        publication_year=None
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    """Delete an item.
    
    TODO: Implement soft delete:
    - Mark as deleted in library_items
    - Remove from user collections
    - Keep global catalog entry
    """
    # Placeholder - just return success
    return None
