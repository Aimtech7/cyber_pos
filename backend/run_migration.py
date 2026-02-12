from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    logger.info("Running migration: migration_hardening.sql")
    try:
        # Use filename directly as we expect to run from backend/ dir
        with open("migration_hardening.sql", "r") as f:
            sql_script = f.read()
            
        with engine.connect() as connection:
            # For Supabase Pooler (Transaction Mode), explicit begin() can sometimes cause issues/hangs
            # if not handled perfectly, or if driver/pooler mismatch.
            # Let's try executing directly. SQLAlchemy 2.0+ usually auto-begins.
            # But let's try just executing.
            
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            for statement in statements:
                logger.info(f"Executing: {statement[:50]}...")
                try:
                    connection.execute(text(statement))
                    connection.commit() # Commit after each or at end
                except Exception as e:
                     logger.warning(f"Statement failed (might already exist): {e}")
            
            logger.info("Migration completed.")
            
    except Exception as e:
        logger.error(f"Error checking migration: {e}")

if __name__ == "__main__":
    run_migration()
