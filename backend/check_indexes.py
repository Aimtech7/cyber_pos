from app.database import engine
from sqlalchemy import text
import logging

def check_indexes():
    # This query works for PostgreSQL. For SQLite, it needs "PRAGMA index_list(table_name)"
    # Let's try to detect dialect or just run generic simple queries.
    # The user environment is likely SQLite based on previous context or Postgres if configured.
    # If SQLite, `sqlite_master` can be queried.
    
    with engine.connect() as conn:
        dialect = engine.dialect.name
        print(f"Database Dialect: {dialect}")
        
        tables = ["transactions", "transaction_items", "inventory_items", "stock_movements", "sessions"]
        
        for table in tables:
            print(f"\nIndexes for {table}:")
            if dialect == 'sqlite':
                result = conn.execute(text(f"PRAGMA index_list('{table}')"))
                for row in result:
                    print(f"- {row[1]}")
            elif dialect == 'postgresql':
                result = conn.execute(text(f"SELECT indexname FROM pg_indexes WHERE tablename = '{table}'"))
                for row in result:
                    print(f"- {row[0]}")

if __name__ == "__main__":
    check_indexes()
