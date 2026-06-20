import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.database import get_products, get_user_by_id
from utils.ui_components import apply_custom_css, render_header, render_hero_section, render_testimonial
from utils.maps import show_nearby_stores_modal
from utils.recommendations import get_recommended_products, get_trending_products
from utils.product_aggregation import get_aggregated_products
from components.product_cards import add_to_cart

st.set_page_config(page_title="LiveMART - Customer Dashboard", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

# Apply custom CSS
apply_custom_css()

# Render header
render_header()

# Require authentication
require_auth("customer")

# Show balloons if just logged in
if st.session_state.get("show_login_balloons", False):
    st.balloons()
    # Clear the flag so balloons only show once
    st.session_state.show_login_balloons = False

# Initialize session state for maps
if "show_stores_map" not in st.session_state:
    st.session_state.show_stores_map = False

user = get_current_user()

# Hero section
render_hero_section(f"Welcome Back, {user.get('name', 'Customer')}!")

# Show stores map if button was clicked (show at top, before products)
if st.session_state.get("show_stores_map", False):
    st.markdown("---")
    st.markdown("## 📍 Nearby Stores")
    
    # Debug info
    center_lat, center_lng = 17.54, 78.57
    st.success(f"✅ Map loading for coordinates: {center_lat}°N, {center_lng}°E")
    
    try:
        show_nearby_stores_modal()
    except Exception as e:
        st.error(f"Error loading map: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("❌ Close Map", key="close_map", use_container_width=True):
            st.session_state.show_stores_map = False
            st.rerun()
    st.markdown("---")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")
    
    # Get aggregated products for filters (one per product_id)
    all_aggregated = get_aggregated_products()
    categories = list(set([p.get("category", "Uncategorized") for p in all_aggregated if p.get("category")]))
    categories.sort()
    
    selected_category = st.selectbox("Category", ["All"] + categories)
    
    # Price range filter
    if all_aggregated:
        prices = [p.get("price", 0) for p in all_aggregated if p.get("price", 0) > 0]
        if prices:
            min_price, max_price = st.slider(
                "Price Range (₹)",
                min_value=float(min(prices)),
                max_value=float(max(prices)),
                value=(float(min(prices)), float(max(prices)))
            )
        else:
            min_price, max_price = 0.0, 10000.0
    else:
        min_price, max_price = 0.0, 10000.0
    
    # Stock availability filter
    in_stock_only = st.checkbox("Show only in-stock items", value=True)
    
    # Location button
    st.divider()
    if st.button("📍 Find Nearby Stores", use_container_width=True, help="View stores on Google Maps", key="find_stores_btn"):
        st.session_state.show_stores_map = True
        st.rerun()
    
    # Cart summary
    st.divider()
    if "cart" in st.session_state and st.session_state.cart:
        st.header("🛒 Cart Summary")
        total = sum(item.get("price", 0) * item.get("quantity", 0) for item in st.session_state.cart)
        st.write(f"**Items:** {len(st.session_state.cart)}")
        st.write(f"**Total:** ₹{total:,.2f}")
        if st.button("View Cart", use_container_width=True):
            st.switch_page("pages/7_Cart.py")
    
    # Sign out button
    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        from utils.auth import logout_user
        logout_user()
        st.success("Logged out successfully!")
        st.rerun()

# Get aggregated products and filter according to inventory management rules
# Rule: Show wholesaler products ONLY if retailer stock = 0
filtered_products = []

for aggregated_product in all_aggregated:
    retailer_stock = aggregated_product.get("retailer_stock", 0)
    wholesaler_stock = aggregated_product.get("wholesaler_stock", 0)
    
    # Apply inventory management rule: Only show wholesaler products if retailer stock is 0
    # If retailer has stock, only show retailer products
    # If retailer stock = 0 and wholesaler has stock, show wholesaler products
    if retailer_stock > 0:
        # Retailer has stock - show this product (from retailers)
        # Use first retailer product for display
        retailer_products = aggregated_product.get("retailer_products", [])
        if retailer_products:
            # Create display product from aggregated info but use retailer product
            display_product = aggregated_product.copy()
            display_product["stock"] = retailer_stock
            display_product["stock_display"] = f"Retailer Stock: {retailer_stock} units"
            if wholesaler_stock > 0:
                display_product["stock_display"] += f" | Wholesaler Stock: {wholesaler_stock} units"
            filtered_products.append(display_product)
    elif wholesaler_stock > 0:
        # Retailer stock = 0, but wholesaler has stock - show this product (from wholesaler)
        display_product = aggregated_product.copy()
        display_product["stock"] = wholesaler_stock
        display_product["stock_display"] = f"Wholesaler Stock: {wholesaler_stock} units (available, +3 days delivery)"
        filtered_products.append(display_product)
    elif not in_stock_only:
        # No stock at all, but user wants to see out-of-stock items
        display_product = aggregated_product.copy()
        display_product["stock"] = 0
        display_product["stock_display"] = "Out of stock"
        filtered_products.append(display_product)

# Apply category filter
if selected_category != "All":
    filtered_products = [p for p in filtered_products if p.get("category") == selected_category]

# Apply price filter
filtered_products = [p for p in filtered_products if min_price <= p.get("price", 0) <= max_price]

# Apply stock filter
if in_stock_only:
    filtered_products = [p for p in filtered_products if p.get("stock", 0) > 0]

# Recommended Products Section
customer_id = user.get("user_id")
recommended_products_raw = get_recommended_products(customer_id, limit=12)  # Get more to filter

# Apply inventory management rule to recommended products: Only show wholesaler if retailer stock = 0
recommended_products = []
for product in recommended_products_raw:
    product_id = product.get("product_id")
    if product_id:
        from utils.product_aggregation import get_product_stock_info
        stock_info = get_product_stock_info(product_id)
        retailer_stock = stock_info.get("retailer_stock", 0)
        wholesaler_stock = stock_info.get("wholesaler_stock", 0)
        
        # Only include if retailer has stock, OR (retailer stock = 0 AND wholesaler has stock)
        if retailer_stock > 0:
            # Use aggregated product info
            display_product = stock_info.copy()
            display_product["stock"] = retailer_stock
            display_product["stock_display"] = f"Retailer Stock: {retailer_stock} units"
            if wholesaler_stock > 0:
                display_product["stock_display"] += f" | Wholesaler Stock: {wholesaler_stock} units"
            recommended_products.append(display_product)
        elif wholesaler_stock > 0:
            # Retailer stock = 0, wholesaler has stock
            display_product = stock_info.copy()
            display_product["stock"] = wholesaler_stock
            display_product["stock_display"] = f"Wholesaler Stock: {wholesaler_stock} units (available, +3 days delivery)"
            recommended_products.append(display_product)
    
    # Limit to 6 after filtering
    if len(recommended_products) >= 6:
        break

if recommended_products:
    st.markdown('<div class="product-grid-container">', unsafe_allow_html=True)
    st.markdown('<h2 style="margin-bottom: 2rem; font-size: 2rem; font-weight: 700;">⭐ Recommended For You</h2>', unsafe_allow_html=True)
    
    # Display recommended products
    cols_per_row = 3
    for i in range(0, len(recommended_products), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(recommended_products):
                product = recommended_products[i + j]
                product_index = i + j
                # Create unique key using product_id, seller_id (if available), and index
                product_id = product.get('product_id', 'unknown')
                seller_id = product.get('seller_id', '')
                unique_key_suffix = f"rec_{product_id}_{seller_id}_{product_index}" if seller_id else f"rec_{product_id}_{product_index}"
                
                with col:
                    # Product card with "Recommended" badge
                    image_url = product.get('image_url', '')
                    if not image_url or not image_url.startswith('http'):
                        image_url = 'https://via.placeholder.com/300x350/E8E8E8/999999?text=No+Image'
                    
                    st.markdown(f"""
                    <div class="product-card" style="margin-bottom: 2rem; position: relative;">
                        <div style="position: absolute; top: 10px; right: 10px; background-color: #FFD700; color: #000; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 700; z-index: 10;">
                            ⭐ Recommended
                        </div>
                        <div class="product-image-container">
                            <img src="{image_url}" 
                                 alt="{product.get('name', 'Product')}" 
                                 class="product-image" 
                                 style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px 12px 0 0;" />
                        </div>
                        <div class="product-info">
                            <div class="product-name">{product.get('product_name', product.get('name', 'Unnamed Product'))}</div>
                            <div style="color: #666; font-size: 0.9rem; margin: 0.5rem 0;">{product.get('category', 'N/A')}</div>
                            <div class="product-price">₹{product.get('price', 0):,.2f}</div>
                            <div style="color: #666; font-size: 0.85rem; margin-top: 0.5rem;">{product.get('stock_display', f"Stock: {product.get('stock', 0)}")}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add to cart button with unique key
                    # For aggregated products, use the first available retailer product or wholesaler product
                    available_stock = product.get("stock", 0)
                    quantity = st.number_input("Qty", min_value=1, max_value=available_stock if available_stock > 0 else 1, value=1, key=f"qty_{unique_key_suffix}")
                    if st.button("Add to Cart", key=f"add_{unique_key_suffix}", use_container_width=True):
                        # Get the actual product to add to cart (prefer retailer product if available)
                        retailer_products = product.get("retailer_products", [])
                        wholesaler_products = product.get("wholesaler_products", [])
                        product_to_add = retailer_products[0] if retailer_products else (wholesaler_products[0] if wholesaler_products else product)
                        add_to_cart(product_to_add, quantity)
                        st.success(f"Added {quantity} x {product.get('product_name', product.get('name', 'Product'))} to cart!")
                        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

# Display products in grid
st.markdown('<div class="product-grid-container">', unsafe_allow_html=True)
st.markdown('<h2 style="margin-bottom: 2rem; font-size: 2rem; font-weight: 700;">All Products</h2>', unsafe_allow_html=True)

if filtered_products:
    # Create product cards with Streamlit components for interactivity
    cols_per_row = 3
    for i in range(0, len(filtered_products), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(filtered_products):
                product = filtered_products[i + j]
                product_index = i + j
                # Create unique key using product_id and index (aggregated products don't have seller_id in the same way)
                product_id = product.get('product_id', 'unknown')
                unique_key_suffix = f"{product_id}_{product_index}"
                
                with col:
                    # Product card
                    image_url = product.get('image_url', '')
                    if not image_url or not image_url.startswith('http'):
                        image_url = 'https://via.placeholder.com/300x350/E8E8E8/999999?text=No+Image'
                    
                    st.markdown(f"""
                    <div class="product-card" style="margin-bottom: 2rem;">
                        <div class="product-image-container">
                            <img src="{image_url}" 
                                 alt="{product.get('product_name', product.get('name', 'Product'))}" 
                                 class="product-image" 
                                 style="width: 100%; height: 300px; object-fit: cover; border-radius: 12px 12px 0 0;" />
                        </div>
                        <div class="product-info">
                            <div class="product-name">{product.get('product_name', product.get('name', 'Unnamed Product'))}</div>
                            <div style="color: #666; font-size: 0.9rem; margin: 0.5rem 0;">{product.get('category', 'N/A')}</div>
                            <div class="product-price">₹{product.get('price', 0):,.2f}</div>
                            <div style="color: #666; font-size: 0.85rem; margin-top: 0.5rem;">{product.get('stock_display', f"Stock: {product.get('stock', 0)}")}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add to cart button with unique key
                    # For aggregated products, use the first available retailer product or wholesaler product
                    available_stock = product.get("stock", 0)
                    quantity = st.number_input("Qty", min_value=1, max_value=available_stock if available_stock > 0 else 1, value=1, key=f"qty_{unique_key_suffix}")
                    if st.button("Add to Cart", key=f"add_{unique_key_suffix}", use_container_width=True):
                        # Get the actual product to add to cart (prefer retailer product if available)
                        retailer_products = product.get("retailer_products", [])
                        wholesaler_products = product.get("wholesaler_products", [])
                        product_to_add = retailer_products[0] if retailer_products else (wholesaler_products[0] if wholesaler_products else product)
                        add_to_cart(product_to_add, quantity)
                        st.success(f"Added {quantity} x {product.get('product_name', product.get('name', 'Product'))} to cart!")
                        st.rerun()
else:
    st.info("No products match your filters. Try adjusting your search criteria.")

st.markdown('</div>', unsafe_allow_html=True)

# Testimonial section
render_testimonial(
    "LiveMART has transformed my shopping experience! The quality is exceptional and delivery is always on time.",
    f"{user.get('name', 'Customer')}"
)
