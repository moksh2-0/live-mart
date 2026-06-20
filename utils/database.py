import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Base directory for data files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def get_file_path(filename: str) -> str:
    """Get the full path to a data file."""
    return os.path.join(DATA_DIR, filename)

def read_json(filename: str) -> Dict[str, Any]:
    """Read data from a JSON file."""
    filepath = get_file_path(filename)
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def write_json(filename: str, data: Dict[str, Any]) -> bool:
    """Write data to a JSON file."""
    filepath = get_file_path(filename)
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False

# User operations
def get_users() -> List[Dict[str, Any]]:
    """Get all users."""
    data = read_json("users.json")
    return data.get("users", [])

def save_user(user: Dict[str, Any]) -> bool:
    """Save a new user."""
    data = read_json("users.json")
    if "users" not in data:
        data["users"] = []
    
    # Check if user already exists
    existing_users = data["users"]
    if any(u.get("email") == user.get("email") for u in existing_users):
        return False
    
    # Add user_id and timestamp if not present
    if "user_id" not in user:
        user["user_id"] = str(uuid.uuid4())
    if "created_at" not in user:
        user["created_at"] = datetime.now().isoformat()
    
    data["users"].append(user)
    return write_json("users.json", data)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email."""
    users = get_users()
    for user in users:
        if user.get("email") == email:
            return user
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by user_id."""
    users = get_users()
    for user in users:
        if user.get("user_id") == user_id:
            return user
    return None

