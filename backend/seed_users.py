from app.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_users():
    db = SessionLocal()
    try:
        users = [
            {
                "email": "admin@cybercafe.com",
                "username": "admin",
                "full_name": "System Admin",
                "password": "admin123",
                "role": UserRole.ADMIN
            },
            {
                "email": "manager@cybercafe.com",
                "username": "manager",
                "full_name": "Store Manager",
                "password": "manager123",
                "role": UserRole.MANAGER
            },
            {
                "email": "attendant@cybercafe.com",
                "username": "attendant",
                "full_name": "Front Desk",
                "password": "attendant123",
                "role": UserRole.ATTENDANT
            }
        ]
        
        for user_data in users:
            user = db.query(User).filter(User.email == user_data["email"]).first()
            if not user:
                logger.info(f"Creating user: {user_data['email']}")
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    full_name=user_data["full_name"],
                    password_hash=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True
                )
                db.add(user)
            else:
                logger.info(f"User already exists: {user_data['email']}")
                # Ensure correct role/password for dev
                user.role = user_data["role"]
                user.password_hash = get_password_hash(user_data["password"])
                user.username = user_data["username"]
                
        db.commit()
        logger.info("Users seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
