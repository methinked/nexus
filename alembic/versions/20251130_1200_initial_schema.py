"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('status', sa.Enum('online', 'offline', 'error', name='nodestatus'), nullable=False, index=True),
        sa.Column('metadata', sa.JSON(), nullable=False, default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
    )

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('type', sa.Enum('ocr', 'shell', 'sync', name='jobtype'), nullable=False, index=True),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='jobstatus'), nullable=False, index=True),
        sa.Column('node_id', sa.String(36), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('payload', sa.JSON(), nullable=False, default=dict),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('node_id', sa.String(36), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('cpu_percent', sa.Float(), nullable=False),
        sa.Column('memory_percent', sa.Float(), nullable=False),
        sa.Column('disk_percent', sa.Float(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('metrics')
    op.drop_table('jobs')
    op.drop_table('nodes')
