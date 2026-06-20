from utils.database import save_order, get_orders, update_order, get_product_by_id, update_product, get_order_by_id, get_user_by_id, get_products, get_users
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

def calculate_delivery_days_from_distance(distance_km: float) -> int:
    """
    Calculate delivery days based on distance from customer to seller.
    
    Delivery time logic (updated to 1-5 days range):
    - 0-50 km: 1-2 days (fast delivery)
    - 50-150 km: 2-3 days (medium delivery)
    - 150-300 km: 3-4 days (long distance)
    - 300+ km: 4-5 days (very long distance)
    
    Args:
        distance_km: Distance in kilometers
    
    Returns:
        Number of days for delivery (1-5 days)
    """
    if distance_km <= 50:
        # Local/close delivery: 1-2 days
        base_days = 1
        # Add 1 day if distance > 25 km
        additional_days = 1 if distance_km > 25 else 0
        return base_days + additional_days
    elif distance_km <= 150:
        # Medium distance: 2-3 days
        base_days = 2
        # Add 1 day if distance > 100 km
        additional_days = 1 if distance_km > 100 else 0
        return base_days + additional_days
    elif distance_km <= 300:
        # Long distance: 3-4 days
        base_days = 3
        # Add 1 day if distance > 225 km
        additional_days = 1 if distance_km > 225 else 0
        return base_days + additional_days
    else:
        # Very long distance: 4-5 days
        base_days = 4
        # Add 1 day if distance > 400 km
        additional_days = 1 if distance_km > 400 else 0
        return min(5, base_days + additional_days)  # Cap at 5 days

def check_wholesaler_delay_needed(product_id: str, retailer_id: str = None) -> Tuple[bool, int]:
    """
    Check if order needs wholesaler delay (retailer stock = 0 but wholesaler has stock).
    
    Args:
        product_id: Product ID to check
        retailer_id: ID of retailer assigned to order (optional)
    
    Returns:
        Tuple of (needs_delay: bool, wholesaler_stock: int)
    """
    from utils.product_aggregation import get_product_stock_info
    
    stock_info = get_product_stock_info(product_id)
    retailer_stock = stock_info.get("retailer_stock", 0)
    wholesaler_stock = stock_info.get("wholesaler_stock", 0)
    
    # If specific retailer is assigned, check their stock
    if retailer_id:
        retailer_products = stock_info.get("retailer_products", [])
        retailer_product = None
        for p in retailer_products:
            if p.get("seller_id") == retailer_id:
                retailer_product = p
                break
        
        if retailer_product:
            retailer_stock_for_assigned = retailer_product.get("stock", 0)
            # If assigned retailer has stock, no delay needed
            if retailer_stock_for_assigned > 0:
                return False, wholesaler_stock
            # If assigned retailer stock = 0 but wholesaler has stock, delay needed
            elif retailer_stock_for_assigned == 0 and wholesaler_stock > 0:
                return True, wholesaler_stock
    
    # General check: if retailer stock is 0 (aggregated) but wholesaler has stock, delay needed
    if retailer_stock == 0 and wholesaler_stock > 0:
        return True, wholesaler_stock
    
    return False, wholesaler_stock

