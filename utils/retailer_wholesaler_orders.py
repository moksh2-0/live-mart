"""
Retailer-Wholesaler Order Management
Handles orders from retailers to wholesalers with automatic stock updates and email notifications
"""
from typing import Dict, List, Any, Optional, Tuple
from utils.database import (
    save_order, get_order_by_id, update_order, 
    get_product_by_id, update_product, get_products,
    get_user_by_id
)
from utils.email_service import send_email
from datetime import datetime
import uuid

def create_retailer_to_wholesaler_order(
    retailer_id: str,
    wholesaler_id: str,
    product_id: str,
    quantity: int,
    linked_customer_order_id: Optional[str] = None
) -> Tuple[bool, Optional[str], str]:
    """
    Create an order from retailer to wholesaler.
    Automatically updates stock and sends email notifications.
    
    Args:
        retailer_id: ID of retailer placing the order
        wholesaler_id: ID of wholesaler receiving the order
        product_id: Product ID being ordered
        quantity: Quantity to order (must match customer order if linked)
        linked_customer_order_id: Optional customer order ID this order is linked to (high priority)
    
    Returns:
        Tuple of (success: bool, order_id: Optional[str], message: str)
    """
    # Get product details
    wholesaler_product = None
    all_products = get_products()
    
    for p in all_products:
        if p.get("product_id") == product_id and p.get("seller_id") == wholesaler_id:
            wholesaler_product = p
            break
    
    if not wholesaler_product:
        return False, None, "Product not found for this wholesaler"
    
    # Check wholesaler stock
    wholesaler_stock = wholesaler_product.get("stock", 0)
    if wholesaler_stock < quantity:
        return False, None, f"Insufficient stock. Available: {wholesaler_stock}, Requested: {quantity}"
    
    # If linked to customer order, verify quantity matches
    if linked_customer_order_id:
        customer_order = get_order_by_id(linked_customer_order_id)
        if customer_order:
            # Find matching item in customer order
            order_items = customer_order.get("items", [])
            for item in order_items:
                if item.get("product_id") == product_id:
                    customer_quantity = item.get("quantity", 0)
                    if quantity != customer_quantity:
                        return False, None, f"Quantity must match customer order: {customer_quantity}"
                    break
    
    # Get product price
    price = wholesaler_product.get("price", 0)
    
    # Generate order_id before saving
    order_id = str(uuid.uuid4())
    
    # Create order
    order_data = {
        "order_id": order_id,
        "customer_id": retailer_id,  # Retailer is the customer
        "seller_id": wholesaler_id,  # Wholesaler is the seller
        "order_type": "retailer_to_wholesaler",
        "items": [{
            "product_id": product_id,
            "quantity": quantity,
            "price": price
        }],
        "total_amount": price * quantity,
        "payment_method": "offline",
        "payment_status": "pending",
        "status": "pending",
        "is_high_priority": bool(linked_customer_order_id),  # High priority if linked to customer order
        "linked_customer_order_id": linked_customer_order_id,
        "priority": "high" if linked_customer_order_id else "normal"
    }
    
    success = save_order(order_data)
    if not success:
        return False, None, "Failed to create order"
    
    # Automatically update stock
    update_result = update_stock_for_retailer_order(
        wholesaler_id=wholesaler_id,
        retailer_id=retailer_id,
        product_id=product_id,
        quantity=quantity
    )
    
    if not update_result["success"]:
        return False, None, f"Order created but stock update failed: {update_result['message']}"
    
    # Update customer order status if linked
    if linked_customer_order_id:
        customer_order = get_order_by_id(linked_customer_order_id)
        if customer_order:
            update_order(linked_customer_order_id, {
                "status": "pending wholesaler order",
                "wholesaler_order_id": order_id
            })
    
    # Send email notifications
    send_retailer_order_notifications(order_id, retailer_id, wholesaler_id, linked_customer_order_id)
    
    return True, order_id, "Order created successfully. Stock updated automatically."

