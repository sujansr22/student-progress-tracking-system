"""cleanup_academic_year_index_and_fk

Revision ID: a1b2c3d4e5f6
Revises: f0a1b2c3d4e5
Create Date: 2026-02-27 12:28:45.701265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop redundant index
    op.drop_index('ix_academic_years_id', table_name='academic_years')
    
    # 2. Refine classes.academic_year_id FK (Ensure name and RESTRICT)
    # Using 'classes_academic_year_id_fkey' as the explicit name requested
    op.drop_constraint('classes_academic_year_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key(
        'classes_academic_year_id_fkey', 
        'classes', 
        'academic_years', 
        ['academic_year_id'], 
        ['id'], 
        ondelete='RESTRICT'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate FK with CASCADE
    op.drop_constraint('classes_academic_year_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key(
        'classes_academic_year_id_fkey', 
        'classes', 
        'academic_years', 
        ['academic_year_id'], 
        ['id'], 
        ondelete='CASCADE'
    )
    
    # Recreate redundant index
    op.create_index('ix_academic_years_id', 'academic_years', ['id'], unique=False)
