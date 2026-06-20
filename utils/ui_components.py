"""
UI Components for LiveMART - TrendZone-inspired design
"""
import streamlit as st

def apply_custom_css():
    """Apply custom CSS for TrendZone-inspired design."""
    st.markdown("""
    <style>
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container */
        .main {
            padding: 0;
        }
        
        .block-container {
            padding: 0;
            max-width: 100%;
        }
        
        /* Header styling */
        .header-container {
            background-color: white;
            padding: 1.5rem 3rem;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 900;
            color: #000;
            letter-spacing: -0.5px;
        }
        
        .nav-links {
            display: flex;
            gap: 2.5rem;
            list-style: none;
            margin: 0;
            padding: 0;
            align-items: center;
        }
        
        .nav-links a {
            color: #000;
            text-decoration: none;
            font-weight: 500;
            font-size: 1rem;
            transition: color 0.2s;
        }
        
        .nav-links a:hover {
            color: #666;
        }
        
        .header-right {
            display: flex;
            gap: 1.5rem;
            align-items: center;
        }
        
        .icon-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.3rem;
            padding: 0.5rem;
            color: #000;
        }
        
        .sign-in-btn {
            background-color: white;
            border: 2px solid #000;
            color: #000;
            padding: 0.6rem 1.8rem;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .sign-in-btn:hover {
            background-color: #000;
            color: white;
        }
        
        /* Hero section */
        .hero-section {
            padding: 5rem 3rem;
            text-align: center;
            background: linear-gradient(to bottom, #fafafa, white);
            margin-bottom: 3rem;
        }
        
        .hero-headline {
            font-size: 4.5rem;
            font-weight: 900;
            color: #000;
            margin: 2rem 0;
            line-height: 1.1;
            letter-spacing: -1px;
        }
        
        /* Product grid */
        .product-grid-container {
            padding: 2rem 3rem;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .product-card {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .product-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }
        
        .product-image-container {
            width: 100%;
            height: 350px;
            overflow: hidden;
            background: #f5f5f5;
        }
        
        .product-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }
        
        .product-card:hover .product-image {
            transform: scale(1.05);
        }
        
        .product-info {
            padding: 1.5rem;
        }
        
        .product-name {
            font-size: 1.2rem;
            font-weight: 600;
            color: #000;
            margin-bottom: 0.5rem;
        }
        
        .product-price {
            font-size: 1.4rem;
            font-weight: 700;
            color: #000;
        }
        
        /* Testimonial section */
        .testimonial-section {
            background: #f8f8f8;
            padding: 4rem 3rem;
            margin: 4rem 0;
            border-radius: 20px;
            max-width: 1600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .testimonial-quote-icon {
            font-size: 5rem;
            color: #ddd;
            margin-bottom: 1rem;
            line-height: 1;
        }
        
        .testimonial-text {
            font-size: 1.5rem;
            color: #000;
            margin: 1.5rem 0;
            font-style: italic;
            line-height: 1.6;
        }
        
        .testimonial-author {
            font-weight: 700;
            color: #000;
            margin-top: 1.5rem;
            font-size: 1.1rem;
        }
        
        /* Dark mode styles */
        [data-theme="dark"] {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        
        [data-theme="dark"] .header-container {
            background-color: #1a1a1a;
            border-bottom: 1px solid #333;
        }
        
        [data-theme="dark"] .logo,
        [data-theme="dark"] .nav-links a,
        [data-theme="dark"] .icon-btn {
            color: #ffffff;
        }
        
        [data-theme="dark"] .hero-section {
            background: linear-gradient(to bottom, #2a2a2a, #1a1a1a);
        }
        
        [data-theme="dark"] .hero-headline {
            color: #ffffff;
        }
        
        [data-theme="dark"] .product-card {
            background: #2a2a2a;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        [data-theme="dark"] .product-name,
        [data-theme="dark"] .product-price {
            color: #ffffff;
        }
        
        [data-theme="dark"] .testimonial-section {
            background: #2a2a2a;
        }
        
        [data-theme="dark"] .testimonial-text,
        [data-theme="dark"] .testimonial-author {
            color: #ffffff;
        }
        
        [data-theme="dark"] .sign-in-btn {
            background-color: #1a1a1a;
            border-color: #fff;
            color: #fff;
        }
        
        [data-theme="dark"] .sign-in-btn:hover {
            background-color: #fff;
            color: #000;
        }
        
        /* Button styling */
        .primary-btn {
            background-color: #000;
            color: white;
            padding: 1rem 2.5rem;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .primary-btn:hover {
            background-color: #333;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        [data-theme="dark"] .primary-btn {
            background-color: #fff;
            color: #000;
        }
        
        [data-theme="dark"] .primary-btn:hover {
            background-color: #ccc;
        }
        
        /* Section spacing */
        .section-spacing {
            margin: 4rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the top header with navigation."""
    from utils.auth import is_authenticated, get_current_user
    
    user = get_current_user()
    is_logged_in = is_authenticated()
    
    # Cart count
    cart_count = len(st.session_state.get("cart", []))
    
    st.markdown("""
    <div class="header-container">
        <div class="header-content">
            <div class="logo">LiveMART</div>
            <nav class="nav-links">
                <a href="/">Home</a>
                <a href="/Customer_Dashboard">Shop</a>
                <a href="/Search">Search</a>
                <a href="/Cart">Cart</a>
            </nav>
            <div class="header-right">
    """, unsafe_allow_html=True)
    
    # Header right section with icons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Search icon (placeholder)
        st.markdown('<button class="icon-btn" title="Search">🔍</button>', unsafe_allow_html=True)
    
    with col2:
        # Cart icon with count
        if cart_count > 0:
            st.markdown(f'<button class="icon-btn" title="Cart ({cart_count} items)">🛒 <span style="font-size: 0.7rem; background: red; color: white; border-radius: 50%; padding: 2px 6px; margin-left: -5px;">{cart_count}</span></button>', unsafe_allow_html=True)
        else:
            st.markdown('<button class="icon-btn" title="Cart">🛒</button>', unsafe_allow_html=True)
    
    # Sign In button (only show if not logged in)
    if not is_logged_in:
        col_signin = st.columns([1])[0]
        with col_signin:
            if st.button("Sign In", key="header_signin", use_container_width=True):
                st.switch_page("pages/1_Registration.py")
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)