def update_stock_for_retailer_order(
    wholesaler_id: str,
    retailer_id: str,
    product_id: str,
    quantity: int
) -> Dict[str, Any]:
    """
    Automatically update stock when retailer orders from wholesaler.
    
    Args:
        wholesaler_id: ID of wholesaler
        retailer_id: ID of retailer
        product_id: Product ID
        quantity: Quantity ordered
    
    Returns:
        Dictionary with success status and message
    """
    all_products = get_products()
    
    # Find wholesaler product
    wholesaler_product = None
    for p in all_products:
        if p.get("product_id") == product_id and p.get("seller_id") == wholesaler_id:
            wholesaler_product = p
            break
    
    if not wholesaler_product:
        return {"success": False, "message": "Wholesaler product not found"}
    
    # Check if wholesaler has enough stock
    current_wholesaler_stock = wholesaler_product.get("stock", 0)
    if current_wholesaler_stock < quantity:
        return {"success": False, "message": f"Insufficient wholesaler stock: {current_wholesaler_stock}"}
    
    # Decrease wholesaler stock
    new_wholesaler_stock = current_wholesaler_stock - quantity
    update_product(wholesaler_product.get("product_id"), {"stock": new_wholesaler_stock})
    
    # Find or create retailer product
    retailer_product = None
    for p in all_products:
        if p.get("product_id") == product_id and p.get("seller_id") == retailer_id:
            retailer_product = p
            break
    
    if retailer_product:
        # Increase existing retailer stock
        current_retailer_stock = retailer_product.get("stock", 0)
        new_retailer_stock = current_retailer_stock + quantity
        update_product(retailer_product.get("product_id"), {"stock": new_retailer_stock})
    else:
        # Create new retailer product entry
        retailer_product_data = {
            "product_id": product_id,
            "name": wholesaler_product.get("name"),
            "category": wholesaler_product.get("category"),
            "description": wholesaler_product.get("description", ""),
            "price": wholesaler_product.get("price"),
            "stock": quantity,
            "seller_id": retailer_id,
            "seller_type": "retailer",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": wholesaler_product.get("image_url", "")
        }
        from utils.database import save_product
        save_product(retailer_product_data)
    
    return {
        "success": True,
        "message": "Stock updated successfully",
        "wholesaler_stock_before": current_wholesaler_stock,
        "wholesaler_stock_after": new_wholesaler_stock,
        "retailer_stock_after": retailer_product.get("stock", 0) + quantity if retailer_product else quantity
    }

