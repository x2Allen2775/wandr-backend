import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:y1MT6fyNOqEl9ArM@db.fqizfuewpkxxasazvzno.supabase.co:5432/postgres"

def main():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        print("Creating emergency_contacts table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                relation VARCHAR NOT NULL,
                phone_number VARCHAR NOT NULL,
                is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        print("Table created successfully!")

if __name__ == "__main__":
    main()
