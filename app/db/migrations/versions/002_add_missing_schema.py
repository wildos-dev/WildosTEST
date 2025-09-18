"""Add missing schema - certificates and log tables

Revision ID: 002_add_missing_schema
Revises: 001_initial_schema
Create Date: 2025-01-09 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_missing_schema'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing certificate columns to nodes table
    try:
        op.add_column('nodes', sa.Column('certificate', sa.Text(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('nodes', sa.Column('private_key', sa.Text(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('nodes', sa.Column('cert_created_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('nodes', sa.Column('cert_expires_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    # Create user_usage_logs table
    try:
        op.create_table('user_usage_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('created_time', sa.DateTime(), nullable=False),
            sa.Column('usage_data', sa.BigInteger(), nullable=True),
            sa.Column('node_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table might already exist
    
    # Create notification_reports table
    try:
        op.create_table('notification_reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('notification_type', sa.String(length=64), nullable=False),
            sa.Column('recipient', sa.String(length=256), nullable=False),
            sa.Column('subject', sa.String(length=512), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table might already exist
    
    # Create backend_logs table  
    try:
        op.create_table('backend_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('node_id', sa.Integer(), nullable=True),
            sa.Column('backend_name', sa.String(length=64), nullable=False),
            sa.Column('log_level', sa.String(length=16), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table might already exist


def downgrade():
    # Drop tables in reverse order
    op.drop_table('backend_logs')
    op.drop_table('notification_reports')
    op.drop_table('user_usage_logs')
    
    # Remove certificate columns from nodes table
    op.drop_column('nodes', 'cert_expires_at')
    op.drop_column('nodes', 'cert_created_at')
    op.drop_column('nodes', 'private_key')
    op.drop_column('nodes', 'certificate')