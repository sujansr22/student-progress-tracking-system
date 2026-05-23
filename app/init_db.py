from app.core.database import engine, Base
from app.models.models import Institution, User, Student

def init_db():
    print("Database initialization check complete.")

if __name__ == "__main__":
    init_db()
