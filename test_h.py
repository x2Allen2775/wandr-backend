import sys
import os

# allow importing app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.user import User, FollowRequest
from app.models.post import Post
from app.models.trip import Trip
from app.models.interest import Interest
from app.services.user_service import _deserialize_user
from app.schemas.user import UserProfile, RemoteProfileResponse

def test():
    q = "h"
    db = SessionLocal()
    
    current_user = db.query(User).filter_by(username="allen2775").first()
    
    results = db.query(User).filter(
        User.username.ilike(f"%{q}%"),
        User.id != current_user.id
    ).limit(20).all()

    print(f"Total matching query '{q}':", len(results))
    
    current_following_ids = {u.id for u in current_user.following}
    
    response = []
    
    for u in results:
        print("- Raw SQLAlchemy user:", u.username)
        # try pydantic parse
        base_prof = UserProfile.from_orm(_deserialize_user(u)).dict()
        
        status = "none"
        follower_count = len(u.followers) if isinstance(u.followers, list) else u.followers.count()
        following_count = len(u.following) if isinstance(u.following, list) else u.following.count()
        
        target_followers_list = u.followers if isinstance(u.followers, list) else u.followers.all()
        target_followers = {f.id for f in target_followers_list}
        mutuals = len(current_following_ids.intersection(target_followers))
        
        profile_dict = {
            **base_prof,
            "follower_count": follower_count,
            "following_count": following_count,
            "mutual_connections_count": mutuals,
            "follow_status": status
        }
        resp = RemoteProfileResponse.parse_obj(profile_dict)
        response.append(resp.dict())
        
    print("Success")

if __name__ == "__main__":
    test()
