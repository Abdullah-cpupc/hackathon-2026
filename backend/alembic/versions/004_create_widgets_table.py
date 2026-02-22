"""Create widgets table

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Create widgets table
    op.create_table('widgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('widget_id', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('minimized_shape', sa.String(), nullable=False),
        sa.Column('minimized_bg_color', sa.String(), nullable=False),
        sa.Column('maximized_style', sa.String(), nullable=False),
        sa.Column('system_bubble_bg_color', sa.String(), nullable=False),
        sa.Column('user_bubble_bg_color', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )
    
    # Create index on widget_id for fast lookups
    op.create_index('idx_widgets_widget_id', 'widgets', ['widget_id'])
    
    # Create index on company_id for efficient queries
    op.create_index('idx_widgets_company_id', 'widgets', ['company_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_widgets_company_id', table_name='widgets')
    op.drop_index('idx_widgets_widget_id', table_name='widgets')
    
    # Drop widgets table
    op.drop_table('widgets')
