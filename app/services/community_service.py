from sqlalchemy.orm import Session
from app.models.user import User
from app.models.interest import Interest

def get_users_by_interest(interest_name: str, db: Session, limit: int = 50) -> list[User]:
    """Fetch users that have a specific interest associated with them."""
    # SQLAlchemy Join across the association table seamlessly
    users = (
        db.query(User)
        .join(User.interests)
        .filter(Interest.name == interest_name)
        .filter(User.is_active == True)
        .limit(limit)
        .all()
    )
    return users
