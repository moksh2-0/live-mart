"""
Quick test to verify the correct redirect URI format for Streamlit pages
Run this to see what the actual page URL would be
"""
import streamlit as st

st.set_page_config(page_title="Test Redirect URI", page_icon="🔍")

st.title("OAuth Redirect URI Test")

st.info("""
To find the correct redirect URI for your OAuth callback:

1. **Current configured URI:** `http://localhost:8501/OAuth_Callback`

2. **Try these in Google Cloud Console:**
   - `http://localhost:8501/OAuth_Callback`
   - `http://localhost:8501/9_OAuth_Callback`
   - `http://localhost:8501/?page=OAuth_Callback`

3. **To verify the actual URL:**
   - Start your Streamlit app
   - Navigate to the OAuth Callback page manually
   - Check the URL in your browser's address bar
   - Use that EXACT URL (including any query parameters) in Google Cloud Console

**Important:** The redirect URI in Google Cloud Console must match EXACTLY what you're sending in the OAuth request.
""")

st.markdown("---")
st.markdown("### Current Configuration")
st.code("""
GOOGLE_REDIRECT_URI = "http://localhost:8501/OAuth_Callback"
""")

st.markdown("### Steps to Fix:")
st.markdown("""
1. Go to [Google Cloud Console - OAuth Clients](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   - `http://localhost:8501/OAuth_Callback`
4. Click "Save"
5. Try logging in again
""")

