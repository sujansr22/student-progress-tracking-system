"""remove_cascades_enforce_restrict

Revision ID: f0a1b2c3d4e5
Revises: 57e11cf83f0f
Create Date: 2026-02-27 12:23:33.665646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = '57e11cf83f0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. academic_years.institution_id: CASCADE -> RESTRICT
    op.drop_constraint('academic_years_institution_id_fkey', 'academic_years', type_='foreignkey')
    op.create_foreign_key('academic_years_institution_id_fkey', 'academic_years', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')
    
    # 2. classes.institution_id: CASCADE -> RESTRICT
    op.drop_constraint('classes_institution_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key('classes_institution_id_fkey', 'classes', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')
    
    # 3. classes.academic_year_id: CASCADE -> RESTRICT
    op.drop_constraint('classes_academic_year_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key('classes_academic_year_id_fkey', 'classes', 'academic_years', ['academic_year_id'], ['id'], ondelete='RESTRICT')

    # 4. attendance.institution_id: CASCADE -> RESTRICT
    op.drop_constraint('attendance_institution_id_fkey', 'attendance', type_='foreignkey')
    op.create_foreign_key('attendance_institution_id_fkey', 'attendance', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')

    # 5. survey_responses.institution_id: CASCADE -> RESTRICT
    op.drop_constraint('survey_responses_institution_id_fkey', 'survey_responses', type_='foreignkey')
    op.create_foreign_key('survey_responses_institution_id_fkey', 'survey_responses', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')

    # 6. survey_answers.survey_response_id: CASCADE -> RESTRICT
    op.drop_constraint('survey_answers_survey_response_id_fkey', 'survey_answers', type_='foreignkey')
    op.create_foreign_key('survey_answers_survey_response_id_fkey', 'survey_answers', 'survey_responses', ['survey_response_id'], ['id'], ondelete='RESTRICT')

    # 7. users.institution_id: CASCADE -> RESTRICT
    op.drop_constraint('users_institution_id_fkey', 'users', type_='foreignkey')
    op.create_foreign_key('users_institution_id_fkey', 'users', 'institutions', ['institution_id'], ['id'], ondelete='RESTRICT')

    # 8. Add soft-delete support to academic_years
    op.add_column('academic_years', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('academic_years', 'deleted_at')

    # Users
    op.drop_constraint('users_institution_id_fkey', 'users', type_='foreignkey')
    op.create_foreign_key('users_institution_id_fkey', 'users', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')

    # Survey Answers
    op.drop_constraint('survey_answers_survey_response_id_fkey', 'survey_answers', type_='foreignkey')
    op.create_foreign_key('survey_answers_survey_response_id_fkey', 'survey_answers', 'survey_responses', ['survey_response_id'], ['id'], ondelete='CASCADE')

    # Survey Responses
    op.drop_constraint('survey_responses_institution_id_fkey', 'survey_responses', type_='foreignkey')
    op.create_foreign_key('survey_responses_institution_id_fkey', 'survey_responses', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')

    # Attendance
    op.drop_constraint('attendance_institution_id_fkey', 'attendance', type_='foreignkey')
    op.create_foreign_key('attendance_institution_id_fkey', 'attendance', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')

    # Classes
    op.drop_constraint('classes_academic_year_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key('classes_academic_year_id_fkey', 'classes', 'academic_years', ['academic_year_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('classes_institution_id_fkey', 'classes', type_='foreignkey')
    op.create_foreign_key('classes_institution_id_fkey', 'classes', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')

    # Academic Years
    op.drop_constraint('academic_years_institution_id_fkey', 'academic_years', type_='foreignkey')
    op.create_foreign_key('academic_years_institution_id_fkey', 'academic_years', 'institutions', ['institution_id'], ['id'], ondelete='CASCADE')
