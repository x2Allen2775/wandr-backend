import asyncio
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Database URL not found.")
    exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Marking user's first trip as completed to allow testing Peer Reviews...")
    result = conn.execute(text("UPDATE trips SET status = 'completed' WHERE id IN (SELECT id FROM trips LIMIT 2)"))
    conn.commit()
    print("Done! Updated trips.")
