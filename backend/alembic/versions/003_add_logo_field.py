"""Add logo field to companies table

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Add logo column to companies table
    op.add_column('companies', sa.Column('logo_url', sa.String(), nullable=True))

def downgrade():
    # Remove logo column from companies table
    op.drop_column('companies', 'logo_url')
