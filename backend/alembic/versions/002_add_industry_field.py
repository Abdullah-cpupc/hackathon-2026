"""Add industry field to companies table

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add industry column to companies table
    op.add_column('companies', sa.Column('industry', sa.String(), nullable=True))

def downgrade():
    # Remove industry column from companies table
    op.drop_column('companies', 'industry')
