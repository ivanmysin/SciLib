"""Collections Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter()


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    item_count: int = 0


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None


@router.get("/", response_model=List[CollectionResponse])
async def list_collections(
    limit: int = 50,
    offset: int = 0,
):
    """List all collections.
    
    TODO: Implement database query with:
    - Pagination
    - Hierarchical structure (parent/child)
    - Item count per collection
    """
    return []


@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(collection: CollectionCreate):
    """Create a new collection.
    
    TODO: Implement collection creation:
    - Validate parent_id if provided
    - Check for duplicate names
    - Store in database
    """
    # Placeholder
    return CollectionResponse(
        id="00000000-0000-0000-0000-000000000000",
        name=collection.name,
        description=collection.description,
        item_count=0
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: str):
    """Get collection by ID.
    
    TODO: Implement database lookup:
    - Find collection by UUID
    - Include item count
    - Include child collections
    """
    try:
        UUID(collection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid collection ID format"
        )
    
    return CollectionResponse(
        id=collection_id,
        name="Sample Collection",
        description="A sample collection",
        item_count=5
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(collection_id: str, collection: CollectionCreate):
    """Update an existing collection."""
    try:
        UUID(collection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid collection ID format"
        )
    
    return CollectionResponse(
        id=collection_id,
        name=collection.name,
        description=collection.description,
        item_count=0
    )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(collection_id: str):
    """Delete a collection (soft delete)."""
    try:
        UUID(collection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid collection ID format"
        )
    
    return None


@router.get("/{collection_id}/items")
async def get_collection_items(collection_id: str, limit: int = 50, offset: int = 0):
    """Get items in a collection."""
    return []


@router.post("/{collection_id}/items/{item_id}")
async def add_item_to_collection(collection_id: str, item_id: str):
    """Add an item to a collection."""
    return {"message": f"Item {item_id} added to collection {collection_id}"}


@router.delete("/{collection_id}/items/{item_id}")
async def remove_item_from_collection(collection_id: str, item_id: str):
    """Remove an item from a collection."""
    return {"message": f"Item {item_id} removed from collection {collection_id}"}
