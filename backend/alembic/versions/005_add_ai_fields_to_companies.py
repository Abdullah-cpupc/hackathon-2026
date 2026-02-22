"""Add AI fields to companies table

Revision ID: 005
Revises: 004
Create Date: 2024-01-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade():
    # Add AI-related columns to companies table (nullable first)
    op.add_column('companies', sa.Column('ai_enabled', sa.Boolean(), nullable=True))
    op.add_column('companies', sa.Column('ai_collection_name', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('last_scraped_at', sa.DateTime(), nullable=True))
    op.add_column('companies', sa.Column('ai_build_status', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('ai_error_message', sa.Text(), nullable=True))
    
    # Update existing records with default values
    op.execute("UPDATE companies SET ai_enabled = false WHERE ai_enabled IS NULL")
    op.execute("UPDATE companies SET ai_build_status = 'not_started' WHERE ai_build_status IS NULL")
    
    # Now make ai_enabled NOT NULL
    op.alter_column('companies', 'ai_enabled', nullable=False)

def downgrade():
    # Remove AI-related columns from companies table
    op.drop_column('companies', 'ai_error_message')
    op.drop_column('companies', 'ai_build_status')
    op.drop_column('companies', 'last_scraped_at')
    op.drop_column('companies', 'ai_collection_name')
    op.drop_column('companies', 'ai_enabled')
