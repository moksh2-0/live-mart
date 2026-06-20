"""
Geocoding and Location Services
Converts addresses to coordinates and calculates distances
"""
import os
import requests
import streamlit as st
from typing import Optional, Tuple, Dict, Any
import math

def get_geocoding_api_key() -> Optional[str]:
    """Get Google Maps Geocoding API key from config or environment."""
    # Try config file
    try:
        from config_maps import GOOGLE_MAPS_API_KEY
        if GOOGLE_MAPS_API_KEY:
            return GOOGLE_MAPS_API_KEY
    except ImportError:
        pass
    
    # Try Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'google_maps' in st.secrets:
            return st.secrets.google_maps.api_key
    except:
        pass
    
    # Try environment variable
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if api_key:
        return api_key
    
    return None

def geocode_address(address: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
    """
    Convert an address to latitude and longitude coordinates using Google Geocoding API.
    
    Args:
        address: Address string (e.g., "Hyderabad, India")
    
    Returns:
        (latitude, longitude, formatted_address, error_message)
        Returns (None, None, None, error) if geocoding fails
    """
    api_key = get_geocoding_api_key()
    
    if not api_key:
        # Fallback: Try to use browser geolocation or return None
        return None, None, None, "Google Maps API key not configured"
    
    try:
        # Google Geocoding API endpoint
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        status = data.get("status")
        
        if status == "OK" and data.get("results"):
            result = data["results"][0]
            location = result["geometry"]["location"]
            latitude = location["lat"]
            longitude = location["lng"]
            formatted_address = result.get("formatted_address", address)
            
            return latitude, longitude, formatted_address, None
        elif status == "ZERO_RESULTS":
            return None, None, None, f"Location '{address}' not found. Please try a more specific address (e.g., 'Hyderabad, India' or 'New Delhi, Delhi, India')"
        elif status == "INVALID_REQUEST":
            return None, None, None, f"Invalid location format. Please provide a valid address like 'City, State, Country'"
        elif status == "OVER_QUERY_LIMIT":
            return None, None, None, "API quota exceeded. Please try again later."
        elif status == "REQUEST_DENIED":
            error_msg = data.get("error_message", "Geocoding API request denied. Check your API key permissions.")
            return None, None, None, error_msg
        else:
            error_msg = data.get("error_message", f"Geocoding failed: {status}")
            return None, None, None, error_msg
    
    except requests.exceptions.RequestException as e:
        return None, None, None, f"Network error: {str(e)}"
    except Exception as e:
        return None, None, None, f"Geocoding error: {str(e)}"

def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Convert coordinates to an address using Google Reverse Geocoding API.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Formatted address string or None if reverse geocoding fails
    """
    api_key = get_geocoding_api_key()
    
    if not api_key:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{latitude},{longitude}",
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0].get("formatted_address")
        
        return None
    
    except Exception:
        return None

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "km") -> float:
    """
    Calculate the distance between two coordinates using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        unit: Distance unit ("km" or "mi")
    
    Returns:
        Distance in specified unit
    """
    # Radius of the Earth in km
    R = 6371.0 if unit == "km" else 3959.0  # Earth radius in miles if unit is "mi"
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distance
    distance = R * c
    
    return distance

def get_user_coordinates(user: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """
    Get coordinates for a user. First checks if stored, otherwise geocodes the address.
    
    Args:
        user: User dictionary with location information
    
    Returns:
        (latitude, longitude) or (None, None) if not available
    """
    # Check if coordinates are already stored
    if "latitude" in user and "longitude" in user:
        if user.get("latitude") and user.get("longitude"):
            return float(user["latitude"]), float(user["longitude"])
    
    # Try to geocode the location
    location = user.get("location", "")
    if location:
        lat, lng, formatted_address, error = geocode_address(location)
        if lat and lng:
            # Optionally update the user record with coordinates (can be done asynchronously)
            return lat, lng
    
    return None, None

def geocode_user_location(user: Dict[str, Any], update_user: bool = False) -> Dict[str, Any]:
    """
    Geocode a user's location and optionally update the user record.
    
    Args:
        user: User dictionary
        update_user: Whether to update the user record with geocoded coordinates
    
    Returns:
        Dictionary with geocoding results:
        {
            "success": bool,
            "latitude": float or None,
            "longitude": float or None,
            "formatted_address": str or None,
            "error": str or None
        }
    """
    location = user.get("location", "")
    
    if not location:
        return {
            "success": False,
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "error": "No location provided"
        }
    
    lat, lng, formatted_address, error = geocode_address(location)
    
    if lat and lng:
        result = {
            "success": True,
            "latitude": lat,
            "longitude": lng,
            "formatted_address": formatted_address,
            "error": None
        }
        
        # Update user record if requested
        if update_user:
            from utils.database import update_user
            update_user(user.get("user_id"), {
                "latitude": lat,
                "longitude": lng,
                "formatted_address": formatted_address or location
            })
        
        return result
    else:
        return {
            "success": False,
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "error": error or "Geocoding failed"
        }

def filter_by_distance(
    items: list,
    center_lat: float,
    center_lng: float,
    max_distance_km: float,
    get_coordinates_func: callable
) -> list:
    """
    Filter items by distance from a center point.
    
    Args:
        items: List of items to filter
        center_lat: Center latitude
        center_lng: Center longitude
        max_distance_km: Maximum distance in kilometers
        get_coordinates_func: Function that takes an item and returns (lat, lng)
    
    Returns:
        Filtered list of items within max_distance_km
    """
    filtered = []
    
    for item in items:
        lat, lng = get_coordinates_func(item)
        if lat and lng:
            distance = calculate_distance(center_lat, center_lng, lat, lng, unit="km")
            if distance <= max_distance_km:
                item_with_distance = item.copy() if isinstance(item, dict) else item
                if isinstance(item_with_distance, dict):
                    item_with_distance["_distance_km"] = round(distance, 2)
                filtered.append(item_with_distance)
    
    return filtered

def sort_by_distance(
    items: list,
    center_lat: float,
    center_lng: float,
    get_coordinates_func: callable
) -> list:
    """
    Sort items by distance from a center point.
    
    Args:
        items: List of items to sort
        center_lat: Center latitude
        center_lng: Center longitude
        get_coordinates_func: Function that takes an item and returns (lat, lng)
    
    Returns:
        Sorted list of items (nearest first)
    """
    items_with_distance = []
    
    for item in items:
        lat, lng = get_coordinates_func(item)
        if lat and lng:
            distance = calculate_distance(center_lat, center_lng, lat, lng, unit="km")
            item_with_distance = {
                "item": item,
                "distance": distance
            }
            items_with_distance.append(item_with_distance)
    
    # Sort by distance
    items_with_distance.sort(key=lambda x: x["distance"])
    
    # Return items with distance info
    result = []
    for entry in items_with_distance:
        item = entry["item"].copy() if isinstance(entry["item"], dict) else entry["item"]
        if isinstance(item, dict):
            item["_distance_km"] = round(entry["distance"], 2)
        result.append(item)
    
    return result

