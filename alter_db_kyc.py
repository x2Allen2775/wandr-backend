"""Add kyc_document_url and kyc_verified_at columns to users table."""
from sqlalchemy import text
from app.database import engine

if __name__ == "__main__":
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN kyc_document_url VARCHAR"))
            conn.commit()
            print("✅ Added kyc_document_url to users")
        except Exception as e:
            print(f"⚠️  kyc_document_url may already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN kyc_verified_at TIMESTAMP WITH TIME ZONE"))
            conn.commit()
            print("✅ Added kyc_verified_at to users")
        except Exception as e:
            print(f"⚠️  kyc_verified_at may already exist: {e}")

    print("✅ KYC migration complete!")
