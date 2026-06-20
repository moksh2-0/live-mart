import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.database import get_product_by_id, get_user_by_id
from utils.orders import create_order
from utils.payments import display_payment_form
from components.product_cards import add_to_cart

st.set_page_config(page_title="LiveMART - Shopping Cart", page_icon=None, layout="wide")

# Require authentication
require_auth("customer")

# Helper function to clear order popup state
def clear_order_popup_state():
    st.session_state.order_completed = False
    st.session_state.order_popup_shown = False
    if "completed_order_id" in st.session_state:
        del st.session_state.completed_order_id
    if "completed_order_amount" in st.session_state:
        del st.session_state.completed_order_amount
    if "payment_method_used" in st.session_state:
        del st.session_state.payment_method_used

user = get_current_user()

# Check if order was just completed - show simple success message at top
if st.session_state.get("order_completed", False) and not st.session_state.get("order_popup_shown", False):
    st.session_state.order_popup_shown = True
    
    order_id = st.session_state.get("completed_order_id", "")
    amount = st.session_state.get("completed_order_amount", 0)
    payment_method = st.session_state.get("payment_method_used", "offline")
    
    # Get estimated delivery date from order
    from utils.database import get_order_by_id
    order = get_order_by_id(order_id) if order_id else None
    estimated_delivery = order.get("estimated_delivery_date", "") if order else ""
    estimated_delivery_days = order.get("estimated_delivery_days", 5) if order else 5
    delivery_breakdown = order.get("delivery_breakdown", {}) if order else {}
    
    # Calculate estimated delivery date if not set
    if not estimated_delivery:
        from datetime import datetime, timedelta
        estimated_date = datetime.now() + timedelta(days=estimated_delivery_days)
        estimated_delivery = estimated_date.strftime("%Y-%m-%d")
    
    # Get retailer info
    retailer_name = "N/A"
    if order:
        seller_id = order.get("seller_id")
        if seller_id:
            retailer = get_user_by_id(seller_id)
            if retailer:
                retailer_name = retailer.get("name", "Unknown Retailer")
    
    # Display simple success banner at top (no complex modal)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center; box-shadow: 0 8px 16px rgba(40,167,69,0.3);">
        <h2 style="color: white; font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">Order Successful</h2>
        <p style="color: white; font-size: 1.2rem; opacity: 0.95;">Your order has been placed successfully!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.balloons()
    
    # Order details in an expander
    with st.expander("Order Confirmation Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Order ID:** `#{order_id[:8] if order_id else 'N/A'}`")
            st.write(f"**Total Amount:** ₹{amount:,.2f}")
            st.write(f"**Payment Method:** {payment_method.title() if payment_method else 'Offline'}")
        
        with col2:
            st.write(f"**Assigned Retailer:** {retailer_name}")
            st.write(f"**Estimated Delivery:** {estimated_delivery} ({estimated_delivery_days} day(s))")
            if order and order.get("items"):
                st.write(f"**Items Ordered:** {len(order.get('items', []))}")
        
        # Show order items
        if order and order.get("items"):
            st.markdown("---")
            st.markdown("**Ordered Items:**")
            for item in order.get("items", []):
                item_name = item.get("name", "Unknown Product")
                item_qty = item.get("quantity", 1)
                item_price = item.get("price", 0)
                item_total = item_qty * item_price
                st.write(f"- {item_qty}x {item_name} @ ₹{item_price:.2f} = **₹{item_total:.2f}**")
        
        # Delivery breakdown if available
        if delivery_breakdown and delivery_breakdown.get("products"):
            st.markdown("---")
            st.markdown("**Delivery Time Breakdown:**")
            for product_info in delivery_breakdown.get("products", []):
                product_name = product_info.get("product_name", "Unknown Product")
                total_days = product_info.get("total_delivery_days", estimated_delivery_days)
                base_days = product_info.get("base_delivery_days", 0)
                wholesaler_delay = product_info.get("wholesaler_delay_days", 0)
                distance = product_info.get("distance_km")
                
                delivery_text = f"- **{product_name}:** "
                if distance:
                    delivery_text += f"{base_days} day(s) base (distance: {distance:.1f} km)"
                    if wholesaler_delay > 0:
                        delivery_text += f" + {wholesaler_delay} day(s) wholesaler = **{total_days} day(s) total**"
                else:
                    delivery_text += f"{total_days} day(s)"
                st.markdown(delivery_text)
        
        st.info("You will receive an order confirmation email shortly. You'll receive real-time status updates via email as your order progresses.")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("View Orders", key="popup_view_orders", use_container_width=True, type="primary"):
            clear_order_popup_state()
            st.switch_page("pages/6_Orders.py")
    
    with col2:
        if st.button("Continue Shopping", key="popup_continue", use_container_width=True):
            clear_order_popup_state()
            st.switch_page("pages/2_Customer_Dashboard.py")
    
    with col3:
        if st.button("Dismiss", key="popup_dismiss", use_container_width=True):
            clear_order_popup_state()
            st.rerun()
    
    st.stop()

