"""
Google Maps / Geocoding Configuration.

Secrets are loaded from environment variables (via a local .env file).
Never hardcode a real API key in this file - see .env.example.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Default coordinates (latitude, longitude) - used as a fallback map center
DEFAULT_COORDINATES = {
    "latitude": float(os.getenv("DEFAULT_LATITUDE", "17.54")),
    "longitude": float(os.getenv("DEFAULT_LONGITUDE", "78.57")),
}

# Google Maps API Key - get one from https://console.cloud.google.com/apis/credentials
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
