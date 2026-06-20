"""
Email Configuration for LiveMART (Gmail SMTP).

Secrets are loaded from environment variables (via a local .env file).
Never hardcode a real Gmail App Password in this file - see .env.example.
"""
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  # Gmail App Password, not your account password
