"""
Retailer Notification System
Handles sending emails to retailers for restocking and new product notifications
"""
from typing import Dict, List, Any, Optional
from utils.database import get_users, get_user_by_id, get_order_by_id
from utils.email_service import send_email
from utils.product_aggregation import get_product_stock_info, is_product_only_listed_by_wholesaler

def send_restock_notification(retailer_id: str, product_id: str, product_name: str, wholesaler_stock: int) -> bool:
    """
    Send email to retailer to restock a product from wholesaler.
    Sent when retailer stock is 0 but wholesaler has stock.
    
    Args:
        retailer_id: ID of the retailer
        product_id: Product ID that needs restocking
        product_name: Name of the product
        wholesaler_stock: Stock available at wholesaler
    
    Returns:
        True if email sent successfully, False otherwise
    """
    retailer = get_user_by_id(retailer_id)
    if not retailer:
        return False
    
    retailer_email = retailer.get("email", "")
    retailer_name = retailer.get("name", "Retailer")
    
    if not retailer_email:
        return False
    
    subject = f"Restock Alert: {product_name} - Stock Available at Wholesaler"
    
    body = f"""
Dear {retailer_name},

You have received an order for {product_name}, but your stock is currently 0.

Good news! This product is available at the wholesaler with {wholesaler_stock} units in stock.

Please restock this item from your wholesaler to fulfill the customer order.

Product Details:
- Product Name: {product_name}
- Product ID: {product_id[:8]}
- Wholesaler Stock Available: {wholesaler_stock} units

This order will take an additional 2 days for delivery as it needs to be sourced from the wholesaler first.

Best regards,
LiveMART System
    """
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc3545;">Restock Alert: {product_name}</h2>
                <p>Dear {retailer_name},</p>
                <p>You have received an order for <strong>{product_name}</strong>, but your stock is currently <strong>0</strong>.</p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px; margin: 20px 0;">
                    <p><strong>Good news!</strong> This product is available at the wholesaler with <strong>{wholesaler_stock} units</strong> in stock.</p>
                </div>
                
                <p>Please restock this item from your wholesaler to fulfill the customer order.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>Product Details:</h3>
                    <p><strong>Product Name:</strong> {product_name}</p>
                    <p><strong>Product ID:</strong> {product_id[:8]}</p>
                    <p><strong>Wholesaler Stock Available:</strong> {wholesaler_stock} units</p>
                </div>
                
                <div style="background-color: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; border-radius: 4px; margin: 20px 0;">
                    <p><strong>Note:</strong> This order will take an additional <strong>2 days</strong> for delivery as it needs to be sourced from the wholesaler first.</p>
                </div>
                
                <p style="margin-top: 20px;">Please log in to your Retailer Dashboard to manage your inventory and orders.</p>
                <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART System</p>
            </div>
        </body>
    </html>
    """
    
    success, message = send_email(retailer_email, subject, body, html_body)
    return success

def send_new_product_notification_to_all_retailers(product_id: str, product_name: str, category: str, price: float) -> Dict[str, Any]:
    """
    Send email to all retailers when a product is only listed by wholesaler.
    Notifies them that they can list this product on their dashboard.
    
    Args:
        product_id: Product ID
        product_name: Product name
        category: Product category
        price: Product price
    
    Returns:
        Dictionary with notification results: {"sent": int, "failed": int, "total": int}
    """
    all_users = get_users()
    retailers = [u for u in all_users if u.get("role", "").lower() == "retailer"]
    
    if not retailers:
        return {"sent": 0, "failed": 0, "total": 0}
    
    results = {"sent": 0, "failed": 0, "total": len(retailers)}
    
    subject = f"New Product Available: {product_name} - Consider Adding to Your Inventory"
    
    for retailer in retailers:
        retailer_email = retailer.get("email", "")
        retailer_name = retailer.get("name", "Retailer")
        
        if not retailer_email:
            results["failed"] += 1
            continue
        
        body = f"""
Dear {retailer_name},

A new product is now available at the wholesaler level:

Product: {product_name}
Category: {category}
Price: ₹{price:,.2f}
Product ID: {product_id[:8]}

This product is currently only listed by wholesalers. Consider adding it to your inventory to expand your product range and serve more customers.

You can add this product to your Retailer Dashboard at any time.

Best regards,
LiveMART System
        """
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007bff;">New Product Available for Listing</h2>
                    <p>Dear {retailer_name},</p>
                    <p>A new product is now available at the wholesaler level that you may want to add to your inventory:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">{product_name}</h3>
                        <p><strong>Category:</strong> {category}</p>
                        <p><strong>Price:</strong> ₹{price:,.2f}</p>
                        <p><strong>Product ID:</strong> {product_id[:8]}</p>
                    </div>
                    
                    <div style="background-color: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; border-radius: 4px; margin: 20px 0;">
                        <p>This product is currently <strong>only listed by wholesalers</strong>. Consider adding it to your inventory to:</p>
                        <ul>
                            <li>Expand your product range</li>
                            <li>Serve more customers</li>
                            <li>Increase your sales opportunities</li>
                        </ul>
                    </div>
                    
                    <p>You can add this product to your <strong>Retailer Dashboard</strong> at any time.</p>
                    <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART System</p>
                </div>
            </body>
        </html>
        """
        
        success, message = send_email(retailer_email, subject, body, html_body)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1
    
    return results

