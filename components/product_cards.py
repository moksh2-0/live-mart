import streamlit as st
from utils.database import get_user_by_id

def display_product_card(product: dict, show_add_to_cart: bool = True, show_seller_info: bool = False, key_suffix: str = ""):
    """Display a product card with details.
    
    Args:
        product: Product dictionary
        show_add_to_cart: Whether to show add to cart button
        show_seller_info: Whether to show seller information
        key_suffix: Optional suffix to make keys unique (e.g., index)
    """
    # Create unique key suffix using product_id and optional suffix
    unique_key = f"{product.get('product_id', 'unknown')}_{key_suffix}" if key_suffix else str(product.get('product_id', 'unknown'))
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Product image with better handling
        image_url = product.get("image_url", "")
        if image_url and image_url.startswith("http"):
            try:
                st.image(image_url, width=150, use_container_width=False)
            except Exception as e:
                # Fallback if image fails to load
                st.image("https://via.placeholder.com/150x150/CCCCCC/666666?text=Image+Error", width=150)
        else:
            # Use category-based placeholder images
            category = product.get("category", "").lower()
            placeholder_map = {
                "electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=300&h=300&fit=crop",
                "clothing": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=300&h=300&fit=crop",
                "footwear": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300&h=300&fit=crop",
                "food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=300&h=300&fit=crop",
                "home": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=300&h=300&fit=crop",
            }
            placeholder = placeholder_map.get(category, "https://via.placeholder.com/150x150/E8E8E8/999999?text=No+Image")
            st.image(placeholder, width=150, use_container_width=False)
    
    with col2:
        st.subheader(product.get("name", "Unnamed Product"))
        st.write(f"**Category:** {product.get('category', 'N/A')}")
        
        # Always show retailer/seller information if available
        if product.get("seller_id"):
            seller = get_user_by_id(product.get("seller_id"))
            if seller:
                seller_name = seller.get('name', 'Unknown Seller')
                seller_type = product.get('seller_type', '').lower()
                seller_type_display = '🏪 Retailer' if seller_type == 'retailer' else '📦 Wholesaler' if seller_type == 'wholesaler' else 'Seller'
                st.write(f"**{seller_type_display}:** {seller_name}")
        
        st.write(f"**Price:** ₹{product.get('price', 0):.2f}")
        st.write(f"**Stock:** {product.get('stock', 0)} units")
        
        if product.get("availability_date"):
            st.write(f"**Available from:** {product.get('availability_date')}")
        
        if product.get("description"):
            st.caption(product.get("description")[:100] + "..." if len(product.get("description", "")) > 100 else product.get("description"))
        
        if show_add_to_cart:
            col_qty, col_btn = st.columns([1, 2])
            with col_qty:
                quantity = st.number_input("Quantity", min_value=1, max_value=product.get("stock", 1), value=1, key=f"qty_{unique_key}")
            with col_btn:
                button_key = f"add_{unique_key}"
                if st.button("Add to Cart", key=button_key, use_container_width=True):
                    add_to_cart(product, quantity)
                    # Add bounce animation with success message
                    st.markdown(f"""
                    <div style="
                        background-color: #28a745;
                        color: white;
                        padding: 0.75rem 1rem;
                        border-radius: 8px;
                        margin-top: 0.5rem;
                        font-weight: 600;
                        text-align: center;
                        animation: bounce 0.5s ease;
                    ">
                        ✓ Added {quantity} x {product.get('name', 'Product')} to cart!
                    </div>
                    <style>
                        @keyframes bounce {{
                            0%, 100% {{ transform: translateY(0); }}
                            50% {{ transform: translateY(-10px); }}
                        }}
                    </style>
                    """, unsafe_allow_html=True)
                    st.rerun()

def add_to_cart(product: dict, quantity: int):
    """Add a product to the cart in session state."""
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    # Check if product already in cart
    cart = st.session_state.cart
    for item in cart:
        if item.get("product_id") == product.get("product_id"):
            item["quantity"] += quantity
            return
    
    # Add new item to cart
    cart.append({
        "product_id": product.get("product_id"),
        "name": product.get("name"),
        "price": product.get("price"),
        "quantity": quantity,
        "stock": product.get("stock")
    })

def display_product_grid(products: list, cols: int = 3, show_add_to_cart: bool = True):
    """Display products in a grid layout."""
    if not products:
        st.info("No products found.")
        return
    
    for i in range(0, len(products), cols):
        cols_list = st.columns(cols)
        for j, col in enumerate(cols_list):
            if i + j < len(products):
                with col:
                    # Use index to create unique keys for each product card instance
                    product_index = i + j
                    display_product_card(products[i + j], show_add_to_cart=show_add_to_cart, key_suffix=str(product_index))

