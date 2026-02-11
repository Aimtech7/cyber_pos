import sys
import os
from sqlalchemy import text
from app.models.user import User

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("1. Testing imports...")
try:
    from app.database import SessionLocal
    from app.core.security import get_password_hash, verify_password
    print("   Imports successful.")
    from app.config import settings
    print(f"   Configured URL: {settings.DATABASE_URL.replace(':', '***').replace('@', ' at ')}")
except Exception as e:
    print(f"   Import failed: {e}")
    sys.exit(1)

print("2. Testing password hashing...")
try:
    hash = get_password_hash("test")
    print(f"   Hashing successful: {hash[:10]}...")
    if verify_password("test", hash):
        print("   Verification successful.")
    else:
        print("   Verification failed.")
except Exception as e:
    print(f"   Hashing failed: {e}")
    # Don't exit, try DB
    
print("3. Testing database connection...")
try:
    # Use SessionLocal which loads from .env
    db = SessionLocal()
    
    # Use text() for SQL expression in SQLAlchemy 2.0
    db.execute(text("SELECT 1"))
    print("   Database connection successful!")
    
    # Check for users
    user_count = db.query(User).count()
    print(f"   Found {user_count} users in database.")
    
    if user_count > 0:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
             print("   Admin user exists.")
             if verify_password("admin123", admin.password_hash):
                 print("   Admin login verification successful!")
             else:
                 print("   Admin login verification FAILED (wrong password hash).")
        else:
             print("   Admin user NOT found.")
    else:
        print("   No users found. Seeding required.")
             
    db.close()
except Exception as e:
    print(f"   Database connection failed: {e}")
    print("\n   TROUBLESHOOTING:")
    print("   1. Check if your DATABASE_URL in backend/.env is correct.")
    print("   2. Ensure your IP is allowed in Supabase settings (or 0.0.0.0/0).")
    print("   3. If using pooler (port 5432/6543), ensure 'Mode' is set correctly.")
    print("   4. Verify username/password/project-ref.")
