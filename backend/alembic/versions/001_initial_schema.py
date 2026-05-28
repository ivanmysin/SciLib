"""Initial schema - create all tables

Revision ID: 001
Revises: 
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    sa.Enum('admin', 'user', name='user_role').create(op.get_bind())
    sa.Enum('webdav', 'upload', 'doi_import', 'crossref', name='item_source').create(op.get_bind())
    sa.Enum('pending', 'processing', 'completed', 'failed', name='processing_status').create(op.get_bind())
    sa.Enum('owner', 'editor', 'reader', name='group_member_role').create(op.get_bind())
    
    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('role', postgresql.ENUM('admin', 'user', name='user_role'), nullable=False),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, default=False),
        sa.Column('storage_quota_bytes', sa.Numeric(precision=20), nullable=False, default=10737418240),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # System settings table
    op.create_table('system_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )
    
    # MCP audit log table
    op.create_table('mcp_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mcp_token_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('tool_arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Insert default system settings
    op.execute("""
        INSERT INTO system_settings (key, value, updated_at) VALUES
        ('maintenance_mode', 'false', now()),
        ('registration_enabled', 'true', now()),
        ('max_upload_size_mb', '100', now()),
        ('default_quota_gb', '10', now())
    """)
    
    # Create seed admin user (password: admin123)
    op.execute("""
        INSERT INTO users (id, email, password_hash, display_name, role, is_blocked, storage_quota_bytes, created_at, updated_at)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'admin@scilib.local',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
            'System Administrator',
            'admin',
            false,
            107374182400,
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('mcp_audit_log')
    op.drop_table('system_settings')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    sa.Enum(name='user_role').drop(op.get_bind())
    sa.Enum(name='item_source').drop(op.get_bind())
    sa.Enum(name='processing_status').drop(op.get_bind())
    sa.Enum(name='group_member_role').drop(op.get_bind())
