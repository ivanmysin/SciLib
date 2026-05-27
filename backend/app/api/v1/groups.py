"""Groups Router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter()


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    member_count: int = 0
    role: Optional[str] = None


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupMemberResponse(BaseModel):
    user_id: str
    email: str
    display_name: Optional[str] = None
    role: str


@router.get("/", response_model=List[GroupResponse])
async def list_groups(limit: int = 50, offset: int = 0):
    """List all groups the current user is a member of."""
    return []


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(group: GroupCreate):
    """Create a new group.
    
    TODO: Implement group creation:
    - Create group record
    - Add creator as owner
    - Return group with member count = 1
    """
    return GroupResponse(
        id="00000000-0000-0000-0000-000000000000",
        name=group.name,
        description=group.description,
        member_count=1,
        role="owner"
    )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str):
    """Get group by ID with membership info."""
    try:
        UUID(group_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID format"
        )
    
    return GroupResponse(
        id=group_id,
        name="Sample Group",
        description="A sample research group",
        member_count=5,
        role="member"
    )


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: str, group: GroupCreate):
    """Update group details (owners only)."""
    try:
        UUID(group_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID format"
        )
    
    return GroupResponse(
        id=group_id,
        name=group.name,
        description=group.description,
        member_count=0,
        role="owner"
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str):
    """Delete a group (owners only)."""
    try:
        UUID(group_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID format"
        )
    
    return None


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def list_group_members(group_id: str):
    """List all members of a group."""
    return []


@router.post("/{group_id}/members/{user_id}")
async def add_member(group_id: str, user_id: str, role: str = "reader"):
    """Add a member to the group."""
    return {"message": f"User {user_id} added to group {group_id} as {role}"}


@router.delete("/{group_id}/members/{user_id}")
async def remove_member(group_id: str, user_id: str):
    """Remove a member from the group."""
    return {"message": f"User {user_id} removed from group {group_id}"}


@router.patch("/{group_id}/members/{user_id}/role")
async def update_member_role(group_id: str, user_id: str, role: str):
    """Update a member's role in the group."""
    return {"message": f"User {user_id} role updated to {role} in group {group_id}"}
