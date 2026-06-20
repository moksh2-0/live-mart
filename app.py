import streamlit as st
from utils.auth import is_authenticated, get_current_user, logout_user
from utils.ui_components import apply_custom_css, render_header, render_hero_section, render_testimonial

# Page configuration
st.set_page_config(
    page_title="LiveMART - Online Delivery System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "cart" not in st.session_state:
    st.session_state.cart = []

def main():
    # Apply custom CSS
    apply_custom_css()
    
    # Render header
    render_header()
    
    # Hero section
    render_hero_section("Elevate Your Style With Bold Fashion")
    
    # Main content
    
    if not is_authenticated():
        # Show featured products or categories
        from utils.database import get_products
        from components.product_cards import add_to_cart
        
        products = get_products()[:6]  # Show first 6 products
        
        st.markdown('<div class="product-grid-container">', unsafe_allow_html=True)
        st.markdown('<h2 style="margin-bottom: 2rem; font-size: 2rem; font-weight: 700; text-align: center;">Featured Products</h2>', unsafe_allow_html=True)
        
        if products:
            # Add global JavaScript for product card clicks
            st.markdown("""
            <script>
            if (typeof handleProductCardClick === 'undefined') {
                function handleProductCardClick(productId) {
                    const url = new URL(window.location);
                    url.searchParams.set('view_product_id', productId);
                    window.location.href = url.toString();
                }
            }
            </script>
            """, unsafe_allow_html=True)
            
            # Handle product card click navigation (check once before rendering)
            query_params = st.query_params
            clicked_product_id = query_params.get("view_product_id")
            if clicked_product_id:
                st.session_state.view_product_id = clicked_product_id
                # Clear query param
                new_params = dict(query_params)
                new_params.pop("view_product_id", None)
                query_params.clear()
                for key, value in new_params.items():
                    query_params[key] = value
                st.switch_page("pages/8_Product_Detail.py")
            
            # Display products in grid using Streamlit columns
            cols_per_row = 3
            for i in range(0, len(products), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(products):
                        product = products[i + j]
                        product_index = i + j  # Unique index for each product
                        with col:
                            # Product card
                            image_url = product.get('image_url', '')
                            if not image_url or not image_url.startswith('http'):
                                image_url = 'https://via.placeholder.com/300x350/E8E8E8/999999?text=No+Image'
                            
                            # Get retailer/seller information
                            seller_name = "Unknown Seller"
                            seller_type_display = ""
                            seller_id = product.get('seller_id')
                            if seller_id:
                                from utils.database import get_user_by_id
                                seller = get_user_by_id(seller_id)
                                if seller:
                                    seller_name = seller.get('name', 'Unknown Seller')
                                    seller_type = product.get('seller_type', '').lower()
                                    if seller_type == 'retailer':
                                        seller_type_display = 'Retailer'
                                    elif seller_type == 'wholesaler':
                                        seller_type_display = 'Wholesaler'
                            
                            # Escape HTML entities to prevent code from being displayed
                            import html as html_module
                            product_name = html_module.escape(str(product.get('name', 'Unnamed Product')))
                            product_category = html_module.escape(str(product.get('category', 'N/A')))
                            seller_name_escaped = html_module.escape(str(seller_name))
                            
                            # Build retailer display HTML
                            if seller_type_display and seller_name:
                                retailer_display = f'<div style="color: #4a90e2; font-size: 0.85rem; margin: 0.5rem 0; font-weight: 500;">{seller_type_display}: {seller_name_escaped}</div>'
                            else:
                                retailer_display = ""
                            
                            # Get product ID (use index if product_id is missing)
                            product_id = product.get('product_id') or f"product_{product_index}"
                            
                            # Build complete HTML string with escaped values
                            # Make entire card clickable to view details
                            product_card_html = (
                                f'<div class="product-card" style="margin-bottom: 2rem;" onclick="handleProductCardClick(\'{product_id}\');">'
                                f'<div class="product-image-container" style="cursor: pointer;">'
                                f'<img src="{image_url}" alt="{product_name}" class="product-image" style="width: 100%; height: 300px; object-fit: cover; border-radius: 8px 8px 0 0;" />'
                                f'</div>'
                                f'<div class="product-info" style="cursor: pointer;">'
                                f'<div class="product-name">{product_name}</div>'
                                f'<div style="color: #777; font-size: 0.75rem; margin: 0.25rem 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 400;">{product_category}</div>'
                                + retailer_display +
                                f'<div class="product-price">₹{product.get("price", 0):,.2f}</div>'
                                f'</div>'
                                f'</div>'
                            )
                            st.markdown(product_card_html, unsafe_allow_html=True)
                            
                            # View Details button
                            if st.button("View Details", key=f"home_view_{product_index}_{product_id}", use_container_width=True, type="secondary"):
                                st.session_state.view_product_id = product_id
                                st.switch_page("pages/8_Product_Detail.py")
                            
                            # Add to cart button (only if logged in, but show for demo)
                            # Use index to ensure unique keys
                            if st.button("Add to Cart", key=f"home_add_{product_index}_{product_id}", use_container_width=True, type="primary"):
                                st.info("Please sign in to add items to cart")
        else:
            st.info("No products available at the moment.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Testimonial section
        render_testimonial(
            "LiveMART's styles are fresh, bold, and exactly what I needed to upgrade my wardrobe. Loved the quality and vibe!",
            "Rafi H."
        )
        
        # Call to action
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Explore Collections →", key="explore_btn", use_container_width=True):
                st.switch_page("pages/1_Registration.py")
    else:
        user = get_current_user()
        role = user.get("role", "")
        
        # Redirect based on role
        if role == "customer":
            st.switch_page("pages/2_Customer_Dashboard.py")
        elif role == "retailer":
            st.switch_page("pages/3_Retailer_Dashboard.py")
        elif role == "wholesaler":
            st.switch_page("pages/4_Wholesaler_Dashboard.py")

if __name__ == "__main__":
    main()

