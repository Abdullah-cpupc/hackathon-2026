"""Add api_key and allowed_domains to widgets table

Revision ID: 006
Revises: 005
Create Date: 2024-01-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade():
    # Add api_key column to widgets table
    op.add_column('widgets', sa.Column('api_key', sa.String(), nullable=True))
    
    # Add allowed_domains column to widgets table
    op.add_column('widgets', sa.Column('allowed_domains', sa.Text(), nullable=True))
    
    # Create unique index on api_key for fast lookups
    op.create_index('idx_widgets_api_key', 'widgets', ['api_key'], unique=True)

def downgrade():
    # Drop index
    op.drop_index('idx_widgets_api_key', table_name='widgets')
    
    # Remove columns
    op.drop_column('widgets', 'allowed_domains')
    op.drop_column('widgets', 'api_key')

