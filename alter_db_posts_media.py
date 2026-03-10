import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Drop existing media_url (since we are creating new posts anyway)
    # Re-add as media_urls Text (for JSON string array)
    cursor.execute("""
        ALTER TABLE posts
        DROP COLUMN IF EXISTS media_url;
    """)

    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN media_urls TEXT;
    """)

    conn.commit()
    print("Database altered successfully. 'media_url' converted to 'media_urls' json array.")

except Exception as e:
    print(f"Error altering database: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()
