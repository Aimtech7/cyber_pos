from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.config import settings
import sys

# Setup DB connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def seed_admin():
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if user:
            print("Admin user already exists.")
            return

        # Create user
        new_user = User(
            id=1,
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        print("Successfully created Admin user (ID: 1).")
    except Exception as e:
        print(f"Error seeding user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
