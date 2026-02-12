"""
Migration runner for offline mode support
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the offline mode migration"""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Running offline mode migration...")
        
        # Read and execute migration SQL
        with open("migration_offline_mode.sql", "r") as f:
            sql = f.read()
            cursor.execute(sql)
        
        # Commit changes
        conn.commit()
        
        print("[SUCCESS] Migration completed successfully!")
        print("Added columns:")
        print("  - client_generated_id (UUID, unique)")
        print("  - offline_receipt_number (VARCHAR)")
        print("  - synced_at (TIMESTAMP)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
