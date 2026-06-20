from typing import List, Dict, Any
from utils.database import get_products

def filter_by_category(products: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """Filter products by category."""
    if category == "All" or not category:
        return products
    return [p for p in products if p.get("category", "").lower() == category.lower()]

def filter_by_price_range(products: List[Dict[str, Any]], min_price: float, max_price: float) -> List[Dict[str, Any]]:
    """Filter products by price range."""
    return [p for p in products if min_price <= p.get("price", 0) <= max_price]

def filter_by_stock(products: List[Dict[str, Any]], in_stock_only: bool = True) -> List[Dict[str, Any]]:
    """Filter products by stock availability."""
    if not in_stock_only:
        return products
    return [p for p in products if p.get("stock", 0) > 0]

def filter_by_seller_type(products: List[Dict[str, Any]], seller_type: str) -> List[Dict[str, Any]]:
    """Filter products by seller type (retailer/wholesaler)."""
    if seller_type == "All" or not seller_type:
        return products
    return [p for p in products if p.get("seller_type", "").lower() == seller_type.lower()]

def search_products(query: str, products: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search products by name or description."""
    if products is None:
        products = get_products()
    
    if not query:
        return products
    
    query_lower = query.lower()
    results = []
    
    for product in products:
        name = product.get("name", "").lower()
        description = product.get("description", "").lower()
        category = product.get("category", "").lower()
        
        if query_lower in name or query_lower in description or query_lower in category:
            results.append(product)
    
    return results

def filter_by_location(products: List[Dict[str, Any]], user_location: str, seller_locations: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """Filter products by seller location (basic implementation)."""
    if not user_location or not seller_locations:
        return products
    
    # Basic location matching (can be enhanced with Google Maps API)
    user_location_lower = user_location.lower()
    filtered = []
    
    for product in products:
        seller_id = product.get("seller_id")
        seller_location = seller_locations.get(seller_id, "").lower()
        
        # Simple matching - check if locations share common words
        if user_location_lower in seller_location or seller_location in user_location_lower:
            filtered.append(product)
    
    return filtered

def apply_all_filters(
    products: List[Dict[str, Any]],
    category: str = "All",
    min_price: float = 0.0,
    max_price: float = float('inf'),
    in_stock_only: bool = True,
    seller_type: str = "All",
    search_query: str = ""
) -> List[Dict[str, Any]]:
    """Apply all filters to a product list."""
    filtered = products
    
    # Apply search first
    if search_query:
        filtered = search_products(search_query, filtered)
    
    # Apply category filter
    filtered = filter_by_category(filtered, category)
    
    # Apply price filter
    filtered = filter_by_price_range(filtered, min_price, max_price)
    
    # Apply stock filter
    filtered = filter_by_stock(filtered, in_stock_only)
    
    # Seller type filter removed - no longer filtering by seller type
    
    return filtered

