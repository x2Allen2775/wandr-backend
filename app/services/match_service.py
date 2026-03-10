from sqlalchemy.orm import Session
from datetime import date
from app.models.user import User
from app.models.trip import Trip
from app.schemas.match import MatchSuggestionResponse
from app.schemas.user import UserProfile

def generate_match_suggestions(db: Session, current_user: User, limit: int = 50) -> list[MatchSuggestionResponse]:
    """
    Core Match Engine Algorithm.
    Scores all active users against the current user out of 5 possible points:
    +2: Has an upcoming trip to the exact same Destination.
    +1: Has an upcoming trip whose dates overlap with yours.
    +1: Shares at least one explicit Onboarding 'Interest'.
    +1: Budget Preference or Active Trip Budget matches yours.
    """
    # 1. Gather all other users
    all_users = db.query(User).filter(User.id != current_user.id).all()
    suggestions = []
    
    # 2. Pre-compute current user's active vectors
    today = date.today()
    my_active_trips = [t for t in current_user.trips if t.end_date >= today and t.status != "completed"]
    my_destinations = {t.destination.lower() for t in my_active_trips}
    my_interests = {interest.name.lower() for interest in current_user.interests}
    
    for other_user in all_users:
        score = 0
        reasons = []
        
        their_active_trips = [t for t in other_user.trips if t.end_date >= today and t.status != "completed"]
        
        # Rule 1 (+2): Destination Match
        their_destinations = {t.destination.lower() for t in their_active_trips}
        shared_destinations = my_destinations.intersection(their_destinations)
        if shared_destinations:
            score += 2
            # Capitalize nicely for the UI
            dest_str = list(shared_destinations)[0].title()
            reasons.append(f"Also going to {dest_str}")
            
        # Rule 2 (+1): Date Overlap
        has_overlap = False
        for my_trip in my_active_trips:
            for their_trip in their_active_trips:
                if my_trip.start_date <= their_trip.end_date and my_trip.end_date >= their_trip.start_date:
                    has_overlap = True
                    break
            if has_overlap: break
            
        if has_overlap:
            score += 1
            reasons.append("Travel dates overlap")
            
        # Rule 3 (+1): Shared Interests
        their_interests = {i.name.lower() for i in other_user.interests}
        shared_interests = my_interests.intersection(their_interests)
        if shared_interests:
            score += 1
            # Just show one shared interest as the primary reason
            int_str = list(shared_interests)[0].title()
            reasons.append(f"Shares interest in {int_str}")
            
        # Rule 4 (+1): Budget Match
        # Check overall preference first, then fall back to active trips
        budget_matched = False
        if current_user.budget_preference and current_user.budget_preference == other_user.budget_preference:
            budget_matched = True
        elif my_active_trips and their_active_trips:
            my_budgets = {t.budget_type for t in my_active_trips if t.budget_type}
            their_budgets = {t.budget_type for t in their_active_trips if t.budget_type}
            if my_budgets.intersection(their_budgets):
                budget_matched = True
        
        if budget_matched:
            score += 1
            budget_str = current_user.budget_preference or "Similar"
            reasons.append(f"{budget_str.title()} travel budget")
            
        # Compile Suggestion
        # Only suggest people with a score > 0
        if score > 0:
            user_response = UserProfile.model_validate(other_user)
            suggestions.append(
                MatchSuggestionResponse(
                    user=user_response,
                    score=score,
                    match_reasons=reasons
                )
            )
            
    # Sort primarily by score (descending)
    suggestions.sort(key=lambda x: x.score, reverse=True)
    
    return suggestions[:limit]
