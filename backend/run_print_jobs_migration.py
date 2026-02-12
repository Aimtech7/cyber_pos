from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_print_jobs_migration():
    logger.info("Running Print Jobs migration: migration_print_jobs.sql")
    try:
        with open("migration_print_jobs.sql", "r") as f:
            sql_script = f.read()
            
        with engine.connect() as connection:
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            for statement in statements:
                logger.info(f"Executing: {statement[:50]}...")
                try:
                    connection.execute(text(statement))
                    connection.commit()
                except Exception as e:
                     logger.warning(f"Statement failed (might already exist): {e}")
            
            logger.info("Print Jobs migration completed.")
            
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        raise

if __name__ == "__main__":
    run_print_jobs_migration()