st.title("Shopping Cart")

# Get cart from session state
cart = st.session_state.get("cart", [])

if not cart:
    st.info("Your cart is empty. Start shopping to add items!")
    if st.button("Browse Products"):
        st.switch_page("pages/2_Customer_Dashboard.py")
else:
    st.write(f"You have **{len(cart)}** item(s) in your cart.")
    
    # Display cart items
    total_amount = 0
    items_to_remove = []
    
    for i, item in enumerate(cart):
        product = get_product_by_id(item.get("product_id"))
        
        if not product:
            items_to_remove.append(i)
            continue
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{item.get('name', 'Unknown Product')}**")
            if product.get("description"):
                st.caption(product.get("description")[:50] + "..." if len(product.get("description", "")) > 50 else product.get("description"))
        
        with col2:
            quantity = st.number_input(
                "Qty",
                min_value=1,
                max_value=min(item.get("stock", 1), product.get("stock", 1)),
                value=item.get("quantity", 1),
                key=f"qty_{i}"
            )
            if quantity != item.get("quantity"):
                cart[i]["quantity"] = quantity
                st.rerun()
        
        with col3:
            price = item.get("price", 0)
            st.write(f"₹{price:.2f}")
        
        with col4:
            item_total = price * item.get("quantity", 1)
            total_amount += item_total
            st.write(f"**₹{item_total:.2f}**")
        
        with col5:
            if st.button("Remove", key=f"remove_{i}", help="Remove from cart", use_container_width=True):
                cart.pop(i)
                st.session_state.cart = cart
                st.rerun()
        
        st.divider()
    
    # Remove invalid items
    if items_to_remove:
        for i in sorted(items_to_remove, reverse=True):
            cart.pop(i)
        st.session_state.cart = cart
        st.rerun()
    
    # Cart summary and checkout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Order Summary")
        st.write(f"**Subtotal:** ₹{total_amount:.2f}")
        st.write(f"**Shipping:** Free")
        st.write(f"**Total:** ₹{total_amount:.2f}")
    
    with col2:
        st.subheader("Checkout")
        payment_method = st.radio("Payment Method", ["online", "offline"], horizontal=True)
        
        if st.button("Place Order", type="primary", use_container_width=True):
            # Create order
            order_created = create_order(
                customer_id=user.get("user_id"),
                items=cart,
                payment_method=payment_method
            )
            
            if order_created:
                # Get the order ID (last order)
                from utils.database import get_orders
                orders = get_orders()
                if orders:
                    latest_order = orders[-1]
                    order_id = latest_order.get("order_id")
                    
                    # Process payment
                    if payment_method == "online":
                        st.session_state.current_order_id = order_id
                        st.session_state.current_order_amount = total_amount
                        st.session_state.current_payment_method = payment_method
                        st.rerun()
                    else:
                        # Offline payment - mark order as completed and show popup
                        st.session_state.order_completed = True
                        st.session_state.order_popup_shown = False  # Reset to show popup
                        st.session_state.completed_order_id = order_id
                        st.session_state.completed_order_amount = total_amount
                        st.session_state.payment_method_used = payment_method
                        # Clear cart
                        st.session_state.cart = []
                        st.rerun()
            else:
                st.error("Failed to create order. Please try again.")
    
    # Payment form (if online payment selected)
    if "current_order_id" in st.session_state:
        st.divider()
        payment_success = display_payment_form(
            st.session_state.current_order_id,
            st.session_state.current_order_amount,
            st.session_state.current_payment_method
        )
        
        if payment_success:
            # Mark order as completed and store info
            st.session_state.order_completed = True
            st.session_state.order_popup_shown = False  # Reset to show popup
            st.session_state.completed_order_id = st.session_state.current_order_id
            st.session_state.completed_order_amount = st.session_state.current_order_amount
            st.session_state.payment_method_used = st.session_state.current_payment_method
            
            # Clear cart
            st.session_state.cart = []
            
            # Clear payment state
            if "current_order_id" in st.session_state:
                del st.session_state.current_order_id
            if "current_order_amount" in st.session_state:
                del st.session_state.current_order_amount
            if "current_payment_method" in st.session_state:
                del st.session_state.current_payment_method
            
            st.rerun()
