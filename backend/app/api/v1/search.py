"""Search Router."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class SearchResult(BaseModel):
    id: str
    title: str
    item_type: str
    doi: Optional[str] = None
    authors: List[str] = []
    publication_year: Optional[int] = None
    score: float = 1.0
    highlight: Optional[str] = None


class SearchResponse(BaseModel):
    items: List[SearchResult]
    total: int
    limit: int
    offset: int


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    year_from: Optional[int] = Query(None, description="Filter by publication year (from)"),
    year_to: Optional[int] = Query(None, description="Filter by publication year (to)"),
    sort_by: str = Query("relevance", description="Sort by: relevance, year, title"),
):
    """Search items with full-text and semantic search.
    
    TODO: Implement hybrid search:
    - Full-text search using PostgreSQL FTS
    - Semantic search using pgvector embeddings
    - Combine results with weighted scoring
    - Apply filters (type, year)
    - Support pagination
    """
    # Placeholder - return empty results
    return SearchResponse(
        items=[],
        total=0,
        limit=limit,
        offset=offset
    )


@router.get("/suggest", response_model=List[str])
async def search_suggest(
    q: str = Query(..., description="Query for suggestions"),
    limit: int = Query(5, ge=1, le=20),
):
    """Get search suggestions/autocomplete.
    
    TODO: Implement autocomplete:
    - Query title trigram index
    - Return matching prefixes
    """
    # Placeholder
    return []
