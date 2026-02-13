import os
import sys
import subprocess
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run Alembic migrations"""
    print("Starting database migrations...")
    
    try:
        # Check if alembic.ini exists
        if not os.path.exists("alembic.ini"):
            print("Error: alembic.ini not found")
            sys.exit(1)
            
        # Run alembic upgrade head
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        print("Migrations applied successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
