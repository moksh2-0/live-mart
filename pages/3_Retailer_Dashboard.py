import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.database import (
    get_products, update_product, delete_product,
    get_products_by_seller, get_orders_by_seller, get_user_by_id,
    get_product_by_id, get_order_by_id
)
# Note: Removed save_product import - retailers cannot add their own products
from datetime import datetime
from collections import defaultdict

st.set_page_config(page_title="LiveMART - Retailer Dashboard", page_icon=None, layout="wide", initial_sidebar_state="expanded")

# Require authentication
require_auth("retailer")

# Show balloons if just logged in
if st.session_state.get("show_login_balloons", False):
    st.balloons()
    # Clear the flag so balloons only show once
    st.session_state.show_login_balloons = False

user = get_current_user()
retailer_id = user.get("user_id")

# Sidebar with sign out
with st.sidebar:
    st.header(f"👤 {user.get('name', 'Retailer')}")
    st.caption(f"Role: Retailer")
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
            key="retailer_update_location"
        )
        
        if st.button("Update Location", key="retailer_update_btn", use_container_width=True):
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

st.title(f"Retailer Dashboard - {user.get('name', 'Retailer')}")

# Tabs for different sections
# Note: Retailers cannot add their own products - they only get products from wholesalers
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Inventory Management", 
    "Customer Orders", 
    "Order from Wholesaler",
    "Customer Reviews & Complaints",
    "Customer History"
])

# Tab 1: Inventory Management
with tab1:
    st.header("Your Products")
    
    my_products = get_products_by_seller(retailer_id)
    
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
        st.info("You don't have any products in your inventory yet. Order products from wholesalers in the 'Order from Wholesaler' tab to add them to your inventory.")

# Note: Tab 2 (Add Product) removed - Retailers can only get products from wholesalers
# Retailers add products to their inventory by ordering from wholesalers in the "Order from Wholesaler" tab

# Tab 2: Customer Orders
with tab2:
    st.header("Customer Orders")
    
    # Get only customer orders (where seller_id is this retailer)
    # Filter to show only orders from customers (not retailer-to-wholesaler orders)
    from utils.database import get_orders
    all_orders = get_orders()
    customer_orders = [
        o for o in all_orders 
        if o.get("seller_id") == retailer_id 
        and o.get("order_type") != "retailer_to_wholesaler"  # Exclude retailer orders to wholesaler
    ]
    
    # Mark customer orders with order_type if not already set
    for order in customer_orders:
        if "order_type" not in order:
            order["order_type"] = "customer_to_retailer"
    
    if customer_orders:
        st.write(f"You have {len(customer_orders)} customer order(s).")
        
        for order in customer_orders:
            order_status = order.get('status', 'pending')
            order_id = order.get('order_id', 'N/A')
            
            # Check if order needs wholesaler order
            needs_wholesaler = order.get("needs_wholesaler_order", False)
            wholesaler_order_id = order.get("wholesaler_order_id")
            # Ensure wholesaler_order_id is a string (not boolean) - filter out boolean values
            if not isinstance(wholesaler_order_id, str):
                wholesaler_order_id = None
            
            status_display = order_status.title()
            if order_status == "pending wholesaler order":
                status_display = "Pending Wholesaler Order [HIGH PRIORITY]"
            
            with st.expander(f"Order #{order_id[:8]} - {status_display} - ₹{order.get('total_amount', 0):.2f}"):
                customer = get_user_by_id(order.get("customer_id"))
                st.write(f"**Customer:** {customer.get('name', 'Unknown') if customer else 'Unknown'}")
                st.write(f"**Order Date:** {order.get('created_at', 'N/A')}")
                st.write(f"**Status:** {order_status.title()}")
                st.write(f"**Payment Status:** {order.get('payment_status', 'N/A')}")
                st.write(f"**Payment Method:** {order.get('payment_method', 'N/A')}")
                st.write(f"**Total Amount:** ₹{order.get('total_amount', 0):.2f}")
                
                # Show if needs wholesaler order
                if needs_wholesaler and not wholesaler_order_id:
                    st.warning("⚠️ This order requires ordering from wholesaler. Items are out of stock.")
                    st.info("Please go to 'Order from Wholesaler' tab to place order for these items.")
                
                # Show linked wholesaler order ID (ensure it's a string, not boolean)
                if wholesaler_order_id and isinstance(wholesaler_order_id, str):
                    st.info(f"✅ Linked to Wholesaler Order: #{wholesaler_order_id[:8]}")
                
                st.subheader("Items:")
                for item in order.get("items", []):
                    product = None
                    for p in get_products():
                        if p.get("product_id") == item.get("product_id"):
                            product = p
                            break
                    if product:
                        st.write(f"- {item.get('quantity', 0)}x {product.get('name', 'Unknown')} @ ₹{item.get('price', 0):.2f}")
                
                # Update order status (but don't allow manual update to "pending wholesaler order")
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
                        if update_order_status(order_id, new_status):
                            st.success(f"Status updated to {new_status}! Customer will be notified via email.")
                            st.rerun()
                        else:
                            st.error("Failed to update order status.")
    else:
        st.info("No customer orders yet. Orders from customers will appear here.")

