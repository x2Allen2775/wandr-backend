import os
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.itinerary import Itinerary, ItineraryMessage

class IterinaryService:
    @staticmethod
    def generate_response(db: Session, user: User, itinerary: Itinerary, new_message: str, api_key: str | None) -> str:
        """
        Calls Gemini to get the next step in the chat.
        Injects the user's travel interests as a System Prompt.
        """
        actual_key = api_key or os.getenv("GEMINI_API_KEY")
        if not actual_key:
            return "Hi there! I notice you haven't provided a Gemini API key yet. Please click the key icon in the top right corner to configure your key so we can start planning your trip!"

        try:
            client = genai.Client(api_key=actual_key)
            
            interests = user.interests or "general travel, sightseeing"
            
            system_prompt = (
                f"You are Wandr AI, an expert Travel Planner. The user has the following general travel interests: {interests}. "
                "When planning trips, tailor locations, food, and activities closely to these interests. "
                "If the user does not specify a destination or number of days, courteously ask for them. "
                "Always respond in clean Markdown with nice formatting (headers, bullet points)."
            )
            
            contents = []
            for msg in itinerary.messages:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})
                
            contents.append({"role": "user", "parts": [{"text": new_message}]})
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                )
            )
            
            return response.text or "Sorry, I couldn't generate a response."
            
        except Exception as e:
            return f"**Gemini API Error**: `{str(e)}`\n\nPlease check your API key in the top right corner."

    @staticmethod
    def extract_destination(content: str) -> str:
        """Helper to try and parse out the destination name from the chat stream"""
        return ""
