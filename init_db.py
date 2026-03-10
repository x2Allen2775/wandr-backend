from app.database import engine, Base
from app.models.user import User, FollowRequest, PasswordReset
from app.models.post import Post
from app.models.trip import Trip
from app.models.interest import Interest
from app.models.message import Conversation, Message
from app.models.itinerary import Itinerary, ItineraryMessage
from app.models.notification import Notification

print("Dropping and recreating all tables in Supabase Postgres...")
Base.metadata.create_all(bind=engine)
print("Successfully deployed schema to Supabase!")
