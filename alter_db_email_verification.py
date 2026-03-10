"""
Migration: Create email_verifications table for OTP codes.
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# Convert from sqlalchemy format to psycopg2 format
conn_str = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")

conn = psycopg2.connect(conn_str)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS email_verifications (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE NOT NULL,
        code VARCHAR(6) NOT NULL,
        purpose VARCHAR NOT NULL DEFAULT 'signup',
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
""")

print("✅ email_verifications table created successfully!")

cur.close()
conn.close()
