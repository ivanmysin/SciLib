"""External APIs Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class CrossRefResult(BaseModel):
    doi: str
    title: str
    authors: list[str]


@router.get("/crossref/{doi}", response_model=CrossRefResult)
async def fetch_crossref(doi: str):
    """Fetch metadata from CrossRef."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="CrossRef integration not yet implemented"
    )
