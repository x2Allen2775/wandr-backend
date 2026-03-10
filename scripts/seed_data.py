import asyncio
import os
import sys
from datetime import datetime, timedelta
import uuid

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.user import User, follows
from app.models.post import Post
from app.models.trip import Trip
import json

def seed_data():
    db = SessionLocal()
    try:
        # 1. Target User Account
        target_email = "maheshsingh2775@gmail.com"
        target_user = db.query(User).filter(User.email == target_email).first()
        
        if not target_user:
            print(f"User {target_email} not found. Creating...")
            target_user = User(
                email=target_email,
                username="mahesh_test",
                full_name="Mahesh Singh",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYm"
            )
            db.add(target_user)
            db.commit()
            db.refresh(target_user)

        # 2. Mock Users
        mock_users = []
        for i in range(1, 6):
            mock_user = db.query(User).filter(User.username == f"mock_user_{i}").first()
            if not mock_user:
                mock_user = User(
                    email=f"mock_{i}@example.com",
                    username=f"mock_user_{i}",
                    full_name=f"Mock User {i}",
                    hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYm"
                )
                db.add(mock_user)
                db.commit()
                db.refresh(mock_user)
            mock_users.append(mock_user)
        
        # 3. Follows
        print("Setting up Follows...")
        # Target follows mock_1 and mock_2
        for m_user in mock_users[:2]:
            if m_user not in target_user.following:
                target_user.following.append(m_user)
                
        # Mock_3, Mock_4, Mock_5 follow Target
        for m_user in mock_users[2:]:
            if target_user not in m_user.following:
                m_user.following.append(target_user)
        db.commit()

        # 4. Posts
        print("Scaffolding Posts...")
        # A mix of single and multi-media posts for mock users so the Feed is populated
        media_sets = [
            json.dumps(["https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=800&q=80"]),
            json.dumps([
                "https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=800&q=80",
                "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&q=80"
            ]),
            json.dumps(["https://images.unsplash.com/photo-1527631746610-bca00a040d60?w=800&q=80"]),
            json.dumps([
                "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800&q=80",
                "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80",
                "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=800&q=80"
            ]),
            json.dumps(["https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800&q=80"])
        ]
        
        for idx, m_user in enumerate(mock_users):
            p = Post(
                user_id=m_user.id,
                caption=f"Having a great time here! - {m_user.username}",
                media_urls=media_sets[idx],
                location=f"Location {idx + 1}",
                visibility="public"
            )
            db.add(p)
        db.commit()

        # 5. Trips (Including a past trip for the target user)
        # We need a trip well in the past to increment countries_travelled
        print("Setting up Trips...")
        past_trip_id = str(uuid.uuid4())
        
        # Check if they already have one to avoid dupes on re-run
        has_past_trip = db.query(Trip).filter(Trip.user_id == target_user.id, Trip.end_date < datetime.utcnow()).first()
        if not has_past_trip:
            past_trip = Trip(
                id=past_trip_id,
                user_id=target_user.id,
                destination="European Backpacking 🎒",
                country="Multiple",
                countries=json.dumps(["France", "Italy", "Spain"]),
                states=json.dumps([]),
                cities=json.dumps(["Paris", "Rome", "Barcelona"]),
                start_date=datetime.utcnow().date() - timedelta(days=365),
                end_date=datetime.utcnow().date() - timedelta(days=345),
                budget_type="budget",
                travel_interests=json.dumps(["Culture", "Food", "History", "Nightlife"]),
                notes="",
                status="completed"
            )
            db.add(past_trip)
            db.commit()
            print(f"Created past trip for target user: added 3 countries.")
        else:
             print("Target user already has a past trip mapped.")

        print("Seeding Complete!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
