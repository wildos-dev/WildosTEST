"""Add missing tables: node_peak_events, node_tokens, failed_auth_attempts

Revision ID: 20250911_add_missing_tables
Revises: 003_add_default_settings
Create Date: 2025-09-11 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250911_add_missing_tables'
down_revision = '003_add_default_settings'
branch_labels = None
depends_on = None


def upgrade():
    """Add node_peak_events table for peak monitoring"""
    
    # Create peak_level enum values (will be handled as strings in SQLite)
    peak_level_enum = sa.Enum('WARNING', 'CRITICAL', name='peak_level')
    peak_category_enum = sa.Enum('CPU', 'MEMORY', 'DISK', 'NETWORK', 'BACKEND', name='peak_category')
    
    # Create node_peak_events table (only this table is missing, others already exist from 001_initial_schema)
    op.create_table('node_peak_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('category', peak_category_enum, nullable=False, server_default='CPU'),
        sa.Column('metric', sa.String(length=64), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('level', peak_level_enum, nullable=False, server_default='WARNING'),
        sa.Column('dedupe_key', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('context_json', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('seq', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_id', 'seq'),
        sa.UniqueConstraint('node_id', 'dedupe_key', 'started_at')
    )
    
    # Create indexes for node_peak_events
    op.create_index('ix_node_peak_events_node_id', 'node_peak_events', ['node_id'])
    op.create_index('ix_node_peak_events_node_started', 'node_peak_events', ['node_id', 'started_at'])


def downgrade():
    """Remove the node_peak_events table"""
    
    # Drop indexes first
    op.drop_index('ix_node_peak_events_node_started', table_name='node_peak_events')
    op.drop_index('ix_node_peak_events_node_id', table_name='node_peak_events')
    
    # Drop the table
    op.drop_table('node_peak_events')
    
    # Note: Enum types are handled automatically in SQLAlchemy