"""Create saved_posts table for bookmark functionality."""
from app.database import engine, Base
from app.models.saved_post import SavedPost

if __name__ == "__main__":
    SavedPost.__table__.create(engine, checkfirst=True)
    print("✅ saved_posts table created successfully!")
