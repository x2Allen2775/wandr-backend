import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Add state column
    cursor.execute("""
        ALTER TABLE trips
        ADD COLUMN IF NOT EXISTS state VARCHAR;
    """)

    conn.commit()
    print("Database altered successfully. 'state' column added.")

except Exception as e:
    print(f"Error altering database: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()
