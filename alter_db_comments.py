"""
Migration: Create the 'comments' table.
"""
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg2://", "postgresql://")

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id VARCHAR PRIMARY KEY,
    post_id VARCHAR NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS ix_comments_user_id ON comments(user_id);
""")
conn.commit()
print("✅ comments table created successfully!")
cur.close()
conn.close()
