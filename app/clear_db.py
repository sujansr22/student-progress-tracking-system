from sqlalchemy import text
from app.core.database import SessionLocal, engine, Base

def clear_db():
    print("Clearing database...")
    with engine.connect() as conn:
        # Use CASCADE to drop tables with dependencies
        conn.execute(text("DROP TABLE IF EXISTS survey_answers CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS survey_responses CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS attendance CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS students CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS instructors CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS institutions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        
        # Drop ENUM types
        conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS attendancestatus CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS surveytype CASCADE"))
        
        conn.commit()
    print("Database cleared.")

if __name__ == "__main__":
    clear_db()
