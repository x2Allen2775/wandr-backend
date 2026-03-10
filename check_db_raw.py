import os
import sys

sys.path.append("/Users/allen2775/Downloads/wandr")

from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def check_users():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT email, phone_verified, kyc_status, legal_name FROM users"))
        rows = result.fetchall()
        print(f"Total Users in DB: {len(rows)}\n" + "-"*50)
        for r in rows:
            print(f"Email: {r[0]} | Phone_Verified: {r[1]} | KYC_Status: {r[2]} | Legal_Name: {r[3]}")

if __name__ == "__main__":
    check_users()