# Tab 4: Order from Wholesaler
with tab3:
    st.header("Order Products from Wholesalers")
    
    # Sub-tabs: New Order and Order History
    sub_tab1, sub_tab2 = st.tabs(["Place New Order", "Order History"])
    
    with sub_tab1:
        # Get customer orders that need wholesaler order (high priority)
        from utils.database import get_orders
        all_orders = get_orders()
        customer_orders_needing_wholesaler = [
            o for o in all_orders 
            if o.get("seller_id") == retailer_id 
            and o.get("order_type") == "customer_to_retailer"
            and o.get("needs_wholesaler_order", False)
            and not o.get("wholesaler_order_id")  # Not yet ordered
            and o.get("status") != "delivered"
        ]
        
        # Sort high priority orders by date (newest first) to show most urgent on top
        customer_orders_needing_wholesaler.sort(
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )
        
        # Section 1: High Priority Orders (Linked to Customer Orders)
        if customer_orders_needing_wholesaler:
            st.subheader("🔴 High Priority: Orders Linked to Customer Orders")
            st.warning(f"⚠️ You have {len(customer_orders_needing_wholesaler)} customer order(s) that need wholesaler restocking. Please place orders to fulfill customer orders.")
            
            for customer_order in customer_orders_needing_wholesaler:
                customer = get_user_by_id(customer_order.get("customer_id"))
                customer_name = customer.get("name", "Unknown") if customer else "Unknown"
                
                # Display customer order in a container with high priority styling
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #fff3cd; padding: 1rem; border-left: 4px solid #ffc107; border-radius: 4px; margin-bottom: 1rem;">
                        <h4 style="color: #856404; margin: 0;">Customer Order: #{customer_order.get('order_id', 'N/A')[:8]}</h4>
                        <p style="margin: 0.5rem 0;"><strong>Customer:</strong> {customer_name}</p>
                        <p style="margin: 0;"><strong>Total Amount:</strong> ₹{customer_order.get('total_amount', 0):.2f}</p>
                        <p style="margin: 0.5rem 0 0 0;"><strong>Status:</strong> {customer_order.get('status', 'pending').title()}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for item in customer_order.get("items", []):
                        product_id = item.get("product_id")
                        quantity = item.get("quantity", 1)
                        
                        # Find wholesaler products for this item
                        all_products = get_products()
                        wholesaler_products_for_item = [
                            p for p in all_products 
                            if p.get("product_id") == product_id 
                            and p.get("seller_type") == "wholesaler"
                        ]
                        
                        if wholesaler_products_for_item:
                            product_info = wholesaler_products_for_item[0]  # Use first one
                            for wholesaler_product in wholesaler_products_for_item:
                                wholesaler = get_user_by_id(wholesaler_product.get("seller_id"))
                                wholesaler_name = wholesaler.get("name", "Unknown") if wholesaler else "Unknown"
                                
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f"**Product:** {product_info.get('name', 'Product')}")
                                    st.write(f"**Required Quantity:** {quantity} units")
                                    st.write(f"**Wholesaler:** {wholesaler_name}")
                                    st.write(f"**Price per unit:** ₹{wholesaler_product.get('price', 0):.2f}")
                                    st.write(f"**Stock available:** {wholesaler_product.get('stock', 0)} units")
                                
                                with col2:
                                    if wholesaler_product.get("stock", 0) >= quantity:
                                        if st.button(f"🔴 Order from {wholesaler_name}", 
                                                   key=f"hp_order_{customer_order.get('order_id')}_{wholesaler_product.get('product_id')}_{wholesaler_product.get('seller_id')}",
                                                   type="primary", use_container_width=True, help=f"Place high priority order for {quantity} units"):
                                            from utils.retailer_wholesaler_orders import create_retailer_to_wholesaler_order
                                            success, order_id, message = create_retailer_to_wholesaler_order(
                                                retailer_id=retailer_id,
                                                wholesaler_id=wholesaler_product.get("seller_id"),
                                                product_id=product_id,
                                                quantity=quantity,
                                                linked_customer_order_id=customer_order.get("order_id")
                                            )
                                            if success:
                                                st.success(f"✅ High Priority Order Placed! Order ID: #{order_id[:8] if order_id else 'N/A'}")
                                                st.info(f"Stock updated automatically. Customer order status: 'Pending wholesaler order'")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to place order: {message}")
                                    else:
                                        st.warning(f"⚠️ Insufficient stock. Available: {wholesaler_product.get('stock', 0)}, Required: {quantity}")
                                
                                st.divider()
                        else:
                            st.warning(f"⚠️ No wholesaler has {item.get('name', 'this product')} available.")
                    
                    st.divider()
        
        st.markdown("---")
        
        # Section 2: All Products from Wholesalers
        st.subheader("All Products from Wholesalers")
        
        all_products = get_products()
        wholesaler_products = [p for p in all_products if p.get("seller_type") == "wholesaler"]
        
        # Group products by product_id and then by wholesaler
        from utils.product_aggregation import get_product_stock_info
        product_ids = list(set([p.get("product_id") for p in wholesaler_products]))
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            categories = list(set([p.get("category", "All") for p in wholesaler_products if p.get("category")]))
            selected_cat = st.selectbox("Category", ["All"] + sorted(categories), key="wholesaler_cat_filter")
        with col2:
            search_term = st.text_input("Search products", key="wholesaler_search")
        
        # Display products grouped by product_id, showing each wholesaler separately
        displayed_products = set()
        
        for product_id in product_ids:
            stock_info = get_product_stock_info(product_id)
            product_name = stock_info.get("product_name", "Unknown")
            category = stock_info.get("category", "")
            
            # Filter by category and search
            if selected_cat != "All" and category != selected_cat:
                continue
            if search_term and search_term.lower() not in product_name.lower():
                continue
            
            # Get all wholesaler products for this product_id
            wholesaler_products_for_id = [
                p for p in wholesaler_products 
                if p.get("product_id") == product_id
            ]
            
            if not wholesaler_products_for_id:
                continue
            
            st.markdown(f"### {product_name} ({category})")
            
            # Show each wholesaler's offering separately
            for wholesaler_product in wholesaler_products_for_id:
                wholesaler = get_user_by_id(wholesaler_product.get("seller_id"))
                wholesaler_name = wholesaler.get("name", "Unknown") if wholesaler else "Unknown"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**Wholesaler:** {wholesaler_name}")
                    st.write(f"**Price:** ₹{wholesaler_product.get('price', 0):.2f} per unit")
                    st.write(f"**Stock:** {wholesaler_product.get('stock', 0)} units")
                    if wholesaler_product.get("description"):
                        st.caption(wholesaler_product.get("description")[:100] + "..." if len(wholesaler_product.get("description", "")) > 100 else wholesaler_product.get("description"))
                
                with col2:
                    max_qty = wholesaler_product.get("stock", 1)
                    # Set value to 0 if stock is 0, otherwise 1
                    default_value = 1 if max_qty > 0 else 0
                    min_val = 1 if max_qty > 0 else 0
                    order_qty = st.number_input(
                        "Quantity", 
                        min_value=min_val, 
                        max_value=max_qty, 
                        value=default_value, 
                        key=f"order_qty_{wholesaler_product.get('product_id')}_{wholesaler_product.get('seller_id')}"
                    )
                
                with col3:
                    if st.button("Place Order", 
                               key=f"order_{wholesaler_product.get('product_id')}_{wholesaler_product.get('seller_id')}",
                               use_container_width=True):
                        from utils.retailer_wholesaler_orders import create_retailer_to_wholesaler_order
                        success, order_id, message = create_retailer_to_wholesaler_order(
                            retailer_id=retailer_id,
                            wholesaler_id=wholesaler_product.get("seller_id"),
                            product_id=wholesaler_product.get("product_id"),
                            quantity=order_qty,
                            linked_customer_order_id=None  # Independent order
                        )
                        if success:
                            st.success(f"Order Placed! Order ID: #{order_id[:8] if order_id else 'N/A'}")
                            st.info("Stock updated automatically.")
                            st.rerun()
                        else:
                            st.error(f"Failed: {message}")
                
                st.markdown("---")
    
    with sub_tab2:
        # Order History
        st.subheader("Order History from Wholesalers")
        
        from utils.retailer_wholesaler_orders import get_retailer_orders_from_wholesalers
        retailer_orders = get_retailer_orders_from_wholesalers(retailer_id)
        
        if retailer_orders:
            st.write(f"You have {len(retailer_orders)} order(s) placed to wholesalers.")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", 
                    ["All", "pending", "confirmed", "processing", "shipped", "delivered"],
                    key="wholesaler_order_status_filter")
            with col2:
                priority_filter = st.selectbox("Filter by Priority",
                    ["All", "High Priority", "Normal"],
                    key="wholesaler_order_priority_filter")
            
            filtered_orders = retailer_orders.copy()
            
            if status_filter != "All":
                filtered_orders = [o for o in filtered_orders if o.get("status") == status_filter]
            
            if priority_filter != "All":
                is_high_priority = priority_filter == "High Priority"
                filtered_orders = [o for o in filtered_orders if o.get("is_high_priority", False) == is_high_priority]
            
            # Display orders
            for order in filtered_orders:
                order_status = order.get("status", "pending")
                is_high_priority = order.get("is_high_priority", False)
                linked_customer_order_id = order.get("linked_customer_order_id")
                
                priority_badge = " [HIGH PRIORITY]" if is_high_priority else ""
                status_display = order_status.title() + priority_badge
                
                wholesaler = get_user_by_id(order.get("seller_id"))
                wholesaler_name = wholesaler.get("name", "Unknown") if wholesaler else "Unknown"
                
                with st.expander(f"Order #{order.get('order_id', 'N/A')[:8]} - {status_display} - {wholesaler_name} - ₹{order.get('total_amount', 0):.2f}"):
                    st.write(f"**Wholesaler:** {wholesaler_name}")
                    st.write(f"**Order Date:** {order.get('created_at', 'N/A')}")
                    st.write(f"**Status:** {order_status.title()}")
                    st.write(f"**Total Amount:** ₹{order.get('total_amount', 0):.2f}")
                    
                    if is_high_priority and linked_customer_order_id:
                        customer_order = get_order_by_id(linked_customer_order_id)
                        if customer_order:
                            customer = get_user_by_id(customer_order.get("customer_id"))
                            customer_name = customer.get("name", "Unknown") if customer else "Unknown"
                            st.warning(f"**HIGH PRIORITY** - Linked to Customer Order: #{linked_customer_order_id[:8]} (Customer: {customer_name})")
                    
                    st.subheader("Items:")
                    for item in order.get("items", []):
                        product = get_product_by_id(item.get("product_id"))
                        product_name = product.get("name", "Unknown") if product else "Unknown"
                        st.write(f"- {item.get('quantity', 0)}x {product_name} @ ₹{item.get('price', 0):.2f}")
        else:
            st.info("No orders placed to wholesalers yet.")

