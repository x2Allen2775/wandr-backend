from app.database import engine
from sqlalchemy import text

def upgrade_db():
    print("Connecting to Supabase to inject new columns...")
    with engine.begin() as conn:
        # Add new columns to the trips table
        columns = [
            "ALTER TABLE trips ADD COLUMN country VARCHAR;",
            "ALTER TABLE trips ADD COLUMN cities TEXT;",
            "ALTER TABLE trips ADD COLUMN travel_interests TEXT;"
        ]
        
        for col_query in columns:
            try:
                conn.execute(text(col_query))
                print(f"SUCCESS: {col_query}")
            except Exception as e:
                print(f"SKIPPED (likely already exists): {col_query} -> {e}")

if __name__ == "__main__":
    upgrade_db()