def update_user(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update a user's information."""
    data = read_json("users.json")
    users = data.get("users", [])
    
    for i, user in enumerate(users):
        if user.get("user_id") == user_id:
            users[i].update(updates)
            users[i]["updated_at"] = datetime.now().isoformat()
            return write_json("users.json", data)
    return False

# Product operations
def get_products() -> List[Dict[str, Any]]:
    """Get all products."""
    data = read_json("products.json")
    return data.get("products", [])

def save_product(product: Dict[str, Any]) -> bool:
    """Save a new product."""
    data = read_json("products.json")
    if "products" not in data:
        data["products"] = []
    
    # Add product_id if not present
    if "product_id" not in product:
        product["product_id"] = str(uuid.uuid4())
    
    data["products"].append(product)
    success = write_json("products.json", data)
    
    # If product is added by wholesaler, check if it needs to notify retailers
    if success and product.get("seller_type", "").lower() == "wholesaler":
        try:
            from utils.retailer_notifications import send_new_product_notification_to_all_retailers
            product_id = product.get("product_id")
            product_name = product.get("name", "")
            category = product.get("category", "")
            price = product.get("price", 0)
            
            # Check if this product is only listed by wholesaler (not by any retailer)
            from utils.product_aggregation import is_product_only_listed_by_wholesaler
            if is_product_only_listed_by_wholesaler(product_id):
                # Notify all retailers
                send_new_product_notification_to_all_retailers(product_id, product_name, category, price)
        except Exception as e:
            # Don't fail product save if notification fails
            print(f"Warning: Failed to send retailer notifications: {e}")
    
    return success

def notify_retailers_of_new_wholesaler_product(product_id: str, product_name: str, category: str, price: float) -> Dict[str, Any]:
    """
    Notify all retailers when a new product is only listed by wholesaler.
    This is called automatically when a wholesaler adds a product.
    """
    try:
        from utils.retailer_notifications import send_new_product_notification_to_all_retailers
        return send_new_product_notification_to_all_retailers(product_id, product_name, category, price)
    except Exception as e:
        print(f"Warning: Failed to notify retailers: {e}")
        return {"sent": 0, "failed": 0, "total": 0}

def update_product(product_id: str, updates: Dict[str, Any]) -> bool:
    """Update a product."""
    data = read_json("products.json")
    products = data.get("products", [])
    
    for i, product in enumerate(products):
        if product.get("product_id") == product_id:
            products[i].update(updates)
            return write_json("products.json", data)
    return False

def delete_product(product_id: str) -> bool:
    """Delete a product."""
    data = read_json("products.json")
    products = data.get("products", [])
    
    data["products"] = [p for p in products if p.get("product_id") != product_id]
    return write_json("products.json", data)

def get_products_by_seller(seller_id: str) -> List[Dict[str, Any]]:
    """Get all products by a specific seller."""
    products = get_products()
    return [p for p in products if p.get("seller_id") == seller_id]

# Order operations
def get_orders() -> List[Dict[str, Any]]:
    """Get all orders."""
    data = read_json("orders.json")
    return data.get("orders", [])

def save_order(order: Dict[str, Any]) -> bool:
    """Save a new order."""
    data = read_json("orders.json")
    if "orders" not in data:
        data["orders"] = []
    
    # Add order_id and timestamp if not present
    if "order_id" not in order:
        order["order_id"] = str(uuid.uuid4())
    if "created_at" not in order:
        order["created_at"] = datetime.now().isoformat()
    if "status" not in order:
        order["status"] = "pending"
    if "payment_status" not in order:
        order["payment_status"] = "pending"
    
    data["orders"].append(order)
    return write_json("orders.json", data)

def update_order(order_id: str, updates: Dict[str, Any]) -> bool:
    """Update an order."""
    data = read_json("orders.json")
    orders = data.get("orders", [])
    
    for i, order in enumerate(orders):
        if order.get("order_id") == order_id:
            orders[i].update(updates)
            return write_json("orders.json", data)
    return False

def get_orders_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """Get all orders for a specific customer."""
    orders = get_orders()
    return [o for o in orders if o.get("customer_id") == customer_id]

def get_orders_by_seller(seller_id: str) -> List[Dict[str, Any]]:
    """Get all orders for a specific seller (retailer/wholesaler)."""
    orders = get_orders()
    result = []
    for order in orders:
        for item in order.get("items", []):
            product = get_product_by_id(item.get("product_id"))
            if product and product.get("seller_id") == seller_id:
                result.append(order)
                break
    return result

def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Get a product by product_id."""
    products = get_products()
    for product in products:
        if product.get("product_id") == product_id:
            return product
    return None

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """Get an order by order_id."""
    orders = get_orders()
    for order in orders:
        if order.get("order_id") == order_id:
            return order
    return None

# Inventory operations
def get_inventory() -> List[Dict[str, Any]]:
    """Get all inventory records."""
    data = read_json("inventory.json")
    return data.get("inventory", [])

def save_inventory_record(record: Dict[str, Any]) -> bool:
    """Save an inventory record."""
    data = read_json("inventory.json")
    if "inventory" not in data:
        data["inventory"] = []
    
    if "record_id" not in record:
        record["record_id"] = str(uuid.uuid4())
    if "updated_at" not in record:
        record["updated_at"] = datetime.now().isoformat()
    
    data["inventory"].append(record)
    return write_json("inventory.json", data)

# Feedback/Review operations
def get_feedbacks() -> List[Dict[str, Any]]:
    """Get all feedbacks/reviews."""
    data = read_json("feedbacks.json")
    return data.get("feedbacks", [])

def save_feedback(feedback: Dict[str, Any]) -> bool:
    """Save a new feedback/review."""
    data = read_json("feedbacks.json")
    if "feedbacks" not in data:
        data["feedbacks"] = []
    
    # Add feedback_id and timestamp if not present
    if "feedback_id" not in feedback:
        feedback["feedback_id"] = str(uuid.uuid4())
    if "created_at" not in feedback:
        feedback["created_at"] = datetime.now().isoformat()
    
    data["feedbacks"].append(feedback)
    return write_json("feedbacks.json", data)

def get_feedbacks_by_product(product_id: str) -> List[Dict[str, Any]]:
    """Get all feedbacks for a specific product."""
    feedbacks = get_feedbacks()
    return [f for f in feedbacks if f.get("product_id") == product_id]

def get_feedbacks_by_seller(seller_id: str) -> List[Dict[str, Any]]:
    """Get all feedbacks for products by a specific seller.
    Checks both:
    1. Product's seller_id (direct product ownership)
    2. Order's seller_id (if feedback is linked to an order)
    """
    feedbacks = get_feedbacks()
    result = []
    for feedback in feedbacks:
        product = get_product_by_id(feedback.get("product_id"))
        if product:
            # Check if product's seller_id matches
            if product.get("seller_id") == seller_id:
                result.append(feedback)
            else:
                # Also check if feedback is linked to an order where this seller is the seller
                order_id = feedback.get("order_id")
                if order_id:
                    order = get_order_by_id(order_id)
                    if order and order.get("seller_id") == seller_id:
                        result.append(feedback)
    return result

def update_feedback(feedback_id: str, updates: Dict[str, Any]) -> bool:
    """Update a feedback."""
    data = read_json("feedbacks.json")
    feedbacks = data.get("feedbacks", [])
    
    for i, feedback in enumerate(feedbacks):
        if feedback.get("feedback_id") == feedback_id:
            feedbacks[i].update(updates)
            feedbacks[i]["updated_at"] = datetime.now().isoformat()
            return write_json("feedbacks.json", data)
    return False

def delete_feedback(feedback_id: str) -> bool:
    """Delete a feedback."""
    data = read_json("feedbacks.json")
    feedbacks = data.get("feedbacks", [])
    
    data["feedbacks"] = [f for f in feedbacks if f.get("feedback_id") != feedback_id]
    return write_json("feedbacks.json", data)

