from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def update_passwords():
    db = SessionLocal()
    try:
        users = {
            "admin": "admin123",
            "manager": "manager123",
            "attendant": "attendant123"
        }
        
        for username, password in users.items():
            user = db.query(User).filter(User.username == username).first()
            if user:
                print(f"Updating password for {username}...")
                user.password_hash = get_password_hash(password)
                db.add(user)
            else:
                print(f"User {username} not found!")
        
        db.commit()
        print("Passwords updated successfully.")
    except Exception as e:
        print(f"Error updating passwords: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_passwords()
