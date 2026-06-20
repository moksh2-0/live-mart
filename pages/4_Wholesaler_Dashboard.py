import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.database import (
    get_products, save_product, update_product, delete_product,
    get_products_by_seller, get_orders_by_seller, get_user_by_id
)
from datetime import datetime

st.set_page_config(page_title="LiveMART - Wholesaler Dashboard", page_icon=None, layout="wide", initial_sidebar_state="expanded")

# Require authentication
require_auth("wholesaler")

# Show balloons if just logged in
if st.session_state.get("show_login_balloons", False):
    st.balloons()
    # Clear the flag so balloons only show once
    st.session_state.show_login_balloons = False

user = get_current_user()
wholesaler_id = user.get("user_id")

# Sidebar with sign out
with st.sidebar:
    st.header(f"👤 {user.get('name', 'Wholesaler')}")
    st.caption(f"Role: Wholesaler")
    st.caption(f"Email: {user.get('email', '')}")
    st.caption(f"Location: {user.get('location', 'Not set')}")
    
    # Update Location Section
    st.divider()
    st.subheader("Update Location")
    with st.expander("Edit Location"):
        st.info("**Format:** City, State, Country (e.g., 'Hyderabad, Telangana, India')")
        new_location = st.text_input(
            "Enter new location",
            placeholder="e.g., Hyderabad, Telangana, India",
            value=user.get('location', ''),
            key="wholesaler_update_location"
        )
        
        if st.button("Update Location", key="wholesaler_update_btn", use_container_width=True):
            if not new_location:
                st.error("Please enter a location")
            elif ',' not in new_location:
                st.error("**Invalid format!** Use: City, State, Country")
            else:
                try:
                    from utils.database import update_user, get_user_by_id
                    from utils.geocoding import geocode_user_location
                    
                    success = update_user(user.get("user_id"), {"location": new_location.strip()})
                    if success:
                        updated_user = get_user_by_id(user.get("user_id"))
                        geocode_result = geocode_user_location(updated_user, update_user=True)
                        if geocode_result.get("success"):
                            st.success(f"Location updated: **{geocode_result.get('formatted_address', new_location)}**")
                        else:
                            st.warning(f"Location updated but geocoding failed")
                        user['location'] = new_location.strip()
                        st.rerun()
                    else:
                        st.error("Failed to update location")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        from utils.auth import logout_user
        logout_user()
        st.success("Logged out successfully!")
        st.rerun()

st.title(f"🏭 Wholesaler Dashboard - {user.get('name', 'Wholesaler')}")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["Inventory Management", "Add Product", "Retailer Orders"])

