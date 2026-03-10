from fastapi import APIRouter, Depends, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User, FollowRequest
from app.schemas.user import UserProfile, ProfileUpdate, TravelInterests, MessageResponse, RemoteProfileResponse
from app.services.user_service import get_user_profile, update_user_profile, save_travel_interests, _deserialize_user
from app.utils.jwt import get_current_user
import os
import uuid as uuid_mod

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user's profile",
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    🔒 **Protected** — requires Bearer token.

    Returns the full profile of the currently authenticated user.
    """
    return _deserialize_user(current_user)


@router.put(
    "/me",
    response_model=UserProfile,
    summary="Update current user's profile",
)
def update_my_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🔒 **Protected** — requires Bearer token.

    Update any of: `full_name`, `bio`, `profile_picture`, `location`,
    `website`, `travel_interests`, `countries_visited`, `travel_style`, `languages`.

    Only fields you include in the request body will be updated.
    """
    user = update_user_profile(current_user, payload, db)
    return _deserialize_user(user)


@router.post(
    "/me/interests",
    response_model=UserProfile,
    summary="Save onboarding travel interests",
)
def set_travel_interests(
    payload: TravelInterests,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🔒 **Protected** — requires Bearer token.

    Called during **onboarding** after first login.
    User selects their travel preferences:
    `["solo", "group", "beaches", "mountains", "backpacking", ...]`
    """
    user = save_travel_interests(current_user, payload, db)
    return _deserialize_user(user)

@router.post(
    "/toggle-privacy",
    response_model=UserProfile,
    summary="Toggle Public vs Private Account",
)
def toggle_privacy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Switch account privacy."""
    current_user.is_public = not current_user.is_public
    db.commit()
    db.refresh(current_user)
    return _deserialize_user(current_user)


@router.get(
    "/search",
    response_model=list[RemoteProfileResponse],
    summary="Search Users globally",
)
def search_profiles(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find users by username matching the query `q`.
    Calculates follow status and obscures private data if needed.
    """
    results = db.query(User).filter(
        or_(
            User.username.ilike(f"%{q}%"),
            User.full_name.ilike(f"%{q}%")
        ),
        User.id != current_user.id
    ).limit(20).all()

    response = []
    
    current_following_ids = {u.id for u in current_user.following}
    
    for u in results:
        base_prof = UserProfile.from_orm(_deserialize_user(u)).dict()
        
        status = "none"
        if u.id in current_following_ids:
            status = "following"
        else:
            # Check for request
            req = db.query(FollowRequest).filter(
                FollowRequest.sender_id == current_user.id,
                FollowRequest.receiver_id == u.id
            ).first()
            if req:
                status = "requested"
                
        follower_count = len(u.followers) if isinstance(u.followers, list) else u.followers.count()
        following_count = len(u.following) if isinstance(u.following, list) else u.following.count()
        
        target_followers_list = u.followers if isinstance(u.followers, list) else u.followers.all()
        target_followers = {f.id for f in target_followers_list}
        mutuals = len(current_following_ids.intersection(target_followers))
        
        # If private and not following, obscure some data
        if not u.is_public and status != "following":
            base_prof["location"] = None
            base_prof["bio"] = "This account is private."
            
        profile_dict = {
            **base_prof,
            "follower_count": follower_count,
            "following_count": following_count,
            "mutual_connections_count": mutuals,
            "follow_status": status
        }
        response.append(RemoteProfileResponse.parse_obj(profile_dict))
        
    return response


@router.get(
    "/{user_id}",
    response_model=RemoteProfileResponse,
    summary="Get another user's profile by ID",
)
def get_user_profile_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🔒 **Protected** — requires Bearer token.

    Fetch any user's public profile by their user ID.
    Includes follow_status, follower/following counts, mutual connections.
    Private accounts show limited info if not following.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found.")

    base_prof = UserProfile.from_orm(_deserialize_user(target)).dict()

    # Determine follow status
    current_following_ids = {u.id for u in current_user.following}
    status = "none"
    if target.id in current_following_ids:
        status = "following"
    else:
        req = db.query(FollowRequest).filter(
            FollowRequest.sender_id == current_user.id,
            FollowRequest.receiver_id == target.id
        ).first()
        if req:
            status = "requested"

    follower_count = len(target.followers) if isinstance(target.followers, list) else target.followers.count()
    following_count = len(target.following) if isinstance(target.following, list) else target.following.count()

    target_followers_list = target.followers if isinstance(target.followers, list) else target.followers.all()
    target_followers = {f.id for f in target_followers_list}
    mutuals = len(current_following_ids.intersection(target_followers))

    # If private and not following, obscure some data
    if not target.is_public and status != "following":
        base_prof["location"] = None
        base_prof["bio"] = "This account is private."

    profile_dict = {
        **base_prof,
        "follower_count": follower_count,
        "following_count": following_count,
        "mutual_connections_count": mutuals,
        "follow_status": status,
    }
    return RemoteProfileResponse.parse_obj(profile_dict)


AVATAR_DIR = "uploads/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

@router.post(
    "/me/avatar",
    response_model=UserProfile,
    summary="Upload or change profile picture",
)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a profile picture. Saves the file and updates the user's profile_picture URL.
    """
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid_mod.uuid4().hex}.{ext}"
    file_path = os.path.join(AVATAR_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8000')}"
    file_url = f"{base_url}/uploads/avatars/{unique_filename}"
    current_user.profile_picture = file_url
    db.commit()
    db.refresh(current_user)
    return _deserialize_user(current_user)
