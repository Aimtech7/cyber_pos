"""
Bootstrap Admin User Script
Creates or updates admin user with environment-provided credentials.
Only runs when BOOTSTRAP_ADMIN=true for security.
"""
import os
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def bootstrap_admin():
    """Create or update admin user from environment variables"""
    
    # Security check
    if os.getenv("BOOTSTRAP_ADMIN", "false").lower() != "true":
        print("❌ BOOTSTRAP_ADMIN is not set to 'true'. Exiting for security.")
        print("   Set BOOTSTRAP_ADMIN=true to run this script.")
        sys.exit(1)
    
    # Get credentials from environment
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    
    if not admin_email or not admin_password:
        print("❌ ADMIN_EMAIL and ADMIN_PASSWORD must be set")
        sys.exit(1)
    
    # Validate password strength
    if len(admin_password) < 8:
        print("❌ ADMIN_PASSWORD must be at least 8 characters")
        sys.exit(1)
    
    db: Session = SessionLocal()
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == admin_email).first()
        
        if user:
            # Update existing user
            print(f"📝 Updating existing user: {admin_email}")
            user.password_hash = get_password_hash(admin_password)
            user.username = admin_username
            user.role = UserRole.ADMIN
            user.is_active = True
            action = "updated"
        else:
            # Create new user
            print(f"✨ Creating new admin user: {admin_email}")
            user = User(
                email=admin_email,
                username=admin_username,
                password_hash=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(user)
            action = "created"
        
        db.commit()
        db.refresh(user)
        
        print(f"✅ Admin user {action} successfully!")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role.value}")
        print(f"   Active: {user.is_active}")
        print(f"\n🔐 You can now login with:")
        print(f"   Username: {user.username}")
        print(f"   Password: [as provided in ADMIN_PASSWORD]")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    bootstrap_admin()
