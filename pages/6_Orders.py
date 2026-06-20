import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.database import get_orders_by_customer, get_orders_by_seller, get_user_by_id, get_product_by_id
from utils.orders import get_order_status_display, get_payment_status_display
from datetime import datetime

st.set_page_config(page_title="LiveMART - Orders", page_icon=None, layout="wide")

# Require authentication
require_auth()

# Clear order popup state when navigating to Orders page (so popup doesn't appear here)
if "order_completed" in st.session_state:
    st.session_state.order_completed = False
    st.session_state.order_popup_shown = False

user = get_current_user()
role = user.get("role", "")

st.title("Orders")

if role == "customer":
    # Customer view
    st.header("Your Orders")
    
    orders = get_orders_by_customer(user.get("user_id"))
    
    if not orders:
        st.info("You haven't placed any orders yet. Start shopping to place your first order!")
        if st.button("Browse Products"):
            st.switch_page("pages/2_Customer_Dashboard.py")
    else:
        st.write(f"You have **{len(orders)}** order(s).")
        
        # Filter orders by status
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "confirmed", "processing", "shipped", "delivered"], key="status_filter")
        
        filtered_orders = orders
        if status_filter != "All":
            filtered_orders = [o for o in orders if o.get("status") == status_filter]
        
        for order in filtered_orders:
            with st.expander(f"Order #{order.get('order_id', 'N/A')[:8]} - {get_order_status_display(order.get('status', 'pending'))} - ₹{order.get('total_amount', 0):.2f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Order Date:** {order.get('created_at', 'N/A')}")
                    st.write(f"**Status:** {get_order_status_display(order.get('status', 'pending'))}")
                    st.write(f"**Payment Status:** {get_payment_status_display(order.get('payment_status', 'pending'))}")
                    st.write(f"**Payment Method:** {order.get('payment_method', 'N/A').title()}")
                    
                    # Show assigned retailer
                    seller_id = order.get("seller_id")
                    if seller_id:
                        retailer = get_user_by_id(seller_id)
                        if retailer:
                            retailer_name = retailer.get("name", "Unknown Retailer")
                            retailer_location = retailer.get("location", "")
                            st.write(f"**Assigned Retailer:** {retailer_name}")
                            if retailer_location:
                                st.caption(f"📍 {retailer_location}")
                            
                            # Show assignment method
                            assignment_details = order.get("retailer_assignment", {})
                            assignment_method = assignment_details.get("assignment_method", "")
                            
                            # If assignment_details is empty, it was assigned by location fallback
                            if not assignment_method or not assignment_details:
                                assignment_method = "nearest_by_location"
                            
                            if assignment_method:
                                if assignment_method == "single_retailer":
                                    st.caption("ℹ️ Assigned to single retailer (has all products in stock)")
                                elif assignment_method == "nearest_retailer":
                                    st.caption("ℹ️ Assigned to nearest retailer (has all products in stock)")
                                elif assignment_method == "nearest_by_location":
                                    st.caption("ℹ️ Assigned to nearest retailer by location (will order from wholesaler if needed)")
                                else:
                                    st.caption(f"ℹ️ Assigned by: {assignment_method}")
                
                with col2:
                    st.write(f"**Total Amount:** ₹{order.get('total_amount', 0):.2f}")
                    
                    # Show estimated delivery date or actual delivery date
                    if order.get("delivery_date"):
                        st.write(f"**Delivered On:** {order.get('delivery_date')}")
                    elif order.get("estimated_delivery_date"):
                        from datetime import datetime
                        est_date = order.get("estimated_delivery_date")
                        estimated_days = order.get("estimated_delivery_days", 0)
                        delivery_breakdown = order.get("delivery_breakdown", {})
                        
                        try:
                            est_datetime = datetime.strptime(est_date, "%Y-%m-%d")
                            today = datetime.now()
                            days_remaining = (est_datetime - today).days
                            
                            delivery_info = f"**Estimated Delivery:** {est_date}"
                            if estimated_days > 0:
                                delivery_info += f" ({estimated_days} day(s))"
                            if days_remaining > 0:
                                delivery_info += f" ({days_remaining} day(s) remaining)"
                            elif days_remaining <= 0:
                                delivery_info += " (Expected soon)"
                            
                            st.write(delivery_info)
                            
                            # Show delivery breakdown if available
                            if delivery_breakdown and delivery_breakdown.get("products"):
                                with st.expander("View Delivery Time Breakdown"):
                                    for product_info in delivery_breakdown.get("products", []):
                                        product_name = product_info.get("product_name", "Unknown")
                                        total_days = product_info.get("total_delivery_days", 0)
                                        base_days = product_info.get("base_delivery_days", 0)
                                        wholesaler_delay = product_info.get("wholesaler_delay_days", 0)
                                        distance = product_info.get("distance_km")
                                        
                                        breakdown_text = f"**{product_name}:** "
                                        if distance:
                                            breakdown_text += f"{base_days} day(s) base (distance: {distance} km)"
                                            if wholesaler_delay > 0:
                                                breakdown_text += f" + {wholesaler_delay} day(s) wholesaler delay = **{total_days} day(s)**"
                                        else:
                                            breakdown_text += f"{total_days} day(s)"
                                        
                                        st.write(breakdown_text)
                                    
                                    if delivery_breakdown.get("has_wholesaler_delay"):
                                        st.info("Note: Some items require ordering from wholesaler, which adds extra processing time.")
                        except:
                            st.write(f"**Estimated Delivery:** {est_date}")
                    
                    if order.get("transaction_id"):
                        st.write(f"**Transaction ID:** {order.get('transaction_id')}")
                
                st.subheader("Items:")
                for item in order.get("items", []):
                    product = get_product_by_id(item.get("product_id"))
                    product_name = product.get("name", "Unknown Product") if product else "Unknown Product"
                    st.write(f"- {item.get('quantity', 0)}x {product_name} @ ₹{item.get('price', 0):.2f} = ₹{item.get('price', 0) * item.get('quantity', 0):.2f}")
                
                # Order timeline with real-time updates
                st.subheader("Order Timeline")
                statuses = ["pending", "confirmed", "processing", "shipped", "delivered"]
                current_status = order.get("status", "pending")
                current_index = statuses.index(current_status) if current_status in statuses else 0
                
                # Show status updates with timestamps
                status_updates = []
                if order.get("created_at"):
                    status_updates.append(("Order Placed", order.get("created_at")))
                if order.get("status_updated_at"):
                    status_updates.append((current_status.title(), order.get("status_updated_at")))
                if order.get("delivery_date"):
                    status_updates.append(("Delivered", order.get("delivery_date")))
                
                # Timeline visualization
                for i, status in enumerate(statuses):
                    status_indicator = "•" if i <= current_index else "○"
                    status_color = "#28a745" if i <= current_index else "#6c757d"
                    status_bg = "#f0f8f0" if i <= current_index else "#f8f9fa"
                    
                    st.markdown(f"""
                    <div style="margin: 0.5rem 0; padding: 0.75rem 1rem; background-color: {status_bg}; border-left: 3px solid {status_color}; border-radius: 4px; display: flex; align-items: center; gap: 0.75rem;">
                        <span style="color: {status_color}; font-weight: bold; font-size: 1.2rem;">{status_indicator}</span>
                        <strong style="color: #333; font-size: 0.95rem;">{status.title()}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Real-time status update info
                if order.get("status_updated_at"):
                    st.caption(f"Last updated: {order.get('status_updated_at', '')[:19]}")
                
                # Delivery confirmation message
                if current_status == "delivered":
                    st.success("Delivery confirmation has been sent to your email!")
                    if order.get("delivery_date"):
                        st.info(f"Delivered on: {order.get('delivery_date', '')[:19]}")
                
                # Feedback option for delivered orders
                if current_status == "delivered":
                    st.divider()
                    st.subheader("Leave Feedback")
                    
                    order_items = order.get("items", [])
                    if order_items:
                        st.info("💡 Click 'Rate & Review' on any product below to review it.")
                        st.markdown("---")
                        
                        for item in order_items:
                            product = get_product_by_id(item.get("product_id"))
                            if product:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.write(f"**{product.get('name', 'Unknown Product')}**")
                                    st.caption(f"Quantity: {item.get('quantity', 0)} | Price: ₹{item.get('price', 0):.2f} each")
                                with col2:
                                    # Check if already reviewed for this order
                                    from utils.feedback import get_feedbacks_by_product
                                    feedbacks = get_feedbacks_by_product(item.get("product_id"))
                                    already_reviewed = any(
                                        f.get("customer_id") == user.get("user_id") and 
                                        f.get("order_id") == order.get("order_id")
                                        for f in feedbacks
                                    )
                                    if already_reviewed:
                                        st.success("✅ Reviewed")
                                    else:
                                        st.info("📝 Pending")
                                with col3:
                                    if st.button("Rate & Review", key=f"review_btn_{order.get('order_id')}_{item.get('product_id')}", use_container_width=True):
                                        st.session_state.view_product_id = item.get("product_id")
                                        st.session_state.review_order_id = order.get("order_id")
                                        st.session_state.show_review_tab = True  # Flag to show review tab
                                        st.switch_page("pages/8_Product_Detail.py")
                                st.markdown("---")
                    else:
                        st.warning("No products found in this order.")

elif role in ["retailer", "wholesaler"]:
    # Retailer/Wholesaler view
    st.header("Orders from Customers" if role == "retailer" else "Orders from Retailers")
    
    orders = get_orders_by_seller(user.get("user_id"))
    
    if not orders:
        st.info("No orders yet. Orders will appear here when customers place orders.")
    else:
        st.write(f"You have **{len(orders)}** order(s).")
        
        # Filter orders by status
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "confirmed", "processing", "shipped", "delivered"], key="status_filter")
        
        filtered_orders = orders
        if status_filter != "All":
            filtered_orders = [o for o in orders if o.get("status") == status_filter]
        
        for order in filtered_orders:
            customer = get_user_by_id(order.get("customer_id"))
            customer_name = customer.get("name", "Unknown") if customer else "Unknown"
            
            with st.expander(f"Order #{order.get('order_id', 'N/A')[:8]} - {customer_name} - {get_order_status_display(order.get('status', 'pending'))} - ₹{order.get('total_amount', 0):.2f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer:** {customer_name}")
                    if customer:
                        st.write(f"**Email:** {customer.get('email', 'N/A')}")
                        st.write(f"**Location:** {customer.get('location', 'N/A')}")
                    st.write(f"**Order Date:** {order.get('created_at', 'N/A')}")
                    st.write(f"**Status:** {get_order_status_display(order.get('status', 'pending'))}")
                
                with col2:
                    st.write(f"**Total Amount:** ₹{order.get('total_amount', 0):.2f}")
                    st.write(f"**Payment Status:** {get_payment_status_display(order.get('payment_status', 'pending'))}")
                    st.write(f"**Payment Method:** {order.get('payment_method', 'N/A').title()}")
                    if order.get("delivery_date"):
                        st.write(f"**Delivery Date:** {order.get('delivery_date')}")
                
                st.subheader("Items:")
                for item in order.get("items", []):
                    product = get_product_by_id(item.get("product_id"))
                    product_name = product.get("name", "Unknown Product") if product else "Unknown Product"
                    st.write(f"- {item.get('quantity', 0)}x {product_name} @ ₹{item.get('price', 0):.2f} = ₹{item.get('price', 0) * item.get('quantity', 0):.2f}")
                
                # Update order status
                st.subheader("Update Order Status")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    new_status = st.selectbox(
                        "Status",
                        ["pending", "confirmed", "processing", "shipped", "delivered"],
                        index=["pending", "confirmed", "processing", "shipped", "delivered"].index(order.get("status", "pending")) if order.get("status") in ["pending", "confirmed", "processing", "shipped", "delivered"] else 0,
                        key=f"status_{order.get('order_id')}"
                    )
                
                with col2:
                    if st.button("Update Status", key=f"update_{order.get('order_id')}", use_container_width=True):
                        from utils.orders import update_order_status, update_stock_after_order
                        
                        # If confirming order, update stock (before status update to ensure stock is reduced)
                        if new_status == "confirmed" and order.get("status") != "confirmed":
                            update_stock_after_order(order.get("order_id"))
                        
                        # Use update_order_status to trigger email notifications
                        if update_order_status(order.get("order_id"), new_status):
                            if new_status == "delivered":
                                st.success("Status updated to delivered! Delivery confirmation email sent to customer.")
                            else:
                                st.success(f"Status updated to {new_status}! Customer will be notified via email.")
                            st.rerun()
                        else:
                            st.error("Failed to update status")

