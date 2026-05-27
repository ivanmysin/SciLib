"""External APIs Router."""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class CrossRefResult(BaseModel):
    doi: str
    title: str
    authors: List[str] = []
    published: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None


class CrossRefSearchResult(BaseModel):
    items: List[CrossRefResult]
    total: int


@router.get("/crossref/{doi}", response_model=CrossRefResult)
async def fetch_crossref(doi: str):
    """Fetch metadata from CrossRef by DOI.
    
    TODO: Implement:
    - Call CrossRef REST API
    - Parse response
    - Cache result in external_api_cache table
    - Handle rate limiting
    """
    # Placeholder implementation
    return CrossRefResult(
        doi=doi,
        title=f"Paper: {doi}",
        authors=["Author One", "Author Two"],
        published="2024-01-01",
        journal="Sample Journal",
        publisher="Sample Publisher",
        url=f"https://doi.org/{doi}"
    )


@router.get("/crossref", response_model=CrossRefSearchResult)
async def search_crossref(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search CrossRef for papers.
    
    TODO: Implement:
    - Call CrossRef search API
    - Parse and transform results
    - Support pagination
    """
    # Placeholder
    return CrossRefSearchResult(
        items=[],
        total=0
    )


@router.get("/arxiv/{arxiv_id}")
async def fetch_arxiv(arxiv_id: str):
    """Fetch metadata from arXiv.
    
    TODO: Implement arXiv API integration.
    """
    return {
        "arxiv_id": arxiv_id,
        "title": f"arXiv:{arxiv_id}",
        "authors": [],
        "abstract": None,
        "published": None,
        "url": f"https://arxiv.org/abs/{arxiv_id}"
    }


@router.get("/doi/resolve/{doi}")
async def resolve_doi(doi: str):
    """Resolve DOI to URL via doi.org.
    
    TODO: Implement DOI resolution.
    """
    return {
        "doi": doi,
        "url": f"https://doi.org/{doi}",
        "resolved": True
    }
