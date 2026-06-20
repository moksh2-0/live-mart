import streamlit as st
import os
from utils.auth import (
    register_user, login_user, generate_otp, store_otp, 
    verify_otp, get_current_user, is_authenticated
)
from utils.database import get_user_by_email

st.set_page_config(page_title="LiveMART - Login / Register", page_icon=None, layout="centered")

# Redirect if already logged in
if is_authenticated():
    user = get_current_user()
    role = user.get("role", "")
    st.success("Logged In Successfully!")
    # Set flag to show balloons on dashboard
    st.session_state.show_login_balloons = True
    # Auto-redirect to respective dashboard
    if role == "customer":
        st.switch_page("pages/2_Customer_Dashboard.py")
    elif role == "retailer":
        st.switch_page("pages/3_Retailer_Dashboard.py")
    elif role == "wholesaler":
        st.switch_page("pages/4_Wholesaler_Dashboard.py")
    st.stop()

st.title("Login / Register")

# Tabs for Login and Register
tab1, tab2, tab3 = st.tabs(["Login", "Register", "Social Login"])

# Login Tab
with tab1:
    st.header("Login to your account")
    
    # Check if forgot password mode is active
    forgot_password_mode = st.session_state.get("forgot_password_mode", False)
    
    if not forgot_password_mode:
        # Normal login with password
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                login_submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            with col2:
                forgot_password_btn = st.form_submit_button("Forgot Password?", use_container_width=True)
            
            if login_submit:
                if not email or not password:
                    st.error("Please fill in all fields")
                else:
                    # Password login
                    user = login_user(email, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.role = user.get("role")
                        st.success("Logged In Successfully!")
                        # Set flag to show balloons on dashboard
                        st.session_state.show_login_balloons = True
                        # Redirect to respective dashboard
                        role = user.get("role", "")
                        if role == "customer":
                            st.switch_page("pages/2_Customer_Dashboard.py")
                        elif role == "retailer":
                            st.switch_page("pages/3_Retailer_Dashboard.py")
                        elif role == "wholesaler":
                            st.switch_page("pages/4_Wholesaler_Dashboard.py")
                    else:
                        st.error("Invalid email or password")
            
            if forgot_password_btn:
                if not email:
                    st.error("Please enter your email address first")
                else:
                    # Check if user exists
                    user = get_user_by_email(email)
                    if user:
                        st.session_state.forgot_password_mode = True
                        st.session_state.forgot_password_email = email
                        st.rerun()
                    else:
                        st.error("User not found. Please register first.")
        
        # Forgot Password Link (alternative)
        st.markdown("---")
        if st.button("Forgot Password? Login with OTP", use_container_width=True):
            st.session_state.forgot_password_mode = True
            st.rerun()
    
    else:
        # Forgot Password - OTP Login Mode
        st.subheader("Forgot Password - Login with OTP")
        email = st.session_state.get("forgot_password_email", "")
        
        if email:
            st.info(f"An OTP will be sent to: **{email}**")
        
        with st.form("forgot_password_form"):
            if not email:
                email = st.text_input("Email", placeholder="your.email@example.com", key="forgot_email")
            
            send_otp_btn = st.form_submit_button("Send OTP", use_container_width=True, type="primary")
            
            if send_otp_btn:
                if not email:
                    st.error("Please enter your email address")
                else:
                    # Check if user exists
                    user = get_user_by_email(email)
                    if user:
                        # Generate and send OTP
                        otp = generate_otp()
                        store_otp(email, otp)
                        st.session_state.login_otp_sent = True
                        st.session_state.login_email = email
                        st.session_state.login_user = user
                        st.session_state.forgot_password_email = email
                        
                        # Try to send OTP via email
                        try:
                            from utils.email_service import send_otp_email
                            email_sent, email_msg = send_otp_email(email, otp, "password reset")
                            if email_sent:
                                st.success(f"OTP sent to {email} via email! Please check your inbox.")
                                st.info("Didn't receive the email? Check your spam folder.")
                            else:
                                # Fallback to displaying OTP if email not configured
                                st.warning(f"Email not configured. Your OTP: **{otp}**")
                                st.info(f"{email_msg}")
                        except Exception as e:
                            # Fallback if email service fails
                            st.warning(f"Email service unavailable. Your OTP: **{otp}**")
                            st.caption(f"Error: {str(e)}")
                    else:
                        st.error("User not found. Please register first.")
        
        # Back to normal login
        if st.button("← Back to Password Login", use_container_width=True):
            st.session_state.forgot_password_mode = False
            if "forgot_password_email" in st.session_state:
                del st.session_state.forgot_password_email
            st.rerun()
    
    # OTP Verification for Login (outside the form)
    if st.session_state.get("login_otp_sent", False):
        st.divider()
        st.subheader("Verify OTP")
        with st.form("login_otp_verification_form"):
            otp_entered = st.text_input("Enter OTP", key="login_otp_input")
            verify_submit = st.form_submit_button("Verify OTP", use_container_width=True)
            
            if verify_submit:
                email = st.session_state.get("login_email")
                if verify_otp(email, otp_entered):
                    user = st.session_state.get("login_user")
                    st.session_state.user = user
                    st.session_state.role = user.get("role")
                    # Clear OTP state and forgot password mode
                    st.session_state.login_otp_sent = False
                    st.session_state.forgot_password_mode = False
                    if "login_email" in st.session_state:
                        del st.session_state.login_email
                    if "login_user" in st.session_state:
                        del st.session_state.login_user
                    if "forgot_password_email" in st.session_state:
                        del st.session_state.forgot_password_email
                    st.success("Logged In Successfully!")
                    # Set flag to show balloons on dashboard
                    st.session_state.show_login_balloons = True
                    # Redirect to respective dashboard
                    role = user.get("role", "")
                    if role == "customer":
                        st.switch_page("pages/2_Customer_Dashboard.py")
                    elif role == "retailer":
                        st.switch_page("pages/3_Retailer_Dashboard.py")
                    elif role == "wholesaler":
                        st.switch_page("pages/4_Wholesaler_Dashboard.py")
                else:
                    st.error("Invalid OTP")

# Register Tab
with tab2:
    st.header("Create a new account")
    
    with st.form("register_form"):
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        role = st.selectbox("Select Role", ["customer", "retailer", "wholesaler"], 
                           help="Choose your role: Customer (buy products), Retailer (sell to customers), Wholesaler (sell to retailers)")
        # Location input with validation and examples
        st.markdown("**Location** (Required)")
        st.caption("Format: City, State, Country (e.g., 'Hyderabad, Telangana, India' or 'Mumbai, Maharashtra, India')")
        
        location = st.text_input(
            "Enter your location", 
            placeholder="e.g., Hyderabad, Telangana, India",
            help="Use format: City, State, Country. More specific = better location features!",
            key="register_location_input"
        )
        
        # Location format validation helper
        if location:
            # Check if location has commas (indicating proper format)
            location_parts = [p.strip() for p in location.split(',')]
            if len(location_parts) < 2:
                st.warning("**Tip:** For better results, use format: 'City, State, Country' (e.g., 'Hyderabad, Telangana, India')")
            elif len(location_parts) == 2:
                st.info("**Good!** Even better if you include country: 'City, State, Country'")
            else:
                st.success("**Great format!** This will work well with location features.")
        
        # Common location examples
        with st.expander("Common Location Examples"):
            st.markdown("""
            **India:**
            - Hyderabad, Telangana, India
            - Mumbai, Maharashtra, India
            - Delhi, Delhi, India
            - Bangalore, Karnataka, India
            - Chennai, Tamil Nadu, India
            - Kolkata, West Bengal, India
            
            **Other:**
            - London, England, UK
            - New York, New York, USA
            - Sydney, New South Wales, Australia
            
            **Minimum required:** City, Country (e.g., 'Hyderabad, India')
            """)
        
        st.info("OTP verification is required for registration. You'll receive an OTP via email.")
        
        register_submit = st.form_submit_button("Register & Send OTP", use_container_width=True, type="primary")
        
        if register_submit:
            # Validation
            if not all([name, email, password, confirm_password, role, location]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            elif get_user_by_email(email):
                st.error("User with this email already exists")
            # Location format validation
            elif not location or len(location.strip()) < 3:
                st.error("Please enter a valid location (at least 3 characters)")
            elif ',' not in location:
                st.error("**Location format invalid!**")
                st.warning("Please use format: **City, State, Country**")
                st.info("**Example:** 'Hyderabad, Telangana, India' or at minimum 'Hyderabad, India'")
                st.stop()  # Stop registration until format is fixed
            else:
                # OTP Verification is MANDATORY for registration
                # Generate and send OTP
                otp = generate_otp()
                store_otp(email, otp)
                st.session_state.otp_sent = True
                st.session_state.registration_data = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": role,
                    "location": location
                }
                
                # Try to send OTP via email
                try:
                    from utils.email_service import send_otp_email
                    email_sent, email_msg = send_otp_email(email, otp, "registration")
                    if email_sent:
                        st.success(f"OTP sent to {email} via email! Please check your inbox.")
                        st.info("Didn't receive the email? Check your spam folder or the OTP may be displayed below if email service is not configured.")
                    else:
                        # Fallback to displaying OTP if email not configured
                        st.warning(f"Email not configured. Your OTP: **{otp}**")
                        st.info(f"{email_msg}")
                except Exception as e:
                    # Fallback if email service fails
                    st.warning(f"Email service unavailable. Your OTP: **{otp}**")
                    st.caption(f"Error: {str(e)}")
    
    # OTP Verification (outside the form)
    if st.session_state.get("otp_sent", False) and st.session_state.get("registration_data"):
        st.divider()
        st.subheader("Verify OTP")
        with st.form("otp_verification_form"):
            otp_entered = st.text_input("Enter OTP", key="register_otp")
            verify_submit = st.form_submit_button("Verify OTP and Register", use_container_width=True)
            
            if verify_submit:
                email = st.session_state.registration_data.get("email")
                if verify_otp(email, otp_entered):
                    user_data = st.session_state.registration_data
                    success, message = register_user(user_data)
                    if success:
                        st.success(message)
                        
                        # Geocode location and store coordinates
                        user = get_user_by_email(email)
                        if user:
                            try:
                                from utils.geocoding import geocode_user_location
                                geocode_result = geocode_user_location(user, update_user=True)
                                if geocode_result.get("success"):
                                    formatted_addr = geocode_result.get('formatted_address', location)
                                    st.success(f"Location verified: **{formatted_addr}**")
                                    st.info("Your location is set up correctly for distance filtering and location-based features!")
                                elif geocode_result.get("error"):
                                    error_msg = geocode_result.get("error", "")
                                    if "not found" in error_msg.lower() or "ZERO_RESULTS" in error_msg:
                                        st.warning(f"⚠️ **Location '{location}' not found by Google Maps.**")
                                        st.error("❌ **Registration successful, but location features won't work until you fix your location.**")
                                        st.info("💡 **Please update your location to:** 'City, State, Country' format (e.g., 'Hyderabad, Telangana, India')")
                                        st.info("🔧 You can update it in your Customer Dashboard → Location Filter")
                                    elif "API key" not in error_msg:
                                        st.warning(f"⚠️ Location geocoding failed: {error_msg}. You can update your location later.")
                                    else:
                                        st.info("💡 Location coordinates will be calculated when you use location-based features.")
                            except Exception as e:
                                st.info("💡 Location coordinates will be calculated when you use location-based features.")
                        
                        # Clear OTP state
                        st.session_state.otp_sent = False
                        if "registration_data" in st.session_state:
                            del st.session_state.registration_data
                        # Auto login
                        user = get_user_by_email(email)
                        st.session_state.user = user
                        st.session_state.role = user.get("role")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Invalid OTP")

# Social Login Tab
with tab3:
    st.header("Login with Google")
    
    from utils.oauth import (
        get_google_oauth_url,
        get_google_oauth_config
    )
    
    google_config = get_google_oauth_config()
    
    if google_config:
        # Generate Google OAuth URL
        state = f"google_{os.urandom(16).hex()}"
        st.session_state.oauth_state = state
        google_url = get_google_oauth_url(state)
        
        if google_url:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # OAuth link opens in same window to preserve session state
                # No target="_blank" - this keeps session state intact
                st.markdown(f'''
                    <div style="margin: 1rem 0;">
                        <a href="{google_url}" style="text-decoration: none; display: block;">
                            <button style="background-color: #4285F4; color: white; padding: 1rem 2rem; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; width: 100%; font-size: 1.1rem; display: block;">🔴 Continue with Google</button>
                        </a>
                    </div>
                    ''', unsafe_allow_html=True)
                st.caption("After login, you'll be redirected back to your dashboard.")
        else:
            st.error("Failed to generate Google OAuth URL")
    else:
        st.warning("Google OAuth not configured. Add credentials in `config_oauth.py` or set environment variables.")
        with st.expander("📖 Setup Instructions"):
            st.markdown("""
            ### Google OAuth Setup:
            1. Go to https://console.cloud.google.com/
            2. Create a project or select existing
            3. Enable Google+ API
            4. Create OAuth 2.0 credentials
            5. Add authorized redirect URI: `http://localhost:8501/OAuth_Callback`
            6. Copy Client ID and Client Secret to `config_oauth.py`
            """)

