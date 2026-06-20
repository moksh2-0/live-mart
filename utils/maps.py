"""
Google Maps integration for showing nearby stores
"""
import streamlit as st
import os
from utils.database import get_users, get_products

def get_google_maps_api_key():
    """Get Google Maps API key from environment or session state."""
    # Try to load from config file
    try:
        from config_maps import GOOGLE_MAPS_API_KEY
        if GOOGLE_MAPS_API_KEY:
            return GOOGLE_MAPS_API_KEY
    except ImportError:
        pass
    
    # Check session state first (for Streamlit secrets) - handle gracefully
    try:
        if hasattr(st, 'secrets'):
            try:
                if 'google_maps' in st.secrets:
                    return st.secrets.google_maps.api_key
            except Exception:
                # Secrets file doesn't exist or is invalid, continue
                pass
    except Exception:
        # Ignore secrets errors
        pass
    
    # Check environment variable
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if api_key:
        return api_key
    
    # Check session state
    if 'google_maps_api_key' in st.session_state:
        return st.session_state.google_maps_api_key
    
    return None

def get_default_coordinates():
    """Get default coordinates (can be configured)."""
    # Try to load from config file
    try:
        from config_maps import DEFAULT_COORDINATES
        return DEFAULT_COORDINATES.get('latitude', 28.6139), DEFAULT_COORDINATES.get('longitude', 77.2090)
    except ImportError:
        pass
    
    # Try environment variables
    default_lat = os.getenv('DEFAULT_LATITUDE')
    default_lng = os.getenv('DEFAULT_LONGITUDE')
    
    if default_lat and default_lng:
        return float(default_lat), float(default_lng)
    
    # Default coordinates (17.54°N, 78.57°E - Hyderabad area)
    return 17.54, 78.57

def get_store_locations():
    """Get store locations from retailers and wholesalers."""
    users = get_users()
    stores = []
    
    for user in users:
        if user.get("role") in ["retailer", "wholesaler"]:
            location = user.get("location", "")
            if location and location != "Unknown":
                # Capitalize name properly
                name = user.get("name", "Store")
                if name:
                    name = ' '.join(word.capitalize() for word in name.split())
                
                stores.append({
                    "name": name,
                    "role": user.get("role", "").title(),
                    "email": user.get("email", ""),
                    "location": location,
                    "user_id": user.get("user_id", "")
                })
    
    return stores

def render_google_maps_with_stores(api_key=None, center_lat=None, center_lng=None, stores=None):
    """
    Render Google Maps with nearby stores.
    
    Args:
        api_key: Google Maps API key (optional)
        center_lat: Center latitude
        center_lng: Center longitude
        stores: List of store dictionaries with location info
    """
    if center_lat is None or center_lng is None:
        center_lat, center_lng = get_default_coordinates()
    
    if stores is None:
        stores = get_store_locations()
    
    # Use Maps Embed API (works with restricted API key)
    # If we have stores with coordinates, center on them; otherwise use user location
    if stores and any(s.get("latitude") and s.get("longitude") for s in stores):
        # Find center of all stores
        valid_stores = [s for s in stores if s.get("latitude") and s.get("longitude")]
        if valid_stores:
            avg_lat = sum(s.get("latitude") for s in valid_stores) / len(valid_stores)
            avg_lng = sum(s.get("longitude") for s in valid_stores) / len(valid_stores)
            map_center_lat, map_center_lng = avg_lat, avg_lng
        else:
            map_center_lat, map_center_lng = center_lat, center_lng
    else:
        map_center_lat, map_center_lng = center_lat, center_lng
    
    # Build Maps Embed API URL
    # Maps Embed API uses q parameter for location search
    from urllib.parse import quote_plus
    
    # Use coordinates for better accuracy
    location_query = f"{map_center_lat},{map_center_lng}"
    
    # Maps Embed API URL format with API key
    if api_key:
        # Using Maps Embed API with API key - URL encode the query
        encoded_query = quote_plus(location_query)
        embed_url = f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={encoded_query}&zoom=12"
    else:
        # Fallback: Basic embed URL without API key (uses coordinates)
        embed_url = f"https://maps.google.com/maps?q={location_query}&hl=en&z=12&output=embed"
    
    st.markdown(f"""
    <div style="width: 100%; height: 500px; margin: 2rem 0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background-color: #f5f5f5;">
        <iframe
            width="100%"
            height="100%"
            style="border:0;"
            loading="lazy"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            src="{embed_url}">
        </iframe>
    </div>
    """, unsafe_allow_html=True)
    
    # Direct link to Google Maps
    direct_map_url = f"https://www.google.com/maps?q={location_query}"
    st.markdown(f'<div style="text-align: center; margin: 1rem 0;"><a href="{direct_map_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #000; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">Open In Google Maps</button></a></div>', unsafe_allow_html=True)
    
    # Note: Maps Embed API shows a basic map. For interactive markers, 
    # users can click on store links below to open in Google Maps
    
    # Display store list (sorted by distance if available)
    if stores:
        # Sort by distance if available
        stores_sorted = sorted(stores, key=lambda s: s.get("distance_km", float('inf')))
        
        st.markdown("### Store List")
        if any(s.get("distance_km") for s in stores_sorted):
            st.caption("Stores sorted by distance (nearest first)")
        
        for idx, store in enumerate(stores_sorted, 1):
            # Capitalize store name
            store_name = store.get('name', 'Store')
            if store_name:
                store_name = ' '.join(word.capitalize() for word in store_name.split())
            
            store_role = store.get('role', '').title()
            store_location = store.get('location', 'N/A')
            distance = store.get('distance_km')
            
            # Create expander title with distance if available
            if distance:
                title = f"{idx}. {store_name} - {store_role} ({distance} km away)"
            else:
                title = f"{idx}. {store_name} - {store_role}"
            
            with st.expander(title):
                st.write(f"**Location:** {store_location}")
                st.write(f"**Email:** {store.get('email', 'N/A')}")
                if distance:
                    st.write(f"**Distance:** {distance} km")
                location_query = store.get('location', '').replace(' ', '+')
                maps_url = f"https://www.google.com/maps/search/?api=1&query={location_query}"
                st.markdown(f'<a href="{maps_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #000; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer; margin-top: 0.5rem;">View On Google Maps</button></a>', unsafe_allow_html=True)
    else:
        st.info("No stores registered yet. Retailers and wholesalers need to register with location information.")

