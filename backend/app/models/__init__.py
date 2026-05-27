"""Scientific Library Database Models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer,
    JSON, LargeBinary, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint,
    event
)
from sqlalchemy.dialects.postgresql import ENUM, INET, TSVECTOR, UUID as PG_UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Enums
class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class ItemSource(str, Enum):
    webdav = "webdav"
    upload = "upload"
    doi_import = "doi_import"
    crossref = "crossref"


class ProcessingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class GroupMemberRole(str, Enum):
    owner = "owner"
    editor = "editor"
    reader = "reader"


# ============================================================================
# USERS & AUTH
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(ENUM(UserRole, name="user_role"), nullable=False, default=UserRole.user)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    storage_quota_bytes: Mapped[int] = mapped_column(Numeric(precision=20), nullable=False, default=10737418240)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    sync_keys: Mapped[List["UserSyncKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    mcp_tokens: Mapped[List["McpToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    groups_owned: Mapped[List["Group"]] = relationship(back_populates="owner", foreign_keys="Group.owner_id")
    group_memberships: Mapped[List["GroupMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    library_items: Mapped[List["LibraryItem"]] = relationship(back_populates="user", foreign_keys="LibraryItem.user_id", cascade="all, delete-orphan")
    added_library_items: Mapped[List["LibraryItem"]] = relationship(back_populates="added_by_user", foreign_keys="LibraryItem.added_by_user_id")
    collections: Mapped[List["Collection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tags: Mapped[List["Tag"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    attachment_blobs: Mapped[List["UserAttachmentBlob"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSyncKey(Base):
    __tablename__ = "user_sync_keys"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_value: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(100))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="sync_keys")

    __table_args__ = (
        Index("idx_sync_keys_active", "key_value", postgresql_where="revoked_at IS NULL"),
    )


class McpToken(Base):
    __tablename__ = "mcp_tokens"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(100))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="mcp_tokens")

    __table_args__ = (
        Index("idx_mcp_tokens_lookup", "token_hash", postgresql_where="revoked_at IS NULL"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


# ============================================================================
# GROUPS
# ============================================================================

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="groups_owned", foreign_keys=[owner_id])
    members: Mapped[List["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    library_items: Mapped[List["LibraryItem"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    collections: Mapped[List["Collection"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    tags: Mapped[List["Tag"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    role: Mapped[GroupMemberRole] = mapped_column(ENUM(GroupMemberRole, name="group_member_role"), nullable=False, default=GroupMemberRole.reader)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="group_memberships")


# ============================================================================
# GLOBAL CATALOG (deduplicated)
# ============================================================================

class Item(Base):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    doi: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    publication_type: Mapped[str] = mapped_column(String(50), nullable=False, default="journalArticle")
    journal_title: Mapped[Optional[str]] = mapped_column(Text)
    publisher: Mapped[Optional[str]] = mapped_column(String(255))
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    volume: Mapped[Optional[str]] = mapped_column(String(50))
    issue: Mapped[Optional[str]] = mapped_column(String(50))
    pages: Mapped[Optional[str]] = mapped_column(String(50))
    url: Mapped[Optional[str]] = mapped_column(Text)
    crossref_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    metadata_source: Mapped[Optional[str]] = mapped_column(String(50))
    metadata_quality: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="item")
    library_items: Mapped[List["LibraryItem"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    embeddings: Mapped[List["DocumentEmbedding"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    citing_citations: Mapped[List["Citation"]] = relationship(
        back_populates="citing_item",
        foreign_keys="Citation.citing_item_id",
        cascade="all, delete-orphan"
    )
    cited_citations: Mapped[List["Citation"]] = relationship(
        back_populates="cited_item",
        foreign_keys="Citation.cited_item_id",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("doi IS NOT NULL OR fingerprint IS NOT NULL", name="check_doi_or_fingerprint"),
        Index("idx_items_authors_gin", "authors", postgresql_using="gin"),
        Index("idx_items_title_trgm", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
    )


# ============================================================================
# ATTACHMENTS (deduplicated by SHA-256)
# ============================================================================

class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    item_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Numeric(precision=20), nullable=False)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    grobid_tei: Mapped[Optional[str]] = mapped_column(Text)  # XML stored as text
    processing_status: Mapped[ProcessingStatus] = mapped_column(ENUM(ProcessingStatus, name="processing_status"), nullable=False, default=ProcessingStatus.pending)
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    item: Mapped[Optional["Item"]] = relationship(back_populates="attachments")
    embeddings: Mapped[List["DocumentEmbedding"]] = relationship(back_populates="attachment", cascade="all, delete-orphan")
    blobs: Mapped[List["UserAttachmentBlob"]] = relationship(back_populates="attachment")

    __table_args__ = (
        Index("idx_attachments_item", "item_id"),
        Index("idx_attachments_status", "processing_status", postgresql_where="processing_status != 'completed'"),
    )


@event.listens_for(Attachment.__table__, "after_create")
def receive_after_create(table, conn, **kw):
    """Create FTS index and tsvector column after table creation."""
    from sqlalchemy import text
    conn.execute(text(
        "ALTER TABLE attachments ADD COLUMN IF NOT EXISTS extracted_text_tsv tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', coalesce(extracted_text, ''))) STORED"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_attachments_fts ON attachments USING gin(extracted_text_tsv)"
    ))


# ============================================================================
# USER ATTACHMENT BLOBS (raw Zotero ZIPs)
# ============================================================================

class UserAttachmentBlob(Base):
    __tablename__ = "user_attachment_blobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    zotero_key: Mapped[str] = mapped_column(String(50), nullable=False)
    blob_path: Mapped[str] = mapped_column(Text, nullable=False)
    blob_size: Mapped[int] = mapped_column(Numeric(precision=20), nullable=False)
    prop_content: Mapped[Optional[str]] = mapped_column(Text)
    attachment_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("attachments.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="attachment_blobs")
    attachment: Mapped[Optional["Attachment"]] = relationship(back_populates="blobs")

    __table_args__ = (
        UniqueConstraint("user_id", "zotero_key", name="uq_user_attachment_blobs_user_zotero"),
    )


# ============================================================================
# LIBRARY ITEMS (user/group ownership + overrides)
# ============================================================================

class LibraryItem(Base):
    __tablename__ = "library_items"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    group_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"))
    title_override: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    added_by: Mapped[ItemSource] = mapped_column(ENUM(ItemSource, name="item_source"), nullable=False, default=ItemSource.upload)
    added_by_user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    item: Mapped["Item"] = relationship(back_populates="library_items")
    user: Mapped[Optional["User"]] = relationship(back_populates="library_items", foreign_keys=[user_id])
    group: Mapped[Optional["Group"]] = relationship(back_populates="library_items")
    added_by_user: Mapped[Optional["User"]] = relationship(foreign_keys=[added_by_user_id])
    collection_items: Mapped[List["LibraryItemCollection"]] = relationship(back_populates="library_item", cascade="all, delete-orphan")
    tags: Mapped[List["LibraryItemTag"]] = relationship(back_populates="library_item", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN group_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="check_library_items_owner"
        ),
        UniqueConstraint("user_id", "item_id", name="uq_library_items_user_item"),
        UniqueConstraint("group_id", "item_id", name="uq_library_items_group_item"),
        Index("idx_library_user_active", "user_id", postgresql_where="is_deleted = FALSE AND user_id IS NOT NULL"),
        Index("idx_library_group_active", "group_id", postgresql_where="is_deleted = FALSE AND group_id IS NOT NULL"),
    )


# ============================================================================
# COLLECTIONS (tree, per-user or per-group)
# ============================================================================

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"))
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    group_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped[Optional["User"]] = relationship(back_populates="collections")
    group: Mapped[Optional["Group"]] = relationship(back_populates="collections")
    parent: Mapped[Optional["Collection"]] = relationship(remote_side="Collection.id", back_populates="children")
    children: Mapped[List["Collection"]] = relationship(back_populates="parent", remote_side=[parent_id])
    collection_items: Mapped[List["LibraryItemCollection"]] = relationship(back_populates="collection", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN group_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="check_collections_owner"
        ),
        Index("idx_collections_parent", "parent_id"),
        Index("idx_collections_user", "user_id"),
        Index("idx_collections_group", "group_id"),
    )


class LibraryItemCollection(Base):
    __tablename__ = "library_item_collections"

    library_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("library_items.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    collection_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    library_item: Mapped["LibraryItem"] = relationship(back_populates="collection_items")
    collection: Mapped["Collection"] = relationship(back_populates="collection_items")


# ============================================================================
# TAGS (per library item)
# ============================================================================

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    group_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"))

    user: Mapped[Optional["User"]] = relationship(back_populates="tags")
    group: Mapped[Optional["Group"]] = relationship(back_populates="tags")
    library_item_tags: Mapped[List["LibraryItemTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN group_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="check_tags_owner"
        ),
        UniqueConstraint("name", "user_id", name="uq_tags_name_user"),
        UniqueConstraint("name", "group_id", name="uq_tags_name_group"),
    )


class LibraryItemTag(Base):
    __tablename__ = "library_item_tags"

    library_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("library_items.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    tag_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    library_item: Mapped["LibraryItem"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="library_item_tags")


# ============================================================================
# EMBEDDINGS
# ============================================================================

class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attachment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("attachments.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_name: Mapped[Optional[str]] = mapped_column(String(100))
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    attachment: Mapped["Attachment"] = relationship(back_populates="embeddings")
    item: Mapped["Item"] = relationship(back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint("attachment_id", "chunk_index", name="uq_document_embeddings_attachment_chunk"),
    )


# ============================================================================
# CITATIONS
# ============================================================================

class Citation(Base):
    __tablename__ = "citations"

    citing_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    cited_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="crossref")
    raw_reference: Mapped[Optional[str]] = mapped_column(Text)

    citing_item: Mapped["Item"] = relationship(back_populates="citing_citations", foreign_keys=[citing_item_id])
    cited_item: Mapped["Item"] = relationship(back_populates="cited_citations", foreign_keys=[cited_item_id])

    __table_args__ = (
        Index("idx_citations_cited", "cited_item_id"),
    )


# ============================================================================
# UNRESOLVED REFERENCES
# ============================================================================

class UnresolvedReference(Base):
    __tablename__ = "unresolved_references"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    citing_item_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    raw_reference: Mapped[str] = mapped_column(Text, nullable=False)
    doi: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ============================================================================
# EXTERNAL API CACHE & SYSTEM
# ============================================================================

class ExternalApiCache(Base):
    __tablename__ = "external_api_cache"

    query_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_cache_expiry", "expires_at"),
    )


class SystemSettings(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


# ============================================================================
# AUDIT LOGS
# ============================================================================

class McpAuditLog(Base):
    __tablename__ = "mcp_audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    mcp_token_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("mcp_tokens.id", ondelete="SET NULL"))
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_arguments: Mapped[Optional[dict]] = mapped_column(JSONB)
    result_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