def render_hero_section(headline: str = "Elevate Your Style With Bold Fashion"):
    """Render hero section with large headline."""
    st.markdown(f"""
    <div class="hero-section">
        <h1 class="hero-headline">{headline}</h1>
    </div>
    """, unsafe_allow_html=True)

def render_testimonial(text: str, author: str):
    """Render testimonial section."""
    st.markdown(f"""
    <div class="testimonial-section">
        <div class="testimonial-quote-icon">"</div>
        <p class="testimonial-text">{text}</p>
        <p class="testimonial-author">— {author}</p>
    </div>
    """, unsafe_allow_html=True)

def render_product_grid_html(products: list):
    """Render product grid in HTML format."""
    if not products:
        return '<p>No products found.</p>'
    
    grid_html = '<div class="product-grid">'
    for product in products:
        image_url = product.get("image_url", "")
        if not image_url or not image_url.startswith("http"):
            # Use placeholder
            image_url = "https://via.placeholder.com/300x350/E8E8E8/999999?text=No+Image"
        
        grid_html += f'''
        <div class="product-card">
            <div class="product-image-container">
                <img src="{image_url}" alt="{product.get('name', 'Product')}" class="product-image" />
            </div>
            <div class="product-info">
                <div class="product-name">{product.get('name', 'Unnamed Product')}</div>
                <div class="product-price">₹{product.get('price', 0):,.2f}</div>
            </div>
        </div>
        '''
    grid_html += '</div>'
    return grid_html