def show_nearby_stores_modal():
    """Show a modal/dialog with nearby stores on Google Maps."""
    api_key = get_google_maps_api_key()
    stores = get_store_locations()
    
    # Get user's location and coordinates
    user = None
    user_lat, user_lng = None, None
    
    try:
        from utils.auth import get_current_user
        from utils.geocoding import get_user_coordinates, geocode_user_location
        user = get_current_user()
        
        if user:
            # Try to get user coordinates
            user_lat, user_lng = get_user_coordinates(user)
            
            # If coordinates not found, try to geocode
            if not user_lat or not user_lng:
                location = user.get("location", "")
                if location:
                    geocode_result = geocode_user_location(user, update_user=True)
                    if geocode_result.get("success"):
                        user_lat = geocode_result.get("latitude")
                        user_lng = geocode_result.get("longitude")
    except:
        pass
    
    # Use user coordinates if available, otherwise use default
    if user_lat and user_lng:
        center_lat, center_lng = user_lat, user_lng
        if user and user.get("location"):
            st.info(f"📍 Your location: {user.get('location')}")
            st.caption(f"📍 Map centered at: {center_lat:.4f}°N, {center_lng:.4f}°E")
    else:
        center_lat, center_lng = get_default_coordinates()
        if user and user.get("location"):
            st.info(f"📍 Your location: {user.get('location')} (coordinates being calculated...)")
        st.caption(f"📍 Map centered at: {center_lat}°N, {center_lng}°E")
    
    st.write("View stores near your location on the map below.")
    
    # Get stores with coordinates
    stores_with_coords = []
    for store in stores:
        try:
            from utils.database import get_user_by_id
            from utils.geocoding import get_user_coordinates, geocode_address
            
            seller = get_user_by_id(store.get("user_id"))
            if seller:
                store_lat, store_lng = get_user_coordinates(seller)
                
                # If coordinates not found, try to geocode
                if not store_lat or not store_lng:
                    location = store.get("location", "")
                    if location:
                        store_lat, store_lng, formatted, error = geocode_address(location)
                        if store_lat and store_lng:
                            # Update seller record
                            from utils.database import update_user
                            update_user(seller.get("user_id"), {
                                "latitude": store_lat,
                                "longitude": store_lng
                            })
                
                if store_lat and store_lng:
                    store_copy = store.copy()
                    store_copy["latitude"] = store_lat
                    store_copy["longitude"] = store_lng
                    
                    # Calculate distance from user if user coordinates available
                    if user_lat and user_lng:
                        from utils.geocoding import calculate_distance
                        distance = calculate_distance(user_lat, user_lng, store_lat, store_lng, unit="km")
                        store_copy["distance_km"] = round(distance, 2)
                    
                    stores_with_coords.append(store_copy)
        except Exception:
            # If geocoding fails, include store without coordinates
            stores_with_coords.append(store)
    
    # Sort stores by distance (nearest first)
    if stores_with_coords and user_lat and user_lng:
        from utils.geocoding import calculate_distance
        # Calculate distance for all stores and sort
        for store in stores_with_coords:
            if store.get("latitude") and store.get("longitude"):
                distance = calculate_distance(
                    user_lat, user_lng,
                    store.get("latitude"), store.get("longitude"),
                    unit="km"
                )
                store["distance_km"] = round(distance, 2)
        
        # Sort by distance (nearest first)
        stores_with_coords.sort(key=lambda s: s.get("distance_km", float('inf')))
    
    # Show map
    if stores_with_coords:
        render_google_maps_with_stores(api_key, center_lat, center_lng, stores_with_coords)
    else:
        st.warning("No stores found. Retailers and wholesalers need to register with location information.")
        # Still show the map with center coordinates
        render_google_maps_with_stores(api_key, center_lat, center_lng, [])
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    **Tips:**
    - Click on markers to see store details
    - Use the "View on Google Maps" button to open in full Google Maps
    - Stores are shown based on registered retailers and wholesalers
    - Distance shown if your location is geocoded
    """)

