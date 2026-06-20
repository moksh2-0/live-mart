"""
OAuth integration for Google and Facebook social login
"""
import streamlit as st
import os
import requests
from urllib.parse import urlencode, parse_qs, urlparse
from utils.database import get_user_by_email, save_user
from utils.auth import hash_password

def get_google_oauth_config():
    """Get Google OAuth configuration."""
    # Check Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'google_oauth' in st.secrets:
            return {
                'client_id': st.secrets.google_oauth.client_id,
                'client_secret': st.secrets.google_oauth.client_secret,
                'redirect_uri': st.secrets.google_oauth.get('redirect_uri', 'http://localhost:8501/OAuth_Callback')
            }
    except Exception:
        pass
    
    # Check environment variables
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret:
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501/OAuth_Callback')
        }
    
    # Check config file
    try:
        from config_oauth import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            return {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': GOOGLE_REDIRECT_URI
            }
    except ImportError:
        pass
    
    return None

def get_facebook_oauth_config():
    """Get Facebook OAuth configuration."""
    # Check Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'facebook_oauth' in st.secrets:
            return {
                'app_id': st.secrets.facebook_oauth.app_id,
                'app_secret': st.secrets.facebook_oauth.app_secret,
                'redirect_uri': st.secrets.facebook_oauth.get('redirect_uri', 'http://localhost:8501/oauth_callback')
            }
    except Exception:
        pass
    
    # Check environment variables
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    
    if app_id and app_secret:
        return {
            'app_id': app_id,
            'app_secret': app_secret,
            'redirect_uri': os.getenv('FACEBOOK_REDIRECT_URI', 'http://localhost:8501/oauth_callback')
        }
    
    # Check config file
    try:
        from config_oauth import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_REDIRECT_URI
        if FACEBOOK_APP_ID and FACEBOOK_APP_SECRET:
            return {
                'app_id': FACEBOOK_APP_ID,
                'app_secret': FACEBOOK_APP_SECRET,
                'redirect_uri': FACEBOOK_REDIRECT_URI
            }
    except ImportError:
        pass
    
    return None

def get_google_oauth_url(state=None):
    """Generate Google OAuth authorization URL."""
    config = get_google_oauth_config()
    if not config:
        return None
    
    params = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    if state:
        params['state'] = state
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return auth_url

def get_facebook_oauth_url(state=None):
    """Generate Facebook OAuth authorization URL."""
    config = get_facebook_oauth_config()
    if not config:
        return None
    
    params = {
        'client_id': config['app_id'],
        'redirect_uri': config['redirect_uri'],
        'scope': 'email,public_profile',
        'response_type': 'code'
    }
    
    if state:
        params['state'] = state
    
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
    return auth_url

def exchange_google_code_for_token(code):
    """Exchange Google authorization code for access token."""
    config = get_google_oauth_config()
    if not config:
        return None
    
    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'code': code,
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'redirect_uri': config['redirect_uri'],
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error exchanging Google code: {str(e)}")
    
    return None

def exchange_facebook_code_for_token(code):
    """Exchange Facebook authorization code for access token."""
    config = get_facebook_oauth_config()
    if not config:
        return None
    
    token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'
    params = {
        'client_id': config['app_id'],
        'client_secret': config['app_secret'],
        'redirect_uri': config['redirect_uri'],
        'code': code
    }
    
    try:
        response = requests.get(token_url, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error exchanging Facebook code: {str(e)}")
    
    return None

def get_google_user_info(access_token):
    """Get user information from Google using access token."""
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error getting Google user info: {str(e)}")
    
    return None

def get_facebook_user_info(access_token):
    """Get user information from Facebook using access token."""
    try:
        response = requests.get(
            'https://graph.facebook.com/v18.0/me',
            params={
                'fields': 'id,name,email',
                'access_token': access_token
            }
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error getting Facebook user info: {str(e)}")
    
    return None

def handle_google_oauth(code):
    """Handle Google OAuth callback and create/login user."""
    # Exchange code for token
    token_data = exchange_google_code_for_token(code)
    if not token_data:
        return False, "Failed to get access token", None, None
    
    access_token = token_data.get('access_token')
    if not access_token:
        return False, "No access token received", None, None
    
    # Get user info
    user_info = get_google_user_info(access_token)
    if not user_info:
        return False, "Failed to get user information", None, None
    
    email = user_info.get('email')
    name = user_info.get('name', 'User')
    
    if not email:
        return False, "No email found in Google account", None, None
    
    # Check if user exists
    existing_user = get_user_by_email(email)
    if existing_user:
        # Login existing user
        st.session_state.user = existing_user
        st.session_state.role = existing_user.get('role')
        return True, "Login successful", None, None
    else:
        # Store user info for role selection
        oauth_user_data = {
            'name': name,
            'email': email,
            'location': user_info.get('locale', 'Unknown'),
            'oauth_provider': 'google',
            'oauth_id': user_info.get('id')
        }
        # Store access token in session state for later use
        st.session_state.oauth_access_token = access_token
        # Return user data so callback page can prompt for role
        return False, "role_selection_required", oauth_user_data, access_token

def handle_facebook_oauth(code):
    """Handle Facebook OAuth callback and create/login user."""
    # Exchange code for token
    token_data = exchange_facebook_code_for_token(code)
    if not token_data:
        return False, "Failed to get access token", None, None
    
    access_token = token_data.get('access_token')
    if not access_token:
        return False, "No access token received", None, None
    
    # Get user info
    user_info = get_facebook_user_info(access_token)
    if not user_info:
        return False, "Failed to get user information", None, None
    
    email = user_info.get('email')
    name = user_info.get('name', 'User')
    
    if not email:
        return False, "No email found in Facebook account", None, None
    
    # Check if user exists
    existing_user = get_user_by_email(email)
    if existing_user:
        # Login existing user
        st.session_state.user = existing_user
        st.session_state.role = existing_user.get('role')
        return True, "Login successful", None, None
    else:
        # Store user info for role selection
        oauth_user_data = {
            'name': name,
            'email': email,
            'location': 'Unknown',
            'oauth_provider': 'facebook',
            'oauth_id': user_info.get('id')
        }
        # Store access token in session state for later use
        st.session_state.oauth_access_token = access_token
        # Return user data so callback page can prompt for role
        return False, "role_selection_required", oauth_user_data, access_token

def create_oauth_user(oauth_user_data, role):
    """Create a new user account from OAuth data with selected role."""
    user_data = {
        'name': oauth_user_data['name'],
        'email': oauth_user_data['email'],
        'password': hash_password(oauth_user_data['email'] + str(os.urandom(16))),  # Random password for OAuth users
        'role': role,
        'location': oauth_user_data.get('location', 'Unknown'),
        'oauth_provider': oauth_user_data.get('oauth_provider'),
        'oauth_id': oauth_user_data.get('oauth_id')
    }
    
    if save_user(user_data):
        user = get_user_by_email(oauth_user_data['email'])
        st.session_state.user = user
        st.session_state.role = user.get('role')
        return True, "Registration successful"
    else:
        return False, "Failed to create account"

