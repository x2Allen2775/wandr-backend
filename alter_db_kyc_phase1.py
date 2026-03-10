import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

print(f"Connecting to database...")

try:
    if DB_URL and DB_URL.startswith("postgresql"):
        conn = psycopg2.connect(DB_URL)
    else:
        conn = sqlite3.connect('wandr.db')
    
    cursor = conn.cursor()
    
    # 1. Add fields to users table
    # kyc_status, kyc_reference_token, legal_name, dob
    alter_commands = [
        "ALTER TABLE users ADD COLUMN kyc_status VARCHAR DEFAULT 'unverified';",
        "ALTER TABLE users ADD COLUMN kyc_reference_token VARCHAR;",
        "ALTER TABLE users ADD COLUMN legal_name VARCHAR;",
        "ALTER TABLE users ADD COLUMN dob TIMESTAMP;"
    ]
    
    for cmd in alter_commands:
        try:
            cursor.execute(cmd)
            print(f"Executed: {cmd}")
        except Exception as e:
            print(f"Skipped (might exist): {cmd} - {e}")
            conn.rollback() if DB_URL and DB_URL.startswith("postgresql") else None

    # 2. Create the user_consents table
    create_table_cmd = """
    CREATE TABLE IF NOT EXISTS user_consents (
        id UUID PRIMARY KEY,
        user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE NOT NULL,
        consent_type VARCHAR NOT NULL,
        ip_address VARCHAR,
        granted BOOLEAN NOT NULL DEFAULT TRUE,
        timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
        revoked_at TIMESTAMP
    );
    """
    if not DB_URL or not DB_URL.startswith("postgresql"):
        # SQLite dialect
        create_table_cmd = """
        CREATE TABLE IF NOT EXISTS user_consents (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE NOT NULL,
            consent_type VARCHAR NOT NULL,
            ip_address VARCHAR,
            granted BOOLEAN NOT NULL DEFAULT 1,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            revoked_at DATETIME
        );
        """
        
    try:
        cursor.execute(create_table_cmd)
        print("Created user_consents table.")
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback() if DB_URL and DB_URL.startswith("postgresql") else None

    conn.commit()
    conn.close()
    print("Migration successful.")
except Exception as e:
    print(f"Failed to connect or migrate: {e}")

