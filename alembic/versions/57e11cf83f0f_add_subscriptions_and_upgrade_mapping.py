"""add_subscriptions_and_upgrade_mapping

Revision ID: 57e11cf83f0f
Revises: 98043b6f03d0
Create Date: 2026-02-26 07:13:47.840355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57e11cf83f0f'
down_revision: Union[str, Sequence[str], None] = '98043b6f03d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create Subscriptions
    op.create_table('subscriptions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_institution_id'), 'subscriptions', ['institution_id'], unique=False)

    # 2. Cleanup Mapping constraints before type change
    op.execute('ALTER TABLE class_instructor_maps DROP CONSTRAINT IF EXISTS class_instructor_maps_class_id_fkey')
    op.execute('ALTER TABLE class_instructor_maps DROP CONSTRAINT IF EXISTS class_instructor_maps_instructor_id_fkey')
    op.execute('ALTER TABLE class_instructor_maps DROP CONSTRAINT IF EXISTS class_instructor_maps_institution_id_fkey')
    op.execute('ALTER TABLE class_instructor_maps DROP CONSTRAINT IF EXISTS unique_instructor_per_class')
    op.execute('ALTER TABLE class_instructor_maps ALTER COLUMN id DROP DEFAULT')

    # 3. Upgrade mapping table
    op.add_column('class_instructor_maps', sa.Column('academic_year_id', sa.Integer(), nullable=False))
    op.add_column('class_instructor_maps', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('class_instructor_maps', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    op.alter_column('class_instructor_maps', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using="gen_random_uuid()",
               existing_nullable=False)
    
    op.create_index(op.f('ix_class_instructor_maps_academic_year_id'), 'class_instructor_maps', ['academic_year_id'], unique=False)
    op.create_index('ix_mappings_institution_academic_year', 'class_instructor_maps', ['institution_id', 'academic_year_id'], unique=False)
    op.create_unique_constraint('unique_instructor_mapping_per_year', 'class_instructor_maps', ['instructor_id', 'class_id', 'academic_year_id'])
    
    # 4. Re-add constraints
    op.create_foreign_key(None, 'class_instructor_maps', 'academic_years', ['academic_year_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'class_instructor_maps', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'class_instructor_maps', 'classes', ['class_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'class_instructor_maps', 'users', ['instructor_id'], ['id'], ondelete='RESTRICT')

    # 5. Seed initial subscriptions for existing institutions to avoid blocking
    op.execute("INSERT INTO subscriptions (id, institution_id, is_active, end_date, created_at) SELECT gen_random_uuid(), id, true, '2027-01-01', now() FROM institutions")


def downgrade() -> None:
    """Downgrade schema."""
    pass
