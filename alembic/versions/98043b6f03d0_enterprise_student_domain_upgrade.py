"""enterprise_student_domain_upgrade

Revision ID: 98043b6f03d0
Revises: 27b2d48294a8
Create Date: 2026-02-26 07:00:06.237932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98043b6f03d0'
down_revision: Union[str, Sequence[str], None] = '27b2d48294a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop dependent constraints first
    op.execute('ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_student_id_fkey')
    op.execute('ALTER TABLE survey_responses DROP CONSTRAINT IF EXISTS survey_responses_student_id_fkey')
    op.execute('ALTER TABLE students DROP CONSTRAINT IF EXISTS students_institution_id_fkey')
    op.execute('ALTER TABLE students DROP CONSTRAINT IF EXISTS students_class_id_fkey')
    op.execute('ALTER TABLE students DROP CONSTRAINT IF EXISTS students_academic_year_id_fkey')

    # 2. Drop sequence defaults before type change
    op.execute('ALTER TABLE students ALTER COLUMN id DROP DEFAULT')

    # 3. Alter column types with explicit casting
    op.execute('ALTER TABLE students ALTER COLUMN id TYPE UUID USING gen_random_uuid()')
    op.execute('ALTER TABLE attendance ALTER COLUMN student_id TYPE UUID USING NULL::uuid')
    op.execute('ALTER TABLE survey_responses ALTER COLUMN student_id TYPE UUID USING NULL::uuid')

    # 4. Add new columns
    op.add_column('students', sa.Column('student_unique_id', sa.String(), nullable=False))
    op.add_column('students', sa.Column('age', sa.Integer(), nullable=False))
    op.add_column('students', sa.Column('gender', sa.String(), nullable=False))
    op.add_column('students', sa.Column('enrollment_date', sa.Date(), nullable=False))
    op.add_column('students', sa.Column('health_notes', sa.Text(), nullable=True))
    op.add_column('students', sa.Column('academic_year_id', sa.Integer(), nullable=False))
    
    op.alter_column('students', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # 5. Indexes and Unique Constraints
    # Use execute for index drops to handle legacy names
    op.execute('DROP INDEX IF EXISTS ix_student_institution_id')
    op.execute('DROP INDEX IF EXISTS ix_students_id')
    op.execute('DROP INDEX IF EXISTS ix_students_institution')
    
    op.create_index(op.f('ix_students_academic_year_id'), 'students', ['academic_year_id'], unique=False)
    op.create_index('ix_students_institution_academic_year', 'students', ['institution_id', 'academic_year_id'], unique=False)
    op.create_index(op.f('ix_students_institution_id'), 'students', ['institution_id'], unique=False)
    op.create_unique_constraint('unique_student_id_per_institution', 'students', ['institution_id', 'student_unique_id'])

    # 6. Re-create foreign keys with RESTRICT
    op.create_foreign_key(None, 'attendance', 'students', ['student_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'survey_responses', 'students', ['student_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'students', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'students', 'classes', ['class_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'students', 'academic_years', ['academic_year_id'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    """Downgrade schema."""
    pass
