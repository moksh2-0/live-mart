"""
Product Aggregation and Stock Management
Handles grouping products by product_id and calculating aggregated stock levels
"""
from typing import Dict, List, Any, Optional, Tuple
from utils.database import get_products, get_user_by_id
from utils.geocoding import get_user_coordinates, calculate_distance

def get_product_stock_info(product_id: str) -> Dict[str, Any]:
    """
    Get aggregated stock information for a product across all retailers and wholesalers.
    
    Returns:
        {
            "product_id": str,
            "product_name": str,
            "category": str,
            "retailer_stock": int,  # Sum of stock across all retailers
            "wholesaler_stock": int,  # Sum of stock across all wholesalers
            "retailer_products": List[Dict],  # List of retailer product entries
            "wholesaler_products": List[Dict],  # List of wholesaler product entries
            "has_retailer_stock": bool,
            "has_wholesaler_stock": bool
        }
    """
    all_products = get_products()
    
    # Find all product entries with this product_id
    product_entries = [p for p in all_products if p.get("product_id") == product_id]
    
    if not product_entries:
        return {
            "product_id": product_id,
            "product_name": "Unknown Product",
            "category": "",
            "retailer_stock": 0,
            "wholesaler_stock": 0,
            "retailer_products": [],
            "wholesaler_products": [],
            "has_retailer_stock": False,
            "has_wholesaler_stock": False
        }
    
    # Use first product as base (they should all have same name, category, etc.)
    base_product = product_entries[0]
    
    # Separate retailer and wholesaler products
    retailer_products = [p for p in product_entries if p.get("seller_type", "").lower() == "retailer"]
    wholesaler_products = [p for p in product_entries if p.get("seller_type", "").lower() == "wholesaler"]
    
    # Calculate aggregated stock
    retailer_stock = sum(p.get("stock", 0) for p in retailer_products)
    wholesaler_stock = sum(p.get("stock", 0) for p in wholesaler_products)
    
    return {
        "product_id": product_id,
        "product_name": base_product.get("name", "Unknown Product"),
        "category": base_product.get("category", ""),
        "description": base_product.get("description", ""),
        "price": base_product.get("price", 0),
        "image_url": base_product.get("image_url", ""),
        "retailer_stock": retailer_stock,
        "wholesaler_stock": wholesaler_stock,
        "retailer_products": retailer_products,
        "wholesaler_products": wholesaler_products,
        "has_retailer_stock": retailer_stock > 0,
        "has_wholesaler_stock": wholesaler_stock > 0
    }

def get_aggregated_products() -> List[Dict[str, Any]]:
    """
    Get all products aggregated by product_id.
    Each product appears once with aggregated stock information.
    
    Returns:
        List of aggregated product dictionaries
    """
    all_products = get_products()
    
    # Group products by product_id
    product_groups: Dict[str, List[Dict]] = {}
    for product in all_products:
        product_id = product.get("product_id")
        if product_id:
            if product_id not in product_groups:
                product_groups[product_id] = []
            product_groups[product_id].append(product)
    
    # Create aggregated products
    aggregated = []
    for product_id, products in product_groups.items():
        stock_info = get_product_stock_info(product_id)
        aggregated.append(stock_info)
    
    return aggregated

def find_nearest_retailer_with_stock(
    product_id: str,
    required_quantity: int,
    customer_lat: float,
    customer_lng: float
) -> Optional[Tuple[Dict[str, Any], float]]:
    """
    Find the nearest retailer who has sufficient stock for a product.
    
    Args:
        product_id: Product ID to find
        required_quantity: Quantity needed
        customer_lat: Customer latitude
        customer_lng: Customer longitude
    
    Returns:
        Tuple of (retailer_product_dict, distance_km) or None if no retailer has stock
    """
    stock_info = get_product_stock_info(product_id)
    retailer_products = stock_info.get("retailer_products", [])
    
    # Filter retailers with sufficient stock
    available_retailers = [
        p for p in retailer_products 
        if p.get("stock", 0) >= required_quantity
    ]
    
    if not available_retailers:
        return None
    
    # If only one retailer, return it
    if len(available_retailers) == 1:
        retailer_product = available_retailers[0]
        seller_id = retailer_product.get("seller_id")
        seller = get_user_by_id(seller_id) if seller_id else None
        
        if seller:
            seller_lat, seller_lng = get_user_coordinates(seller)
            if seller_lat and seller_lng:
                distance = calculate_distance(customer_lat, customer_lng, seller_lat, seller_lng, unit="km")
                return (retailer_product, distance)
        return (retailer_product, 0)  # Return with 0 distance if coordinates unavailable
    
    # Multiple retailers - find nearest
    retailers_with_distance = []
    for retailer_product in available_retailers:
        seller_id = retailer_product.get("seller_id")
        seller = get_user_by_id(seller_id) if seller_id else None
        
        if seller:
            seller_lat, seller_lng = get_user_coordinates(seller)
            if seller_lat and seller_lng:
                distance = calculate_distance(customer_lat, customer_lng, seller_lat, seller_lng, unit="km")
                retailers_with_distance.append((retailer_product, distance))
    
    if not retailers_with_distance:
        # No coordinates available, return first retailer
        return (available_retailers[0], 0)
    
    # Sort by distance and return nearest
    retailers_with_distance.sort(key=lambda x: x[1])
    return retailers_with_distance[0]

def is_product_only_listed_by_wholesaler(product_id: str) -> bool:
    """
    Check if a product is only listed by wholesaler(s) and not by any retailer.
    
    Args:
        product_id: Product ID to check
    
    Returns:
        True if product exists only at wholesaler level, False otherwise
    """
    stock_info = get_product_stock_info(product_id)
    return stock_info.get("has_wholesaler_stock") and not stock_info.get("has_retailer_stock")

