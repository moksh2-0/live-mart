import hashlib
import random
import streamlit as st
from typing import Optional, Dict, Any
from utils.database import get_user_by_email, save_user, get_user_by_id

def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed

def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def store_otp(email: str, otp: str):
    """Store OTP in session state."""
    if "otp_store" not in st.session_state:
        st.session_state.otp_store = {}
    st.session_state.otp_store[email] = otp

def verify_otp(email: str, entered_otp: str) -> bool:
    """Verify OTP from session state."""
    if "otp_store" not in st.session_state:
        return False
    stored_otp = st.session_state.otp_store.get(email)
    return stored_otp == entered_otp

def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user."""
    user = get_user_by_email(email)
    if user and verify_password(password, user.get("password", "")):
        return user
    return None

def register_user(user_data: Dict[str, Any]):
    """Register a new user."""
    email = user_data.get("email")
    password = user_data.get("password")
    
    if not email or not password:
        return False, "Email and password are required"
    
    # Check if user already exists
    if get_user_by_email(email):
        return False, "User with this email already exists"
    
    # Hash password
    user_data["password"] = hash_password(password)
    
    # Save user
    if save_user(user_data):
        return True, "Registration successful"
    return False, "Registration failed"

def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return "user" in st.session_state and st.session_state.user is not None

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current logged-in user."""
    if is_authenticated():
        return st.session_state.user
    return None

def logout_user():
    """Logout current user."""
    if "user" in st.session_state:
        st.session_state.user = None
    if "role" in st.session_state:
        st.session_state.role = None

def require_auth(required_role: Optional[str] = None):
    """Decorator to require authentication (and optionally a specific role)."""
    if not is_authenticated():
        st.error("Please login to access this page.")
        st.stop()
    
    if required_role:
        user = get_current_user()
        if user and user.get("role") != required_role:
            st.error(f"Access denied. This page is for {required_role}s only.")
            st.stop()

