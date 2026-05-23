"""student_portal

Revision ID: p4s1t2u3v4w5
Revises: p3f1a2b3c4d5
Create Date: 2026-05-23

Adds:
  - STUDENT value to userrole enum
  - LATE value to attendancestatus enum
  - students.user_id FK column
  - assigned_surveys table
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p4s1t2u3v4w5"
down_revision: Union[str, None] = "p3f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values (PostgreSQL 12+ supports this in a transaction)
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'STUDENT'")
    op.execute("ALTER TYPE attendancestatus ADD VALUE IF NOT EXISTS 'LATE'")

    # Link students to user accounts
    op.add_column("students", sa.Column("user_id", sa.Integer(),
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_students_user_id", "students", ["user_id"], unique=True)

    op.execute("""
        CREATE TYPE assignedsurveystatus AS ENUM ('PENDING', 'COMPLETED');

        CREATE TABLE assigned_surveys (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id  UUID        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            assigned_by INTEGER     REFERENCES users(id) ON DELETE SET NULL,
            institution_id INTEGER  NOT NULL REFERENCES institutions(id) ON DELETE RESTRICT,
            month       INTEGER     NOT NULL,
            year        INTEGER     NOT NULL,
            due_date    DATE,
            status      assignedsurveystatus NOT NULL DEFAULT 'PENDING',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT unique_assignment_per_period UNIQUE (student_id, month, year)
        );

        CREATE INDEX ix_assigned_surveys_student_id     ON assigned_surveys(student_id);
        CREATE INDEX ix_assigned_surveys_institution_id ON assigned_surveys(institution_id);
    """)


def downgrade() -> None:
    op.drop_table("assigned_surveys")
    op.execute("DROP TYPE IF EXISTS assignedsurveystatus")
    op.drop_index("ix_students_user_id", table_name="students")
    op.drop_column("students", "user_id")
    # Note: PostgreSQL does not support removing enum values; skip enum downgrade
