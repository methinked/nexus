"""add services and deployments tables for docker orchestration

Revision ID: b09d2be4df10
Revises: 002
Create Date: 2025-12-01 20:49:37.097914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b09d2be4df10'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create services and deployments tables for Docker orchestration (Phase 7)."""

    # Create services table
    op.create_table(
        'services',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='general'),
        sa.Column('docker_compose', sa.Text(), nullable=False),
        sa.Column('default_env', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create indexes for services
    op.create_index('ix_services_name', 'services', ['name'])
    op.create_index('ix_services_category', 'services', ['category'])

    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='deploying'),
        sa.Column('service_id', sa.String(36), sa.ForeignKey('services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.String(36), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('container_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
    )

    # Create indexes for deployments
    op.create_index('ix_deployments_name', 'deployments', ['name'])
    op.create_index('ix_deployments_status', 'deployments', ['status'])
    op.create_index('ix_deployments_service_id', 'deployments', ['service_id'])
    op.create_index('ix_deployments_node_id', 'deployments', ['node_id'])
    op.create_index('ix_deployments_container_id', 'deployments', ['container_id'])
    op.create_index('ix_deployments_created_at', 'deployments', ['created_at'])


def downgrade() -> None:
    """Drop services and deployments tables."""

    # Drop deployments table first (due to foreign key constraint)
    op.drop_index('ix_deployments_created_at', 'deployments')
    op.drop_index('ix_deployments_container_id', 'deployments')
    op.drop_index('ix_deployments_node_id', 'deployments')
    op.drop_index('ix_deployments_service_id', 'deployments')
    op.drop_index('ix_deployments_status', 'deployments')
    op.drop_index('ix_deployments_name', 'deployments')
    op.drop_table('deployments')

    # Drop services table
    op.drop_index('ix_services_category', 'services')
    op.drop_index('ix_services_name', 'services')
    op.drop_table('services')
