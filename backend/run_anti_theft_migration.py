"""
Migration runner for Anti-Theft Alerts System
"""
import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Execute the anti-theft alerts migration"""
    engine = create_engine(DATABASE_URL)
    
    # Read migration file
    migration_file = "migration_anti_theft_alerts.sql"
    logger.info(f"Running Anti-Theft Alerts migration: {migration_file}")
    
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    with engine.connect() as conn:
        for statement in statements:
            if statement:
                try:
                    logger.info(f"Executing: {statement[:50]}...")
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Statement failed (might already exist): {e}")
                    conn.rollback()
    
    logger.info("Anti-Theft Alerts migration completed.")

if __name__ == "__main__":
    run_migration()
