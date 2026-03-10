import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def alter_db():
    with engine.begin() as conn:
        print("Adding trust_score and review_count to users table...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN trust_score FLOAT DEFAULT 5.0;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN review_count INTEGER DEFAULT 0;"))
        except Exception as e:
            print(f"Columns might already exist: {e}")

        print("Creating reviews table...")
        try:
            conn.execute(text("""
                CREATE TABLE reviews (
                    id VARCHAR PRIMARY KEY,
                    trip_id VARCHAR NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
                    reviewer_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    reviewee_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rating FLOAT NOT NULL,
                    text_review TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
        except Exception as e:
            print(f"Table might already exist: {e}")

    print("Database altered successfully.")

if __name__ == "__main__":
    alter_db()