def calculate_distance_based_delivery_time(
    customer_id: str,
    items: List[Dict[str, Any]],
    assigned_retailer_id: str = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Calculate delivery time based on distance and product availability.
    
    Args:
        customer_id: Customer user ID
        items: List of order items (products in cart)
    
    Returns:
        Tuple of (total_delivery_days, delivery_breakdown_dict)
        delivery_breakdown contains details about each product's delivery time
    """
    from utils.database import get_user_by_id
    from utils.geocoding import get_user_coordinates, calculate_distance
    
    customer = get_user_by_id(customer_id)
    if not customer:
        # Fallback to default if customer not found
        return 5, {"error": "Customer not found", "default_days": 5}
    
    # Get customer coordinates
    customer_lat, customer_lng = get_user_coordinates(customer)
    if not customer_lat or not customer_lng:
        # Fallback to default if coordinates not available
        return 5, {"error": "Customer location not available", "default_days": 5}
    
    max_delivery_days = 0
    delivery_breakdown = {
        "products": [],
        "has_wholesaler_delay": False,
        "total_days": 0
    }
    
    # Calculate delivery time for each product
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)
        
        # Get stock information
        from utils.product_aggregation import get_product_stock_info
        stock_info = get_product_stock_info(product_id)
        retailer_products = stock_info.get("retailer_products", [])
        wholesaler_stock = stock_info.get("wholesaler_stock", 0)
        
        # Find nearest retailer for this product (or use assigned retailer)
        retailer_product = None
        distance = None
        
        if assigned_retailer_id:
            # Use assigned retailer
            for rp in retailer_products:
                if rp.get("seller_id") == assigned_retailer_id:
                    retailer_product = rp
                    break
            
            if retailer_product:
                retailer = get_user_by_id(assigned_retailer_id)
                if retailer:
                    seller_lat, seller_lng = get_user_coordinates(retailer)
                    if seller_lat and seller_lng:
                        distance = calculate_distance(customer_lat, customer_lng, seller_lat, seller_lng, unit="km")
        else:
            # Find nearest retailer with stock (fallback)
            from utils.product_aggregation import find_nearest_retailer_with_stock
            result = find_nearest_retailer_with_stock(product_id, quantity, customer_lat, customer_lng)
            if result:
                retailer_product, distance = result
        
        delivery_info = {
            "product_id": product_id,
            "product_name": stock_info.get("product_name", "Unknown"),
            "distance_km": round(distance, 2) if distance else None,
            "base_delivery_days": 0,
            "wholesaler_delay_days": 0,
            "total_delivery_days": 0
        }
        
        if distance:
            # Calculate base delivery days from distance
            base_days = calculate_delivery_days_from_distance(distance)
            delivery_info["base_delivery_days"] = base_days
        else:
            # Default distance-based delivery (max 5 days)
            base_days = 5
            delivery_info["base_delivery_days"] = base_days
        
        # Check if wholesaler delay is needed
        # If assigned retailer has stock = 0 but wholesaler has stock, add 2 days
        retailer_stock_for_product = 0
        if retailer_product:
            retailer_stock_for_product = retailer_product.get("stock", 0)
        
        wholesaler_delay = 0
        if retailer_stock_for_product == 0 and wholesaler_stock > 0:
            # Retailer stock is 0 but wholesaler has stock - add delay
            wholesaler_delay = 2
            delivery_info["wholesaler_delay_days"] = wholesaler_delay
            delivery_breakdown["has_wholesaler_delay"] = True
        
        # Total delivery days for this product
        total_days = base_days + wholesaler_delay
        delivery_info["total_delivery_days"] = total_days
        
        # Track maximum delivery time (worst case)
        max_delivery_days = max(max_delivery_days, total_days)
        
        delivery_breakdown["products"].append(delivery_info)
    
    delivery_breakdown["total_days"] = max_delivery_days
    return max_delivery_days, delivery_breakdown

def calculate_estimated_delivery_date(days: int = 5) -> str:
    """Calculate estimated delivery date (default 5 days from now)."""
    estimated_date = datetime.now() + timedelta(days=days)
    return estimated_date.strftime("%Y-%m-%d")

def find_nearest_retailer_by_location(customer_id: str) -> Optional[str]:
    """
    Find the nearest retailer by location when no retailer has the product in inventory.
    Used as a fallback when a product is only at wholesaler level (no retailer has bought it).
    
    Args:
        customer_id: Customer user ID
    
    Returns:
        Nearest retailer ID by location, or None if no retailers found
    """
    from utils.geocoding import get_user_coordinates, calculate_distance
    
    customer = get_user_by_id(customer_id)
    if not customer:
        return None
    
    customer_lat, customer_lng = get_user_coordinates(customer)
    if not customer_lat or not customer_lng:
        return None
    
    # Get all retailers
    all_users = get_users()
    retailers = [u for u in all_users if u.get("role", "").lower() == "retailer"]
    
    if not retailers:
        return None
    
    # Find nearest retailer by location
    nearest_retailer = None
    min_distance = float('inf')
    
    for retailer in retailers:
        retailer_lat, retailer_lng = get_user_coordinates(retailer)
        if retailer_lat and retailer_lng:
            distance = calculate_distance(customer_lat, customer_lng, retailer_lat, retailer_lng, unit="km")
            if distance < min_distance:
                min_distance = distance
                nearest_retailer = retailer.get("user_id")
    
    # If no retailer with coordinates, return first retailer
    if not nearest_retailer and retailers:
        nearest_retailer = retailers[0].get("user_id")
    
    return nearest_retailer

def assign_order_to_retailer(customer_id: str, items: List[Dict[str, Any]]) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Assign order to nearest retailer with sufficient stock.
    
    Args:
        customer_id: Customer user ID
        items: List of order items
    
    Returns:
        Tuple of (assigned_retailer_id, assignment_details)
        assignment_details contains info about which retailer is assigned for each product
        Returns (None, {}) if no retailer has stock - fallback to location-based assignment in create_order()
    """
    from utils.product_aggregation import find_nearest_retailer_with_stock
    from utils.geocoding import get_user_coordinates
    
    customer = get_user_by_id(customer_id)
    if not customer:
        return None, {}
    
    customer_lat, customer_lng = get_user_coordinates(customer)
    if not customer_lat or not customer_lng:
        return None, {}
    
    # Group products by retailer to find the best retailer
    retailer_assignments = {}  # retailer_id -> list of (product_id, quantity, distance)
    
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)
        
        # Find nearest retailer with stock for this product
        result = find_nearest_retailer_with_stock(
            product_id, 
            quantity, 
            customer_lat, 
            customer_lng
        )
        
        if result:
            retailer_product, distance = result
            retailer_id = retailer_product.get("seller_id")
            
            if retailer_id not in retailer_assignments:
                retailer_assignments[retailer_id] = {
                    "products": [],
                    "total_distance": 0,
                    "count": 0
                }
            
            retailer_assignments[retailer_id]["products"].append({
                "product_id": product_id,
                "quantity": quantity,
                "distance": distance
            })
            retailer_assignments[retailer_id]["total_distance"] += distance
            retailer_assignments[retailer_id]["count"] += 1
    
    if not retailer_assignments:
        return None, {}
    
    # If only one retailer, assign to that one
    if len(retailer_assignments) == 1:
        retailer_id = list(retailer_assignments.keys())[0]
        return retailer_id, {
            "retailer_id": retailer_id,
            "assignment_method": "single_retailer",
            "products": retailer_assignments[retailer_id]["products"]
        }
    
    # Multiple retailers - find the best one (nearest average distance)
    best_retailer = None
    best_avg_distance = float('inf')
    
    for retailer_id, data in retailer_assignments.items():
        avg_distance = data["total_distance"] / data["count"]
        if avg_distance < best_avg_distance:
            best_avg_distance = avg_distance
            best_retailer = retailer_id
    
    return best_retailer, {
        "retailer_id": best_retailer,
        "assignment_method": "nearest_retailer",
        "average_distance": best_avg_distance,
        "products": retailer_assignments[best_retailer]["products"]
    }

