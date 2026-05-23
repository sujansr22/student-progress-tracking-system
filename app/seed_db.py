from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import Institution, User, Student, UserRole
from app.core.auth import get_password_hash


def seed_data():
    db: Session = SessionLocal()

    # 1. Create SUPER_ADMIN
    super_admin = User(
        email="owner@spts.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Platform Owner",
        role=UserRole.SUPER_ADMIN,
        institution_id=None
    )
    db.add(super_admin)
    db.commit()

    # 2. Create Institutions
    inst_a = Institution(name="Greenwood High")
    inst_b = Institution(name="Riverdale Academy")

    db.add_all([inst_a, inst_b])
    db.commit()
    db.refresh(inst_a)
    db.refresh(inst_b)

    # 3. Create SCHOOL_ADMINs
    admin_a = User(
        email="admin@greenwood.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Greenwood Admin",
        role=UserRole.SCHOOL_ADMIN,
        institution_id=inst_a.id
    )
    admin_b = User(
        email="admin@riverdale.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Riverdale Admin",
        role=UserRole.SCHOOL_ADMIN,
        institution_id=inst_b.id
    )

    db.add_all([admin_a, admin_b])
    db.commit()

    # 4. Create INSTRUCTORs
    instr_a = User(
        email="teacher1@greenwood.com",
        hashed_password=get_password_hash("teacher123"),
        full_name="Alice Smith",
        role=UserRole.INSTRUCTOR,
        institution_id=inst_a.id
    )
    instr_b = User(
        email="teacher2@riverdale.com",
        hashed_password=get_password_hash("teacher123"),
        full_name="Bob Jones",
        role=UserRole.INSTRUCTOR,
        institution_id=inst_b.id
    )

    db.add_all([instr_a, instr_b])
    db.commit()

    # 5. Create Students
    stud_a1 = Student(
        first_name="John",
        last_name="Doe",
        email="john@greenwood.com",
        institution_id=inst_a.id
    )
    stud_a2 = Student(
        first_name="Jane",
        last_name="Doe",
        email="jane@greenwood.com",
        institution_id=inst_a.id
    )
    stud_b1 = Student(
        first_name="Charlie",
        last_name="Brown",
        email="charlie@riverdale.com",
        institution_id=inst_b.id
    )

    db.add_all([stud_a1, stud_a2, stud_b1])
    db.commit()

    print("Seed data created successfully.")
    print("Logins:")
    print("- Super Admin: owner@spts.com / admin123")
    print("- School Admin: admin@greenwood.com / admin123")
    print("- Instructor: teacher1@greenwood.com / teacher123")
    db.close()


if __name__ == "__main__":
    seed_data()
