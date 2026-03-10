from app.database import engine
from sqlalchemy import text

def run_migration():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN social_google_email VARCHAR;"))
            print("Successfully added social_google_email to users table")
        except Exception as e:
            if "already exists" in str(e):
                print("Column already exists")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    run_migration()
