"""Add ai_build_progress to companies table

Revision ID: 007
Revises: 006
Create Date: 2024-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade():
    # Add ai_build_progress column to companies table
    op.add_column('companies', sa.Column('ai_build_progress', sa.Text(), nullable=True))

def downgrade():
    # Remove ai_build_progress column
    op.drop_column('companies', 'ai_build_progress')

