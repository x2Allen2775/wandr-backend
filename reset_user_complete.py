import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:y1MT6fyNOqEl9ArM@db.fqizfuewpkxxasazvzno.supabase.co:5432/postgres"
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    user_id_res = conn.execute(text("SELECT id FROM users WHERE email = 'maheshsingh2775@gmail.com'")).scalar()
    if user_id_res:
        conn.execute(text("DELETE FROM emergency_contacts WHERE user_id = :uid"), {"uid": user_id_res})
        print(f"Deleted emergency contacts for {user_id_res}")
        
    result = conn.execute(text("""
        UPDATE users 
        SET kyc_status = 'unverified',
            kyc_reference_token = NULL,
            legal_name = NULL,
            dob = NULL,
            social_google_email = NULL
        WHERE email = 'maheshsingh2775@gmail.com'
    """))
    print(f"Rows updated in users: {result.rowcount}")