def send_product_demand_notification_to_all_retailers(product_id: str, product_name: str, wholesaler_stock: int) -> Dict[str, Any]:
    """
    Send email to ALL retailers when a product is ordered but no retailer has stock.
    Notifies all retailers that this product is in demand and they should add it.
    
    Args:
        product_id: Product ID that is in demand
        product_name: Name of the product
        wholesaler_stock: Stock available at wholesaler
    
    Returns:
        Dictionary with notification results: {"sent": int, "failed": int, "total": int}
    """
    all_users = get_users()
    retailers = [u for u in all_users if u.get("role", "").lower() == "retailer"]
    
    if not retailers:
        return {"sent": 0, "failed": 0, "total": 0}
    
    results = {"sent": 0, "failed": 0, "total": len(retailers)}
    
    subject = f"Product Demand Alert: {product_name} - Customer Order Received"
    
    for retailer in retailers:
        retailer_email = retailer.get("email", "")
        retailer_name = retailer.get("name", "Retailer")
        
        if not retailer_email:
            results["failed"] += 1
            continue
        
        body = f"""
Dear {retailer_name},

A customer has placed an order for {product_name}, but NO retailer currently has this product in stock.

This product is in demand and available at the wholesaler level with {wholesaler_stock} units in stock.

Product Details:
- Product Name: {product_name}
- Product ID: {product_id[:8]}
- Wholesaler Stock Available: {wholesaler_stock} units

We recommend adding this product to your inventory to fulfill customer orders and increase your sales opportunities.

You can order this product from any wholesaler in your "Order from Wholesaler" tab.

Best regards,
LiveMART System
        """
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545;">Product Demand Alert: {product_name}</h2>
                    <p>Dear {retailer_name},</p>
                    <p>A customer has placed an order for <strong>{product_name}</strong>, but <strong>NO retailer currently has this product in stock</strong>.</p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px; margin: 20px 0;">
                        <p><strong>This product is in demand!</strong> It's available at the wholesaler level with <strong>{wholesaler_stock} units</strong> in stock.</p>
                    </div>
                    
                    <p>We recommend adding this product to your inventory to fulfill customer orders and increase your sales opportunities.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3>Product Details:</h3>
                        <p><strong>Product Name:</strong> {product_name}</p>
                        <p><strong>Product ID:</strong> {product_id[:8]}</p>
                        <p><strong>Wholesaler Stock Available:</strong> {wholesaler_stock} units</p>
                    </div>
                    
                    <div style="background-color: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; border-radius: 4px; margin: 20px 0;">
                        <p><strong>Action Required:</strong> You can order this product from any wholesaler in your <strong>"Order from Wholesaler"</strong> tab in your Retailer Dashboard.</p>
                    </div>
                    
                    <p style="margin-top: 20px;">Please log in to your Retailer Dashboard to manage your inventory and orders.</p>
                    <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART System</p>
                </div>
            </body>
        </html>
        """
        
        success, message = send_email(retailer_email, subject, body, html_body)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1
    
    return results

def check_and_send_restock_notifications(order_id: str) -> Dict[str, Any]:
    """
    Check if retailer needs to restock any items and send notifications.
    Called after payment completion when order is being confirmed.
    
    Logic:
    - When a customer places an order, the order is assigned to a retailer:
      1. First, tries to assign to nearest retailer with sufficient stock
      2. If no retailer has the product in inventory (product only at wholesaler level),
         assigns to nearest retailer by location (fallback)
    - After order assignment, if assigned retailer's stock = 0 for the product
      (either they don't have the product in inventory, or they have it but stock = 0),
      ALL retailers are notified about product demand. This ensures all retailers 
      are aware of the product demand and can add it to their inventory.
    
    Args:
        order_id: Order ID to check
    
    Returns:
        Dictionary with notification results: {"sent": int, "failed": int}
    """
    order = get_order_by_id(order_id)
    if not order:
        return {"sent": 0, "failed": 0}
    
    seller_id = order.get("seller_id")  # This is the assigned retailer
    if not seller_id:
        return {"sent": 0, "failed": 0}
    
    retailer = get_user_by_id(seller_id)
    if not retailer or retailer.get("role", "").lower() != "retailer":
        return {"sent": 0, "failed": 0}
    
    results = {"sent": 0, "failed": 0}
    items = order.get("items", [])
    
    # Track which products already sent notification (avoid duplicates)
    notified_products = set()
    
    # Check each item in the order
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)
        
        # Skip if already notified for this product
        if product_id in notified_products:
            continue
        
        # Get stock information for this product
        stock_info = get_product_stock_info(product_id)
        retailer_products = stock_info.get("retailer_products", [])
        retailer_stock = stock_info.get("retailer_stock", 0)  # Aggregated retailer stock
        wholesaler_stock = stock_info.get("wholesaler_stock", 0)
        product_name = stock_info.get("product_name", "Unknown Product")
        
        # Find the assigned retailer's stock for this specific product
        retailer_stock_for_assigned = 0
        
        for rp in retailer_products:
            if rp.get("seller_id") == seller_id:
                retailer_stock_for_assigned = rp.get("stock", 0)
                break
        
        # Check if assigned retailer stock is 0 (regardless of other retailers' stock)
        if retailer_stock_for_assigned == 0 and wholesaler_stock > 0:
            # Assigned retailer doesn't have stock - notify ALL retailers
            # This ensures all retailers are aware of the product demand
            notification_results = send_product_demand_notification_to_all_retailers(
                product_id,
                product_name,
                wholesaler_stock
            )
            results["sent"] += notification_results["sent"]
            results["failed"] += notification_results["failed"]
            notified_products.add(product_id)  # Mark as notified
    
    return results