def send_retailer_order_notifications(
    order_id: str,
    retailer_id: str,
    wholesaler_id: str,
    linked_customer_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email notifications when retailer orders from wholesaler.
    
    Args:
        order_id: Retailer order ID
        retailer_id: Retailer user ID
        wholesaler_id: Wholesaler user ID
        linked_customer_order_id: Optional linked customer order ID
    
    Returns:
        Dictionary with notification results
    """
    retailer = get_user_by_id(retailer_id)
    wholesaler = get_user_by_id(wholesaler_id)
    
    if not retailer or not wholesaler:
        return {"sent": 0, "failed": 0}
    
    order = get_order_by_id(order_id)
    if not order:
        return {"sent": 0, "failed": 0}
    
    results = {"sent": 0, "failed": 0}
    
    # Send email to wholesaler
    wholesaler_email = wholesaler.get("email", "")
    wholesaler_name = wholesaler.get("name", "Wholesaler")
    retailer_name = retailer.get("name", "Retailer")
    
    if wholesaler_email:
        subject = f"New Order from {retailer_name}"
        if linked_customer_order_id:
            subject += " [HIGH PRIORITY - Customer Order Linked]"
        
        items_html = ""
        for item in order.get("items", []):
            product = get_product_by_id(item.get("product_id"))
            product_name = product.get("name", "Unknown Product") if product else "Unknown Product"
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{product_name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 0)}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₹{item.get('price', 0):.2f}</td>
            </tr>
            """
        
        priority_badge = ""
        customer_order_info = ""
        if linked_customer_order_id:
            customer_order = get_order_by_id(linked_customer_order_id)
            if customer_order:
                from utils.database import get_user_by_id as get_customer
                customer = get_customer(customer_order.get("customer_id"))
                customer_name = customer.get("name", "Customer") if customer else "Customer"
                priority_badge = '<div style="background-color: #dc3545; color: white; padding: 8px; border-radius: 4px; margin: 10px 0; text-align: center; font-weight: bold;">HIGH PRIORITY - Linked to Customer Order</div>'
                customer_order_info = f"""
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px; margin: 20px 0;">
                    <p><strong>Linked Customer Order:</strong> #{linked_customer_order_id[:8]}</p>
                    <p><strong>Customer:</strong> {customer_name}</p>
                    <p><em>This order is linked to a customer order. Please prioritize fulfillment.</em></p>
                </div>
                """
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007bff;">New Order from Retailer</h2>
                    <p>Dear {wholesaler_name},</p>
                    <p>You have received a new order from <strong>{retailer_name}</strong>.</p>
                    
                    {priority_badge}
                    {customer_order_info}
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>Order ID:</strong> #{order_id[:8]}</p>
                        <p><strong>Total Amount:</strong> ₹{order.get('total_amount', 0):.2f}</p>
                        <p><strong>Status:</strong> {order.get('status', 'Pending')}</p>
                    </div>
                    
                    <h3>Order Items:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background-color: #f8f9fa;">
                                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Item</th>
                                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">Quantity</th>
                                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <p style="margin-top: 20px;"><strong>Note:</strong> Stock has been automatically updated in the system.</p>
                    <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART System</p>
                </div>
            </body>
        </html>
        """
        
        body = f"""
Dear {wholesaler_name},

You have received a new order from {retailer_name}.

Order ID: {order_id[:8]}
Total Amount: ₹{order.get('total_amount', 0):.2f}
Status: {order.get('status', 'Pending')}

{f'[HIGH PRIORITY - Linked to Customer Order: {linked_customer_order_id[:8]}]' if linked_customer_order_id else ''}

Stock has been automatically updated in the system.

Best regards,
LiveMART System
        """
        
        success, msg = send_email(wholesaler_email, subject, body, html_body)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1
    
    # Send email to retailer (stock update confirmation)
    retailer_email = retailer.get("email", "")
    if retailer_email:
        subject = f"Order Placed - Stock Updated Successfully"
        body = f"""
Dear {retailer_name},

Your order to {wholesaler_name} has been placed successfully.

Order ID: {order_id[:8]}
Total Amount: ₹{order.get('total_amount', 0):.2f}

Your stock has been automatically updated in the system.

{f'This order is linked to customer order: {linked_customer_order_id[:8]}' if linked_customer_order_id else ''}

Best regards,
LiveMART System
        """
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #28a745;">Order Placed - Stock Updated</h2>
                    <p>Dear {retailer_name},</p>
                    <p>Your order to <strong>{wholesaler_name}</strong> has been placed successfully.</p>
                    
                    <div style="background-color: #f0f8f0; padding: 15px; border-left: 4px solid #28a745; border-radius: 4px; margin: 20px 0;">
                        <p><strong>Order ID:</strong> #{order_id[:8]}</p>
                        <p><strong>Total Amount:</strong> ₹{order.get('total_amount', 0):.2f}</p>
                        <p><strong>Status:</strong> {order.get('status', 'Pending')}</p>
                    </div>
                    
                    <p><strong>Your stock has been automatically updated in the system.</strong></p>
                    
                    {f'<p><em>This order is linked to customer order: #{linked_customer_order_id[:8]}</em></p>' if linked_customer_order_id else ''}
                    
                    <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART System</p>
                </div>
            </body>
        </html>
        """
        
        success, msg = send_email(retailer_email, subject, body, html_body)
        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1
    
    return results

def get_retailer_orders_from_wholesalers(retailer_id: str) -> List[Dict[str, Any]]:
    """
    Get all orders placed by a retailer to wholesalers.
    
    Args:
        retailer_id: Retailer user ID
    
    Returns:
        List of orders placed by retailer to wholesalers
    """
    from utils.database import get_orders
    all_orders = get_orders()
    
    # Filter orders where retailer is customer and order_type is retailer_to_wholesaler
    retailer_orders = [
        order for order in all_orders
        if order.get("customer_id") == retailer_id
        and order.get("order_type") == "retailer_to_wholesaler"
    ]
    
    # Sort by created_at (newest first)
    retailer_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return retailer_orders

