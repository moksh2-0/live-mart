"""
OAuth callback page for handling Google OAuth redirects
"""
import streamlit as st
from utils.oauth import handle_google_oauth, create_oauth_user

st.set_page_config(page_title="OAuth Callback", page_icon=None, layout="centered", initial_sidebar_state="expanded")

def redirect_to_dashboard():
    """Helper function to redirect user to appropriate dashboard."""
    user = st.session_state.get('user')
    if user:
        role = user.get('role', 'customer')
        if role == 'customer':
            st.switch_page("pages/2_Customer_Dashboard.py")
        elif role == 'retailer':
            st.switch_page("pages/3_Retailer_Dashboard.py")
        elif role == 'wholesaler':
            st.switch_page("pages/4_Wholesaler_Dashboard.py")

# Get query parameters
query_params = st.query_params

# Check for OAuth code
code = query_params.get('code')
state = query_params.get('state')
error = query_params.get('error')

expected_state = st.session_state.get('oauth_state')
state_mismatch = bool(code) and (not state or not expected_state or state != expected_state)

if error:
    st.error(f"OAuth error: {error}")
    if st.button("Go to Login"):
        st.switch_page("pages/1_Registration.py")
elif state_mismatch:
    st.error("This logic account could not be verified (state mismatch). Please try logging in again.")
    if st.button("Go to login"):
        st.switch_page("pages/1_Registration.py")
elif code:
    # Check if we already processed this code and are just waiting for role selection
    if "oauth_user_data" in st.session_state and "oauth_code_processed" in st.session_state:
        # Show role selection for new user (code already processed)
        oauth_data = st.session_state.oauth_user_data
        st.title("Select Your Role")
        st.info(f"Welcome {oauth_data['name']}! Please select your role to complete registration.")
        
        role = st.radio(
            "Choose your account type:",
            ["customer", "retailer", "wholesaler"],
            format_func=lambda x: {
                "customer": "Customer - Browse and purchase products",
                "retailer": "Retailer - Manage inventory and sell products",
                "wholesaler": "Wholesaler - Supply products to retailers"
            }[x]
        )
        
        if st.button("Complete Registration", use_container_width=True):
            success, msg = create_oauth_user(oauth_data, role)
            if success:
                # Clear OAuth session data
                if "oauth_user_data" in st.session_state:
                    del st.session_state.oauth_user_data
                if "oauth_code_processed" in st.session_state:
                    del st.session_state.oauth_code_processed
                if "oauth_access_token" in st.session_state:
                    del st.session_state.oauth_access_token
                if "oauth_state" in  st.session_state:
                    del st.session_state.oauth_state
                
                st.success(f"✅ {msg}")
                st.balloons()
                st.info("Redirecting to dashboard...")
                st.session_state.oauth_role_selected = True
                redirect_to_dashboard()
            else:
                st.error(f"❌ {msg}")
    else:
        # Process the OAuth code for the first time (Google only)
        success, message, oauth_data, access_token = handle_google_oauth(code)
        if success:
            if"oauth_state" in st.session_state:
                del st.session_state.oauth_state
            st.success(f"✅ {message}")
            st.balloons()
            st.info("Redirecting to dashboard...")
            redirect_to_dashboard()
        elif message == "role_selection_required":
            # Store user data in session state
            st.session_state.oauth_user_data = oauth_data
            st.session_state.oauth_code_processed = True
            st.rerun()  # Rerun to show role selection
        else:
            st.error(f"❌ {message}")
            if st.button("Try Again"):
                st.switch_page("pages/1_Registration.py")
else:
    st.warning("No authorization code received.")
    if st.button("Go to Login"):
        st.switch_page("pages/1_Registration.py")

