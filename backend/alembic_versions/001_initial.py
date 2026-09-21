"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables."""
    # This is handled by init_db() in database.py
    # Alembic migrations can be added later for schema changes
    pass


def downgrade():
    """Drop all tables."""
    pass