# Tab 1: Inventory Management
with tab1:
    st.header("Your Products")
    
    my_products = get_products_by_seller(wholesaler_id)
    
    if my_products:
        st.write(f"You have {len(my_products)} product(s) in your inventory.")
        
        for product in my_products:
            with st.expander(f"**{product.get('name')}** - ₹{product.get('price', 0):.2f} | Stock: {product.get('stock', 0)}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Category:** {product.get('category', 'N/A')}")
                    st.write(f"**Description:** {product.get('description', 'No description')}")
                    st.write(f"**Availability Date:** {product.get('availability_date', 'N/A')}")
                
                with col2:
                    # Edit form
                    with st.form(f"edit_{product.get('product_id')}"):
                        st.subheader("Update Product")
                        new_name = st.text_input("Name", value=product.get("name", ""), key=f"name_{product.get('product_id')}")
                        new_category = st.text_input("Category", value=product.get("category", ""), key=f"cat_{product.get('product_id')}")
                        new_price = st.number_input("Price (₹)", min_value=0.0, value=float(product.get("price", 0)), key=f"price_{product.get('product_id')}")
                        new_stock = st.number_input("Stock", min_value=0, value=int(product.get("stock", 0)), key=f"stock_{product.get('product_id')}")
                        new_description = st.text_area("Description", value=product.get("description", ""), key=f"desc_{product.get('product_id')}")
                        new_availability = st.date_input("Availability Date", value=datetime.strptime(product.get("availability_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d") if product.get("availability_date") else datetime.now(), key=f"avail_{product.get('product_id')}")
                        
                        col_update, col_delete = st.columns(2)
                        with col_update:
                            if st.form_submit_button("Update", use_container_width=True):
                                updates = {
                                    "name": new_name,
                                    "category": new_category,
                                    "price": new_price,
                                    "stock": new_stock,
                                    "description": new_description,
                                    "availability_date": new_availability.strftime("%Y-%m-%d")
                                }
                                if update_product(product.get("product_id"), updates):
                                    st.success("Product updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update product")
                        
                        with col_delete:
                            if st.form_submit_button("Delete", use_container_width=True, type="secondary"):
                                if delete_product(product.get("product_id")):
                                    st.success("Product deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete product")
    else:
        st.info("You don't have any products yet. Add your first product in the 'Add Product' tab!")

# Tab 2: Add Product
with tab2:
    st.header("Add New Product")
    
    with st.form("add_product_form"):
        name = st.text_input("Product Name *", placeholder="Enter product name")
        category = st.text_input("Category *", placeholder="e.g., Electronics, Clothing, Food")
        description = st.text_area("Description", placeholder="Product description")
        price = st.number_input("Price (₹) *", min_value=0.0, value=0.0, step=0.01)
        stock = st.number_input("Stock Quantity *", min_value=0, value=0)
        availability_date = st.date_input("Availability Date", value=datetime.now())
        image_url = st.text_input("Image URL (optional)", placeholder="https://images.unsplash.com/photo-...", 
                                  help="Enter a direct image URL. You can use Unsplash, Imgur, or any image hosting service.")
        
        submit = st.form_submit_button("Add Product", use_container_width=True)
        
        if submit:
            if not all([name, category, price >= 0, stock >= 0]):
                st.error("Please fill in all required fields (marked with *)")
            else:
                product_data = {
                    "name": name,
                    "category": category,
                    "description": description,
                    "price": float(price),
                    "stock": int(stock),
                    "seller_id": wholesaler_id,
                    "seller_type": "wholesaler",
                    "availability_date": availability_date.strftime("%Y-%m-%d"),
                    "image_url": image_url if image_url else ""
                }
                
                if save_product(product_data):
                    st.success("Product added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add product")

# Tab 3: Retailer Orders
with tab3:
    st.header("Retailer Orders")
    
    # Get only retailer orders (where seller_id is this wholesaler and order_type is retailer_to_wholesaler)
    # Filter out customer orders
    from utils.database import get_orders
    all_orders = get_orders()
    retailer_orders = [
        o for o in all_orders 
        if o.get("seller_id") == wholesaler_id 
        and o.get("order_type") == "retailer_to_wholesaler"
    ]
    
    # Sort by priority (high priority first) then by date (newest first)
    retailer_orders.sort(key=lambda x: (
        not x.get("is_high_priority", False),  # High priority first
        x.get("created_at", "")  # Then by date (newest first)
    ), reverse=True)
    
    if retailer_orders:
        # Count high priority orders
        high_priority_count = sum(1 for o in retailer_orders if o.get("is_high_priority", False))
        
        st.write(f"You have {len(retailer_orders)} order(s) from retailers.")
        if high_priority_count > 0:
            st.warning(f"⚠️ {high_priority_count} HIGH PRIORITY order(s) linked to customer orders - please prioritize!")
        
        for order in retailer_orders:
            order_status = order.get("status", "pending")
            order_id = order.get("order_id", "N/A")
            is_high_priority = order.get("is_high_priority", False)
            linked_customer_order_id = order.get("linked_customer_order_id")
            
            # Build expander title with priority badge
            priority_badge = " [HIGH PRIORITY]" if is_high_priority else ""
            title = f"Order #{order_id[:8]} - {order_status.title()}{priority_badge} - ₹{order.get('total_amount', 0):.2f}"
            
            with st.expander(title, expanded=is_high_priority):  # Auto-expand high priority orders
                retailer = get_user_by_id(order.get("customer_id"))  # retailer is the customer in this context
                retailer_name = retailer.get("name", "Unknown") if retailer else "Unknown"
                
                st.write(f"**Retailer:** {retailer_name}")
                st.write(f"**Order Date:** {order.get('created_at', 'N/A')}")
                st.write(f"**Status:** {order_status.title()}")
                st.write(f"**Total Amount:** ₹{order.get('total_amount', 0):.2f}")
                
                # Show high priority badge and linked customer order info
                if is_high_priority and linked_customer_order_id:
                    from utils.database import get_order_by_id, get_user_by_id as get_customer
                    customer_order = get_order_by_id(linked_customer_order_id)
                    if customer_order:
                        customer = get_customer(customer_order.get("customer_id"))
                        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
                        st.markdown(f"""
                        <div style="background-color: #dc3545; color: white; padding: 10px; border-radius: 5px; margin: 10px 0;">
                            <strong>HIGH PRIORITY - Linked to Customer Order</strong><br>
                            Customer Order ID: #{linked_customer_order_id[:8]}<br>
                            Customer: {customer_name}<br>
                            <em>Please prioritize this order for customer satisfaction.</em>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.subheader("Items:")
                for item in order.get("items", []):
                    product = None
                    for p in get_products():
                        if p.get("product_id") == item.get("product_id"):
                            product = p
                            break
                    if product:
                        st.write(f"- {item.get('quantity', 0)}x {product.get('name', 'Unknown')} @ ₹{item.get('price', 0):.2f}")
                
                # Update order status
                col1, col2 = st.columns(2)
                with col1:
                    status_options = ["pending", "confirmed", "processing", "shipped", "delivered"]
                    current_index = status_options.index(order_status) if order_status in status_options else 0
                    new_status = st.selectbox(
                        "Update Status",
                        status_options,
                        index=current_index,
                        key=f"status_{order_id}"
                    )
                with col2:
                    if st.button("Update Status", key=f"update_{order_id}"):
                        from utils.orders import update_order_status
                        from utils.database import update_order
                        
                        # Update wholesaler order status
                        if update_order_status(order_id, new_status):
                            # If order is confirmed, update linked customer order status back to "pending"
                            if new_status == "confirmed" and linked_customer_order_id:
                                from utils.database import get_order_by_id as get_cust_order
                                customer_order = get_cust_order(linked_customer_order_id)
                                if customer_order and customer_order.get("status") == "pending wholesaler order":
                                    update_order(linked_customer_order_id, {"status": "pending"})
                                    st.info("Linked customer order status updated to 'pending'.")
                            
                            st.success(f"Status updated to {new_status}! Retailer will be notified via email.")
                            st.rerun()
                        else:
                            st.error("Failed to update order status.")
    else:
        st.info("No orders from retailers yet. Orders will appear here when retailers place orders.")

