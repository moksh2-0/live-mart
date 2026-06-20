"""
Feedback and Notification Utilities
Includes feedback collection, delivery confirmation, and order status notifications
"""
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from utils.database import (
    get_user_by_id, get_product_by_id, get_order_by_id,
    save_feedback, get_feedbacks_by_product, get_feedbacks_by_seller
)

def send_delivery_confirmation_email(order_id: str, customer_email: str, customer_name: str):
    """
    Send delivery confirmation email using email service.
    Falls back to mock mode if email service is not configured.
    """
    if not customer_email:
        print(f"[ERROR] Cannot send delivery confirmation email: No email address for customer {customer_name}")
        return False
    
    order = get_order_by_id(order_id)
    if not order:
        print(f"[ERROR] Cannot send delivery confirmation email: Order {order_id} not found")
        return False
    
    try:
        from utils.email_service import send_delivery_confirmation_email as send_email_service
        
        # Prepare order details for email
        delivery_date = order.get('delivery_date')
        if not delivery_date:
            # Fallback to today if delivery date not set
            from datetime import datetime
            delivery_date = datetime.now().strftime("%Y-%m-%d")
        
        order_details = {
            'total_amount': order.get('total_amount', 0),
            'delivery_date': delivery_date,
            'items': order.get('items', [])
        }
        
        # Send the email
        success, message = send_email_service(customer_email, customer_name, order_id, order_details)
        
        if success:
            print(f"[SUCCESS] Delivery confirmation email sent to {customer_email} for order {order_id[:8]}")
        else:
            # Fallback to mock mode
            print(f"[WARNING] Email service failed: {message}")
            print(f"[MOCK EMAIL] To: {customer_email}")
            print(f"[MOCK EMAIL] Subject: Order #{order_id[:8]} - Delivery Confirmed!")
            print(f"[MOCK EMAIL] Body: Dear {customer_name}, Your order #{order_id[:8]} has been delivered!")
        
        return success
        
    except ImportError as e:
        # Email service not available - use mock
        print(f"[WARNING] Email service import failed: {e}")
        print(f"[MOCK EMAIL] To: {customer_email}")
        print(f"[MOCK EMAIL] Subject: Order #{order_id[:8]} - Delivery Confirmed!")
        print(f"[MOCK EMAIL] Body: Dear {customer_name}, Your order #{order_id[:8]} has been delivered!")
        return True
    except Exception as e:
        # Handle any other errors
        print(f"[ERROR] Failed to send delivery confirmation email: {str(e)}")
        print(f"[MOCK EMAIL] To: {customer_email}")
        print(f"[MOCK EMAIL] Subject: Order #{order_id[:8]} - Delivery Confirmed!")
        print(f"[MOCK EMAIL] Body: Dear {customer_name}, Your order #{order_id[:8]} has been delivered!")
        return False

def send_delivery_confirmation_sms(customer_phone: str, order_id: str):
    """
    Mock function to send delivery confirmation SMS.
    In production, this would integrate with an SMS service (Twilio, AWS SNS, etc.)
    """
    # Mock SMS sending
    print(f"[MOCK SMS] To: {customer_phone}")
    print(f"[MOCK SMS] Message: Your order #{order_id[:8]} has been delivered! Thank you for shopping with LiveMART.")
    
    return True

def send_order_status_update(customer_email: str, customer_name: str, order_id: str, status: str):
    """
    Send real-time order status update notification via email.
    Falls back to mock mode if email service is not configured.
    """
    try:
        from utils.email_service import send_order_status_update_email as send_email
        success, message = send_email(customer_email, customer_name, order_id, status)
        if not success:
            # Fallback to mock mode
            print(f"[MOCK EMAIL] To: {customer_email}")
            print(f"[MOCK EMAIL] Subject: Order #{order_id[:8]} Status Update")
            print(f"[MOCK EMAIL] {message}")
        return success
    except ImportError:
        # Email service not available - use mock
        status_messages = {
            "confirmed": "Your order has been confirmed and is being prepared!",
            "processing": "Your order is now being processed.",
            "shipped": "Great news! Your order has been shipped and is on its way.",
            "delivered": "Your order has been delivered successfully!"
        }
        msg = status_messages.get(status, f"Your order status has been updated to: {status}")
        print(f"[MOCK EMAIL] To: {customer_email}")
        print(f"[MOCK EMAIL] Subject: Order #{order_id[:8]} Status Update")
        print(f"[MOCK EMAIL] Body: Dear {customer_name}, {msg}")
        return True

