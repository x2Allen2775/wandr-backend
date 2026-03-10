"""Create trip social tables: trip_join_requests, trip_members, group_messages.
Also add open_to_join to trips, phone_number + phone_verified to users.
"""
from sqlalchemy import text
from app.database import engine, Base
from app.models.trip_member import TripJoinRequest, TripMember, GroupMessage

if __name__ == "__main__":
    # Create new tables
    TripJoinRequest.__table__.create(engine, checkfirst=True)
    TripMember.__table__.create(engine, checkfirst=True)
    GroupMessage.__table__.create(engine, checkfirst=True)
    print("✅ trip_join_requests, trip_members, group_messages tables created!")

    # Add columns to existing tables
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE trips ADD COLUMN open_to_join BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✅ Added open_to_join to trips")
        except Exception as e:
            print(f"⚠️  open_to_join may already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR"))
            conn.commit()
            print("✅ Added phone_number to users")
        except Exception as e:
            print(f"⚠️  phone_number may already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✅ Added phone_verified to users")
        except Exception as e:
            print(f"⚠️  phone_verified may already exist: {e}")

    print("✅ All migrations complete!")
