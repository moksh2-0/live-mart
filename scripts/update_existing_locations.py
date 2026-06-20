"""
Utility script to update locations for existing users
Run this to fix locations for accounts created before proper validation
"""
from utils.database import get_users, update_user
from utils.geocoding import geocode_user_location

def update_all_user_locations():
    """Update and geocode locations for all users."""
    users = get_users()
    
    print(f"Found {len(users)} users to check...")
    print("-" * 60)
    
    updated_count = 0
    failed_count = 0
    
    for user in users:
        user_id = user.get("user_id")
        name = user.get("name", "Unknown")
        current_location = user.get("location", "")
        email = user.get("email", "")
        
        print(f"\nUser: {name} ({email})")
        print(f"   Current Location: {current_location}")
        
        # Check if location needs fixing
        if not current_location or current_location == "Unknown":
            print(f"   [WARNING] Location is empty or 'Unknown' - skipping")
            continue
        
        # Check if location has proper format (comma)
        if ',' not in current_location:
            print(f"   [WARNING] Location format invalid (no comma) - trying to fix...")
            
            # Try to fix common locations automatically
            location_fixed = None
            location_lower = current_location.lower().strip()
            
            # Common location fixes
            location_map = {
                "hyderabad": "Hyderabad, Telangana, India",
                "hyderbad": "Hyderabad, Telangana, India",  # Fix typo
                "muzaffarnagar": "Muzaffarnagar, Uttar Pradesh, India",
                "delhi": "Delhi, Delhi, India",
                "mumbai": "Mumbai, Maharashtra, India",
                "bangalore": "Bangalore, Karnataka, India",
                "chennai": "Chennai, Tamil Nadu, India",
                "kolkata": "Kolkata, West Bengal, India",
                "shamipet": "Shamipet, Telangana, India",
            }
            
            if location_lower in location_map:
                location_fixed = location_map[location_lower]
                print(f"   [FIX] Auto-correcting to: {location_fixed}")
                # Update location first
                update_user(user_id, {"location": location_fixed})
                user["location"] = location_fixed
                current_location = location_fixed
            else:
                print(f"   [SKIP] Cannot auto-fix - please update manually in dashboard")
                print(f"   [TIP] Use format: City, State, Country")
                continue
        
        # Check if already geocoded
        if user.get("latitude") and user.get("longitude"):
            print(f"   [OK] Already geocoded - skipping")
            continue
        
        # Try to geocode
        try:
            geocode_result = geocode_user_location(user, update_user=True)
            
            if geocode_result.get("success"):
                formatted = geocode_result.get('formatted_address', current_location)
                print(f"   [SUCCESS] Successfully geocoded: {formatted}")
                updated_count += 1
            else:
                error = geocode_result.get('error', 'Unknown error')
                print(f"   [FAILED] Geocoding failed: {error}")
                if "not found" in error.lower() or "ZERO_RESULTS" in error:
                    print(f"   [TIP] Location not found by Google Maps - update with more specific format")
                failed_count += 1
        except Exception as e:
            print(f"   [ERROR] {str(e)}")
            failed_count += 1
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"   Successfully geocoded: {updated_count}")
    print(f"   Failed or skipped: {failed_count}")
    print(f"   Total checked: {len(users)}")
    print("\n[TIP] Users with invalid formats need manual update in dashboard")

if __name__ == "__main__":
    print("Updating locations for existing users...")
    print("=" * 60)
    update_all_user_locations()

