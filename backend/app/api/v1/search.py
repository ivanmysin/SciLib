"""Search Router."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class SearchResult(BaseModel):
    id: int
    title: str
    score: float


@router.get("/", response_model=list[SearchResult])
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search items."""
    return []
