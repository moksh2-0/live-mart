# Integrations Setup Guide

LiveMART works out of the box with **zero configuration** - every external integration
below is optional, and the app gracefully falls back to a mock/simulated version if
the corresponding environment variable isn't set. Use this guide only if you want the
real version of a given feature.

All values go in a `.env` file in the project root (copy `.env.example` to start).
`.env` is gitignored and should never be committed.

---

## 1. Google OAuth (real "Sign in with Google")

Without this, the Google login button still appears but just simulates a successful
login - useful for demos, not real authentication.

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a project (or reuse one), then **Create Credentials → OAuth Client ID**
   - Application type: **Web application**
3. Under **Authorized redirect URIs**, add exactly:
   ```
   http://localhost:8501/OAuth_Callback
   ```
   (must be `http://localhost:8501`, not `127.0.0.1`, and the path is case-sensitive)
4. Copy the generated Client ID and Client Secret into `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
5. If you get `Error 400: redirect_uri_mismatch`, double-check the URI in Cloud Console
   matches your running app's port exactly, and wait 1-2 minutes after saving for the
   change to propagate.

Facebook login follows the same pattern via `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET`
from the [Facebook Developer Console](https://developers.facebook.com/apps/).

---

## 2. Gmail SMTP (real order/notification emails)

Without this, emails are just logged rather than sent.

1. Use a Google Account with [2-Step Verification](https://myaccount.google.com/security) enabled.
2. Generate an **App Password**: Google Account → Security → App Passwords → choose
   "Mail" → generate. This is a 16-character password, separate from your real Gmail
   password.
3. Add to `.env`:
   ```
   SENDER_EMAIL=your-address@gmail.com
   SENDER_PASSWORD=your-16-char-app-password
   ```
4. Never use your actual Google account password here, and never commit this value.
   If an app password is ever accidentally exposed, revoke it immediately from the
   App Passwords page and generate a new one.

---

## 3. Google Maps / Geocoding (real location matching)

Without this, location filtering falls back to basic text matching instead of
distance-based sorting.

1. In the same Google Cloud project, enable the **Geocoding API** (APIs & Services → Library).
2. Create an API key (APIs & Services → Credentials → Create Credentials → API Key).
3. Restrict the key to the Geocoding API only (recommended).
4. Add to `.env`:
   ```
   GOOGLE_MAPS_API_KEY=your-api-key
   ```

**Cost note:** Google gives new accounts a $300/90-day free trial plus a recurring
$200/month credit, which comfortably covers light testing/demo usage (a few hundred
geocoding requests costs well under $1). You do need to add a billing method to enable
the API, but you won't be charged while under the free credit.

---

## Troubleshooting

- **Import errors** → make sure you're running `streamlit run app.py` from the project root.
- **Stale session state** → clear browser cache / open an incognito window.
- **Missing data** → confirm the `data/` directory and its JSON files exist and are valid JSON.
