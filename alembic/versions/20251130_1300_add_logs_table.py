"""add logs table

Revision ID: 002
Revises: 001
Create Date: 2025-11-30 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add logs table for centralized logging."""
    op.create_table(
        'logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('node_id', sa.String(36), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create indexes for efficient queries
    op.create_index('ix_logs_node_id', 'logs', ['node_id'])
    op.create_index('ix_logs_timestamp', 'logs', ['timestamp'])
    op.create_index('ix_logs_level', 'logs', ['level'])
    op.create_index('ix_logs_source', 'logs', ['source'])


def downgrade() -> None:
    """Remove logs table."""
    op.drop_index('ix_logs_source', table_name='logs')
    op.drop_index('ix_logs_level', table_name='logs')
    op.drop_index('ix_logs_timestamp', table_name='logs')
    op.drop_index('ix_logs_node_id', table_name='logs')
    op.drop_table('logs')
