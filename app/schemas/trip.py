from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any
from datetime import date, datetime
import json
from app.schemas.user import UserProfile

class TripBase(BaseModel):
    destination: str
    country: Optional[str] = None
    countries: Optional[List[str]] = None
    states: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    travel_interests: Optional[List[str]] = None
    start_date: date
    end_date: date
    budget_type: str = Field(..., pattern="^(budget|mid|luxury)$")
    notes: Optional[str] = None
    open_to_join: bool = False

    @model_validator(mode='before')
    @classmethod
    def parse_json_strings(cls, data: Any) -> Any:
        if hasattr(data, '__dict__'):
            # If from ORM, cities/travel_interests will be stored as JSON strings
            cities = getattr(data, 'cities', None)
            if isinstance(cities, str):
                try:
                    data.cities = json.loads(cities)
                except (ValueError, TypeError):
                    data.cities = []
                    
            travel_interests = getattr(data, 'travel_interests', None)
            if isinstance(travel_interests, str):
                try:
                    data.travel_interests = json.loads(travel_interests)
                except (ValueError, TypeError):
                    data.travel_interests = []

            countries = getattr(data, 'countries', None)
            if isinstance(countries, str):
                try:
                    data.countries = json.loads(countries)
                except (ValueError, TypeError):
                    data.countries = []

            states = getattr(data, 'states', None)
            if isinstance(states, str):
                try:
                    data.states = json.loads(states)
                except (ValueError, TypeError):
                    data.states = []

        return data

class TripCreate(TripBase):
    pass

class TripResponse(TripBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TripWithUserResponse(TripResponse):
    user: UserProfile
