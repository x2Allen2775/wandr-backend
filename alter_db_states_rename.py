import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Rename `state` column to `states` and change to Text (for JSON logic)
    cursor.execute("""
        ALTER TABLE trips
        RENAME COLUMN state TO states;
    """)

    conn.commit()
    print("Database altered successfully. 'state' column renamed to 'states'.")

except Exception as e:
    print(f"Error altering database: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()
