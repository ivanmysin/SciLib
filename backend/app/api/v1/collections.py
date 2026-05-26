"""Collections Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class CollectionResponse(BaseModel):
    id: int
    name: str


@router.get("/", response_model=list[CollectionResponse])
async def list_collections():
    """List all collections."""
    return []


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: int):
    """Get collection by ID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get collection not yet implemented"
    )