def create_order(customer_id: str, items: List[Dict[str, Any]], payment_method: str = "online") -> bool:
    """
    Create a new order from cart items with distance-based delivery time calculation.
    Assigns order to nearest retailer with sufficient stock.
    Customer orders from retailer only (never directly from wholesaler).
    """
    if not items:
        return False
    
    # Calculate total
    total_amount = sum(item.get("price", 0) * item.get("quantity", 0) for item in items)
    
    # Assign order to nearest retailer with sufficient stock
    assigned_retailer_id, assignment_details = assign_order_to_retailer(customer_id, items)
    
    # If no retailer available (no retailer has the product in inventory), 
    # fallback to nearest retailer by location
    if not assigned_retailer_id:
        assigned_retailer_id = find_nearest_retailer_by_location(customer_id)
    
    # Calculate estimated delivery date based on distance and product availability
    # Pass assigned retailer to check their specific stock levels
    delivery_days, delivery_breakdown = calculate_distance_based_delivery_time(
        customer_id, 
        items, 
        assigned_retailer_id=assigned_retailer_id
    )
    estimated_delivery = calculate_estimated_delivery_date(days=delivery_days)
    
    # Prepare order items
    order_items = []
    for item in items:
        order_items.append({
            "product_id": item.get("product_id"),
            "quantity": item.get("quantity"),
            "price": item.get("price")
        })
    
    order_data = {
        "customer_id": customer_id,
        "seller_id": assigned_retailer_id,  # Assign to retailer
        "items": order_items,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "payment_status": "pending" if payment_method == "online" else "pending",
        "status": "pending",
        "order_type": "customer_to_retailer",  # Mark as customer order
        "estimated_delivery_date": estimated_delivery,
        "estimated_delivery_days": delivery_days,
        "delivery_breakdown": delivery_breakdown,  # Store breakdown for display
        "retailer_assignment": assignment_details,  # Store assignment details
        "wholesaler_order_id": None,  # Will be set when retailer orders from wholesaler
        "needs_wholesaler_order": False  # Will be set if retailer stock is 0
    }
    
    # Check if any items need wholesaler order (retailer stock = 0 but wholesaler has stock)
    from utils.product_aggregation import get_product_stock_info
    needs_wholesaler = False
    
    for item in items:
        product_id = item.get("product_id")
        stock_info = get_product_stock_info(product_id)
        retailer_stock = stock_info.get("retailer_stock", 0)
        wholesaler_stock = stock_info.get("wholesaler_stock", 0)
        
        # Check assigned retailer's specific stock
        if assigned_retailer_id:
            retailer_products = stock_info.get("retailer_products", [])
            for rp in retailer_products:
                if rp.get("seller_id") == assigned_retailer_id:
                    retailer_stock = rp.get("stock", 0)
                    break
        
        if retailer_stock == 0 and wholesaler_stock > 0:
            needs_wholesaler = True
            break
    
    order_data["needs_wholesaler_order"] = needs_wholesaler
    
    return save_order(order_data)