# Tab 4: Customer Reviews & Complaints
with tab4:
    st.header("Customer Reviews & Complaints")
    
    from utils.database import get_feedbacks_by_seller, update_feedback
    from utils.feedback import display_product_feedbacks
    
    feedbacks = get_feedbacks_by_seller(retailer_id)
    
    if not feedbacks:
        st.info("No customer reviews or complaints yet. Reviews will appear here when customers leave feedback on your products.")
    else:
        st.write(f"You have **{len(feedbacks)}** feedback(s) from customers.")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            feedback_type_filter = st.selectbox(
                "Filter by Type",
                ["All", "review", "complaint", "query"],
                key="feedback_type_filter"
            )
        with col2:
            rating_filter = st.selectbox(
                "Filter by Rating",
                ["All", "5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"],
                key="rating_filter"
            )
        with col3:
            sort_option = st.selectbox(
                "Sort By",
                ["Most Recent", "Oldest First", "Highest Rating", "Lowest Rating"],
                key="sort_option"
            )
        
        # Filter feedbacks
        filtered_feedbacks = feedbacks.copy()
        
        if feedback_type_filter != "All":
            filtered_feedbacks = [f for f in filtered_feedbacks if f.get("feedback_type") == feedback_type_filter]
        
        if rating_filter != "All":
            rating_value = int(rating_filter[0])
            filtered_feedbacks = [f for f in filtered_feedbacks if f.get("rating") == rating_value]
        
        # Sort feedbacks
        if sort_option == "Most Recent":
            filtered_feedbacks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_option == "Oldest First":
            filtered_feedbacks.sort(key=lambda x: x.get("created_at", ""))
        elif sort_option == "Highest Rating":
            filtered_feedbacks.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_option == "Lowest Rating":
            filtered_feedbacks.sort(key=lambda x: x.get("rating", 0))
        
        # Display feedbacks
        st.markdown("---")
        
        # Summary statistics
        total_reviews = len([f for f in feedbacks if f.get("feedback_type") == "review"])
        total_complaints = len([f for f in feedbacks if f.get("feedback_type") == "complaint"])
        total_queries = len([f for f in feedbacks if f.get("feedback_type") == "query"])
        ratings_list = [f.get("rating", 0) for f in feedbacks if f.get("rating")]
        avg_rating = sum(ratings_list) / len(ratings_list) if ratings_list else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Feedback", len(feedbacks))
        with col2:
            st.metric("Average Rating", f"{avg_rating:.1f}/5" if avg_rating > 0 else "N/A")
        with col3:
            st.metric("Complaints", total_complaints)
        with col4:
            st.metric("Queries", total_queries)
        
        st.markdown("---")
        
        # Analytics Section - Always show when there are feedbacks
        st.subheader("📊 Analytics & Insights")
        
        # Debug info (can be removed later)
        if len(feedbacks) > 0 and len(ratings_list) == 0:
            st.warning("⚠️ You have feedbacks but no ratings. Analytics will show once ratings are available.")
        
        # Create tabs for different analytics views
        analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs([
            "Rating Distribution", 
            "Product Performance", 
            "Review Trends"
        ])
        
        with analytics_tab1:
            # Rating Distribution Chart
            if ratings_list and len(ratings_list) > 0:
                # Count ratings by star (always calculate this first)
                rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for rating in ratings_list:
                    if 1 <= rating <= 5:
                        rating_counts[rating] = rating_counts.get(rating, 0) + 1
                
                # Try to use pandas for better chart, fallback if not available
                try:
                    import pandas as pd
                    # Create DataFrame for chart
                    rating_df = pd.DataFrame({
                        'Rating': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
                        'Count': [rating_counts[1], rating_counts[2], rating_counts[3], rating_counts[4], rating_counts[5]]
                    })
                    st.bar_chart(rating_df.set_index('Rating'))
                except ImportError:
                    # Fallback without pandas
                    rating_counts_list = [rating_counts[1], rating_counts[2], rating_counts[3], rating_counts[4], rating_counts[5]]
                    st.bar_chart({"Count": rating_counts_list})
                
                # Show percentage breakdown
                total_ratings = len(ratings_list)
                col1, col2, col3, col4, col5 = st.columns(5)
                for i, col in enumerate([col1, col2, col3, col4, col5], 1):
                    count = rating_counts[i]
                    percentage = (count / total_ratings * 100) if total_ratings > 0 else 0
                    with col:
                        st.metric(f"{i} Star", count, f"{percentage:.1f}%")
            else:
                st.info("No ratings available for analytics.")
        
        with analytics_tab2:
            # Product Performance Analytics
            # Group feedbacks by product
            product_feedbacks = defaultdict(list)
            for feedback in feedbacks:
                product_id = feedback.get("product_id")
                if product_id:
                    product_feedbacks[product_id].append(feedback)
            
            if product_feedbacks:
                # Calculate average rating per product
                product_stats = []
                for product_id, product_fb_list in product_feedbacks.items():
                    product = get_product_by_id(product_id)
                    if product:
                        product_ratings = [f.get("rating", 0) for f in product_fb_list if f.get("rating")]
                        avg_product_rating = sum(product_ratings) / len(product_ratings) if product_ratings else 0
                        product_stats.append({
                            "product_id": product_id,
                            "product_name": product.get("name", "Unknown"),
                            "review_count": len(product_fb_list),
                            "avg_rating": avg_product_rating,
                            "total_ratings": len(product_ratings)
                        })
                
                # Sort by average rating (descending)
                product_stats.sort(key=lambda x: x["avg_rating"], reverse=True)
                
                # Display top products
                st.write("**Top Rated Products:**")
                for stat in product_stats[:10]:  # Show top 10
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{stat['product_name']}**")
                    with col2:
                        st.metric("Avg Rating", f"{stat['avg_rating']:.1f}/5")
                    with col3:
                        st.metric("Reviews", stat['review_count'])
                    st.markdown("---")
                
                # Create chart for product ratings
                if len(product_stats) > 0:
                    try:
                        import pandas as pd
                        chart_df = pd.DataFrame(product_stats[:10])  # Top 10 products
                        st.bar_chart(chart_df.set_index('product_name')['avg_rating'])
                    except ImportError:
                        # Fallback without pandas - show simple chart
                        top_products = product_stats[:10]
                        chart_data = {p['product_name']: p['avg_rating'] for p in top_products}
                        st.bar_chart(chart_data)
            else:
                st.info("No product performance data available.")
        
        with analytics_tab3:
            # Review Trends Over Time
            if feedbacks:
                try:
                    import pandas as pd
                except ImportError:
                    pd = None
                
                # Parse dates and group by month
                monthly_counts = defaultdict(int)
                monthly_ratings = defaultdict(list)
                
                for feedback in feedbacks:
                    created_at = feedback.get("created_at", "")
                    if created_at:
                        try:
                            # Parse date (format: YYYY-MM-DD or ISO format)
                            if "T" in created_at:
                                date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            else:
                                date_obj = datetime.strptime(created_at[:10], "%Y-%m-%d")
                            
                            month_key = date_obj.strftime("%Y-%m")
                            monthly_counts[month_key] += 1
                            
                            rating = feedback.get("rating", 0)
                            if rating > 0:
                                monthly_ratings[month_key].append(rating)
                        except:
                            pass
                
                if monthly_counts:
                    # Create DataFrame for trends
                    months = sorted(monthly_counts.keys())
                    counts = [monthly_counts[m] for m in months]
                    avg_ratings = [
                        sum(monthly_ratings[m]) / len(monthly_ratings[m]) 
                        if monthly_ratings[m] else 0 
                        for m in months
                    ]
                    
                    if pd:
                        trends_df = pd.DataFrame({
                            'Month': months,
                            'Review Count': counts,
                            'Avg Rating': avg_ratings
                        })
                        # Display chart
                        st.line_chart(trends_df.set_index('Month'))
                    else:
                        # Fallback without pandas
                        chart_data = {
                            'Review Count': counts,
                            'Avg Rating': avg_ratings
                        }
                        st.line_chart(chart_data)
                    
                    # Show monthly breakdown
                    st.write("**Monthly Breakdown:**")
                    for month in months:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**{month}**")
                        with col2:
                            st.metric("Reviews", monthly_counts[month])
                        with col3:
                            month_avg = sum(monthly_ratings[month]) / len(monthly_ratings[month]) if monthly_ratings[month] else 0
                            st.metric("Avg Rating", f"{month_avg:.1f}/5" if month_avg > 0 else "N/A")
                        st.markdown("---")
                else:
                    st.info("No date information available for trend analysis.")
            else:
                st.info("No review trends data available.")
        
        st.markdown("---")
        
        # Display each feedback
        for feedback in filtered_feedbacks:
            product = get_product_by_id(feedback.get("product_id"))
            customer = get_user_by_id(feedback.get("customer_id"))
            
            product_name = product.get("name", "Unknown Product") if product else "Unknown Product"
            customer_name = customer.get("name", "Anonymous") if customer else "Anonymous"
            customer_email = customer.get("email", "") if customer else ""
            
            # Determine feedback type styling
            feedback_type = feedback.get("feedback_type", "review")
            if feedback_type == "complaint":
                st.error(f"**COMPLAINT** - {product_name}")
            elif feedback_type == "query":
                st.info(f"**QUERY** - {product_name}")
            else:
                st.markdown(f"**REVIEW** - {product_name}")
            
            with st.expander(
                f"Rating: {feedback.get('rating', 0)}/5 - {customer_name} - {feedback.get('created_at', '')[:10]}",
                expanded=feedback_type != "review"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Rating display
                    rating = feedback.get("rating", 0)
                    st.markdown(f"**Rating:** {rating}/5")
                    
                    # Product info
                    if product:
                        st.markdown(f"**Product:** {product_name}")
                        st.caption(f"Category: {product.get('category', 'N/A')} | Price: ₹{product.get('price', 0):.2f}")
                    
                    # Review text
                    review_text = feedback.get("review_text", "")
                    if review_text:
                        st.markdown("---")
                        st.markdown("**Feedback:**")
                        st.write(review_text)
                    else:
                        st.caption("No written review provided.")
                    
                    # Order info if available
                    order_id = feedback.get("order_id")
                    if order_id:
                        st.caption(f"Related Order: #{order_id[:8]}")
                
                with col2:
                    # Customer info
                    st.markdown("**Customer Information:**")
                    st.write(f"**Name:** {customer_name}")
                    if customer_email:
                        st.write(f"**Email:** {customer_email}")
                    
                    # Date info
                    st.markdown("---")
                    st.caption(f"**Submitted:** {feedback.get('created_at', '')[:19]}")
                    
                    # Actions
                    st.markdown("---")
                    st.markdown("**Actions:**")
                    
                    # Respond option (could be expanded to add response functionality)
                    if st.button("Contact Customer", key=f"contact_{feedback.get('feedback_id')}", use_container_width=True):
                        if customer_email:
                            st.success(f"Email: {customer_email}")
                            st.info("In production, this would open an email client or send an automated response.")
                        else:
                            st.warning("No email address available for this customer.")
                    
                    # Mark as resolved (for complaints/queries)
                    if feedback_type in ["complaint", "query"]:
                        resolved_status = feedback.get("resolved", False)
                        if st.button(
                            "Mark as Resolved" if not resolved_status else "Mark as Unresolved",
                            key=f"resolve_{feedback.get('feedback_id')}",
                            use_container_width=True
                        ):
                            update_feedback(feedback.get("feedback_id"), {"resolved": not resolved_status})
                            st.success("Status updated!")
                            st.rerun()
                        
                        if resolved_status:
                            st.success("Resolved")
        
        # Unresolved complaints/queries summary
        unresolved = [f for f in feedbacks if f.get("feedback_type") in ["complaint", "query"] and not f.get("resolved", False)]
        if unresolved:
            st.markdown("---")
            st.warning(f"You have {len(unresolved)} unresolved complaint(s) or query(ies) that need attention.")

# Tab 5: Customer History
with tab5:
    st.header("Customer Purchase History")
    st.caption("View purchase history for all customers who have ordered from you")
    
    # Get all customer orders (exclude retailer-to-wholesaler orders)
    all_orders = get_orders()
    customer_orders = [
        o for o in all_orders
        if o.get("seller_id") == retailer_id 
        and o.get("order_type") != "retailer_to_wholesaler"  # Exclude retailer orders to wholesaler
    ]
    
    if customer_orders:
        # Group orders by customer_id
        customer_orders_dict = {}
        for order in customer_orders:
            customer_id = order.get("customer_id")
            if customer_id:
                if customer_id not in customer_orders_dict:
                    customer_orders_dict[customer_id] = []
                customer_orders_dict[customer_id].append(order)
        
        # Sort customers by total orders (descending)
        sorted_customers = sorted(
            customer_orders_dict.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        st.write(f"You have {len(sorted_customers)} customer(s) with purchase history.")
        st.markdown("---")
        
        # Display customer history
        for customer_id, orders in sorted_customers:
            customer = get_user_by_id(customer_id)
            if not customer:
                continue
            
            customer_name = customer.get("name", "Unknown Customer")
            customer_email = customer.get("email", "")
            customer_location = customer.get("location", "Not set")
            
            # Calculate customer statistics
            total_orders = len(orders)
            total_amount = sum(order.get("total_amount", 0) for order in orders)
            total_items = sum(
                sum(item.get("quantity", 0) for item in order.get("items", []))
                for order in orders
            )
            
            # Find first and last order dates
            order_dates = [order.get("created_at", "") for order in orders if order.get("created_at")]
            first_order_date = min(order_dates) if order_dates else "N/A"
            last_order_date = max(order_dates) if order_dates else "N/A"
            
            # Display customer card
            with st.expander(f"**{customer_name}** - {total_orders} order(s) - Total: ₹{total_amount:,.2f}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"{customer_name}")
                    st.write(f"**Email:** {customer_email if customer_email else 'Not provided'}")
                    st.write(f"**Location:** {customer_location}")
                    st.markdown("---")
                    st.write(f"**Total Orders:** {total_orders}")
                    st.write(f"**Total Items Purchased:** {total_items}")
                    st.write(f"**Total Amount Spent:** ₹{total_amount:,.2f}")
                    st.write(f"**First Order:** {first_order_date[:10] if first_order_date != 'N/A' else 'N/A'}")
                    st.write(f"**Last Order:** {last_order_date[:10] if last_order_date != 'N/A' else 'N/A'}")
                
                with col2:
                    st.markdown("**Quick Actions:**")
                    if customer_email:
                        st.info(f"📧 {customer_email}")
                    if st.button("View Details", key=f"view_customer_{customer_id}", use_container_width=True):
                        st.session_state[f"show_customer_{customer_id}"] = True
                
                st.markdown("---")
                st.subheader("Order History")
                
                # Sort orders by date (newest first)
                sorted_orders = sorted(
                    orders,
                    key=lambda x: x.get("created_at", ""),
                    reverse=True
                )
                
                for order in sorted_orders:
                    order_id = order.get("order_id", "N/A")
                    order_status = order.get("status", "pending")
                    order_date = order.get("created_at", "N/A")
                    
                    with st.container():
                        col_status, col_date, col_amount = st.columns([2, 2, 2])
                        
                        with col_status:
                            status_color = {
                                "pending": "🟡",
                                "confirmed": "🔵",
                                "processing": "🔵",
                                "shipped": "🟣",
                                "delivered": "🟢"
                            }.get(order_status.lower(), "⚪")
                            st.markdown(f"**Status:** {status_color} {order_status.title()}")
                        
                        with col_date:
                            st.markdown(f"**Date:** {order_date[:10] if order_date != 'N/A' else 'N/A'}")
                        
                        with col_amount:
                            st.markdown(f"**Amount:** ₹{order.get('total_amount', 0):,.2f}")
                        
                        # Order items
                        st.markdown("**Products Purchased:**")
                        items_container = st.container()
                        with items_container:
                            for item in order.get("items", []):
                                product = get_product_by_id(item.get("product_id"))
                                product_name = product.get("name", "Unknown Product") if product else "Unknown Product"
                                quantity = item.get("quantity", 0)
                                price = item.get("price", 0)
                                item_total = quantity * price
                                
                                st.markdown(f"- {quantity}x **{product_name}** @ ₹{price:.2f} = ₹{item_total:.2f}")
                        
                        # Payment info
                        payment_status = order.get("payment_status", "N/A")
                        payment_method = order.get("payment_method", "N/A")
                        st.caption(f"Payment: {payment_method.title()} - {payment_status.title()}")
                        
                        st.markdown("---")
    else:
        st.info("No customer orders yet. Customer purchase history will appear here once customers start ordering from you.")

