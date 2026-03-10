import sys
import os

sys.path.append("/Users/allen2775/Downloads/wandr")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Total Users in DB: {len(users)}\n" + "-"*50)
        for u in users:
            print(f"Email: {u.email} | Phone_Verified: {u.phone_verified} | KYC_Status: {u.kyc_status} | Legal_Name: {u.legal_name}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
