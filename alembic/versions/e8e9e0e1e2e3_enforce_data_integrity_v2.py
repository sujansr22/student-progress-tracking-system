"""enforce_data_integrity_v2

Revision ID: e8e9e0e1e2e3
Revises: a1b2c3d4e5f6
Create Date: 2026-02-27 12:33:42.106462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e8e9e0e1e2e3'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - remove cascades and redundant index."""
    # 1. Drop redundant index on academic_years(id) - defensive drop
    op.execute(text("DROP INDEX IF EXISTS ix_academic_years_id"))

    # 2. academic_years.institution_id: CASCADE -> RESTRICT
    op.drop_constraint('academic_years_institution_id_fkey', 'academic_years', type_='foreignkey')
    op.create_foreign_key(
        'academic_years_institution_id_fkey', 
        'academic_years', 
        'institutions', 
        ['institution_id'], 
        ['id'], 
        ondelete='RESTRICT'
    )
    
    # 3. classes.academic_year_id: CASCADE -> RESTRICT
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
    """Downgrade schema - restore cascades and redundant index."""
    # Restore classes.academic_year_id: RESTRICT -> CASCADE
    op.drop_constraint('classes_academic_year_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key(
        'classes_academic_year_id_fkey', 
        'classes', 
        'academic_years', 
        ['academic_year_id'], 
        ['id'], 
        ondelete='CASCADE'
    )

    # Restore academic_years.institution_id: RESTRICT -> CASCADE
    op.drop_constraint('academic_years_institution_id_fkey', 'academic_years', type_='foreignkey')
    op.create_foreign_key(
        'academic_years_institution_id_fkey', 
        'academic_years', 
        'institutions', 
        ['institution_id'], 
        ['id'], 
        ondelete='CASCADE'
    )

    # Recreate redundant index
    op.create_index('ix_academic_years_id', 'academic_years', ['id'], unique=False)