def get_product_average_rating(product_id: str) -> float:
    """Calculate average rating for a product."""
    feedbacks = get_feedbacks_by_product(product_id)
    if not feedbacks:
        return 0.0
    
    ratings = [f.get("rating", 0) for f in feedbacks if f.get("rating")]
    if not ratings:
        return 0.0
    
    return sum(ratings) / len(ratings)

def get_product_rating_count(product_id: str) -> int:
    """Get total number of reviews/ratings for a product."""
    feedbacks = get_feedbacks_by_product(product_id)
    return len([f for f in feedbacks if f.get("rating")])

def display_product_feedbacks(product_id: str, limit: Optional[int] = None):
    """Display feedbacks/reviews for a product."""
    feedbacks = get_feedbacks_by_product(product_id)
    
    if not feedbacks:
        st.info("No reviews yet. Be the first to review this product!")
        return
    
    # Sort by most recent first
    feedbacks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    if limit:
        feedbacks = feedbacks[:limit]
    
    st.subheader(f"📝 Reviews & Feedback ({len(feedbacks)})")
    
    for feedback in feedbacks:
        customer = get_user_by_id(feedback.get("customer_id", ""))
        customer_name = customer.get("name", "Anonymous") if customer else "Anonymous"
        
        with st.expander(f"⭐ {feedback.get('rating', 0)}/5 - {customer_name} - {feedback.get('created_at', '')[:10]}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Rating stars
                rating = feedback.get("rating", 0)
                # Text-based rating display
                st.write(f"**Rating:** {rating}/5")
                
                # Review text
                review_text = feedback.get("review_text", "")
                if review_text:
                    st.write(f"**Review:** {review_text}")
                
                # Feedback type
                feedback_type = feedback.get("feedback_type", "review")
                if feedback_type == "complaint":
                    st.warning("⚠️ This is a complaint/query")
                elif feedback_type == "query":
                    st.info("ℹ️ This is a query")
                
            with col2:
                st.caption(f"Date: {feedback.get('created_at', '')[:10]}")
                if feedback.get("order_id"):
                    st.caption(f"Order: #{feedback.get('order_id', '')[:8]}")

def submit_feedback(customer_id: str, product_id: str, rating: int, review_text: str = "", 
                   feedback_type: str = "review", order_id: str = "") -> bool:
    """
    Submit feedback/review for a product.
    
    Args:
        customer_id: ID of the customer submitting feedback
        product_id: ID of the product being reviewed
        rating: Rating from 1-5
        review_text: Optional review text
        feedback_type: Type of feedback - "review", "complaint", "query"
        order_id: Optional order ID if feedback is related to an order
    """
    if not (1 <= rating <= 5):
        return False
    
    feedback_data = {
        "customer_id": customer_id,
        "product_id": product_id,
        "rating": rating,
        "review_text": review_text,
        "feedback_type": feedback_type,
        "order_id": order_id
    }
    
    return save_feedback(feedback_data)

def can_submit_feedback(customer_id: str, product_id: str) -> Tuple[bool, str]:
    """
    Check if customer can submit feedback for a product.
    Returns (can_submit: bool, reason: str)
    """
    # Check if customer has purchased this product
    from utils.database import get_orders_by_customer
    
    orders = get_orders_by_customer(customer_id)
    has_purchased = False
    
    for order in orders:
        if order.get("status") in ["confirmed", "processing", "shipped", "delivered"]:
            for item in order.get("items", []):
                if item.get("product_id") == product_id:
                    has_purchased = True
                    break
        if has_purchased:
            break
    
    if not has_purchased:
        return False, "You can only review products you have purchased."
    
    # Check if already reviewed (allow multiple reviews if from different orders)
    # This check is optional - we allow customers to review the same product from different orders
    # If you want to restrict to one review per product regardless of order, uncomment below:
    # feedbacks = get_feedbacks_by_product(product_id)
    # for feedback in feedbacks:
    #     if feedback.get("customer_id") == customer_id:
    #         return False, "You have already reviewed this product."
    
    return True, ""

