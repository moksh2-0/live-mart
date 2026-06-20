"""
OAuth Configuration for Google and Facebook.

Secrets are loaded from environment variables (via a local .env file).
Never hardcode real client secrets in this file - see .env.example.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google OAuth Configuration
# Get credentials from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/OAuth_Callback")

# Facebook OAuth Configuration
# Get credentials from: https://developers.facebook.com/apps/
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8501/OAuth_Callback")