def create_retailer_order(retailer_id: str, product_id: str, quantity: int, price: float) -> bool:
    """Create an order from retailer to wholesaler."""
    product = get_product_by_id(product_id)
    if not product:
        return False
    
    order_data = {
        "customer_id": retailer_id,  # Retailer is the customer in this case
        "items": [{
            "product_id": product_id,
            "quantity": quantity,
            "price": price
        }],
        "total_amount": price * quantity,
        "payment_method": "offline",
        "payment_status": "pending",
        "status": "pending"
    }
    
    return save_order(order_data)

def update_order_status(order_id: str, new_status: str) -> bool:
    """Update the status of an order with real-time notifications."""
    order = get_order_by_id(order_id)
    if not order:
        return False
    
    # Update order status
    success = update_order(order_id, {
        "status": new_status,
        "status_updated_at": datetime.now().isoformat()
    })
    
    if success:
        # Send real-time status update notification
        customer_id = order.get("customer_id")
        if customer_id:
            from utils.database import get_user_by_id
            from utils.feedback import send_order_status_update
            
            customer = get_user_by_id(customer_id)
            if customer:
                customer_email = customer.get("email", "")
                customer_name = customer.get("name", "Customer")
                
                # Send notification
                send_order_status_update(customer_email, customer_name, order_id, new_status)
                
                # If status is delivered, send delivery confirmation
                if new_status == "delivered":
                    from utils.feedback import send_delivery_confirmation_email, send_delivery_confirmation_sms
                    
                    # Update delivery date first
                    delivery_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    update_order(order_id, {"delivery_date": delivery_date})
                    
                    # Fetch updated order with delivery date
                    updated_order = get_order_by_id(order_id)
                    if updated_order:
                        # Send delivery confirmation email with updated order data
                        send_delivery_confirmation_email(order_id, customer_email, customer_name)
                        
                        # Send SMS if phone number available
                        customer_phone = customer.get("phone", "")
                        if customer_phone:
                            send_delivery_confirmation_sms(customer_phone, order_id)
    
    return success

def process_order_payment(order_id: str) -> bool:
    """Mark an order as paid."""
    return update_order(order_id, {"payment_status": "completed"})

def update_stock_after_order(order_id: str) -> bool:
    """Update product stock after order is confirmed."""
    orders = get_orders()
    order = None
    for o in orders:
        if o.get("order_id") == order_id:
            order = o
            break
    
    if not order or order.get("status") != "confirmed":
        return False
    
    # Update stock for each item
    for item in order.get("items", []):
        product = get_product_by_id(item.get("product_id"))
        if product:
            current_stock = product.get("stock", 0)
            quantity = item.get("quantity", 0)
            new_stock = max(0, current_stock - quantity)
            update_product(item.get("product_id"), {"stock": new_stock})
    
    return True

def get_order_status_display(status: str) -> str:
    """Get a user-friendly status display."""
    status_map = {
        "pending": "⏳ Pending",
        "confirmed": "✅ Confirmed",
        "processing": "🔄 Processing",
        "shipped": "🚚 Shipped",
        "delivered": "📦 Delivered",
        "cancelled": "❌ Cancelled"
    }
    return status_map.get(status.lower(), status.title())

def get_payment_status_display(status: str) -> str:
    """Get a user-friendly payment status display."""
    status_map = {
        "pending": "⏳ Pending",
        "completed": "✅ Paid",
        "failed": "❌ Failed",
        "refunded": "↩️ Refunded"
    }
    return status_map.get(status.lower(), status.title())

