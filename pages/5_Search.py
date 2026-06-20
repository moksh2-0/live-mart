import streamlit as st
from datetime import datetime
from utils.auth import require_auth, get_current_user
from utils.database import get_products, get_user_by_id
from utils.filters import apply_all_filters, search_products
from components.product_cards import display_product_grid

st.set_page_config(page_title="LiveMART - Search Products", page_icon=None, layout="wide")

# Require authentication
require_auth()

user = get_current_user()

# Check for search query from header search bar
query_params = st.query_params
header_search_query = query_params.get("search_query")
if header_search_query:
    if "current_search" not in st.session_state:
        st.session_state.current_search = ""
    st.session_state.current_search = header_search_query
    # Clear query param to avoid re-triggering
    new_params = dict(query_params)
    new_params.pop("search_query", None)
    query_params.clear()
    for key, value in new_params.items():
        query_params[key] = value

# Initialize search history in session state
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# Track current search
if "current_search" not in st.session_state:
    st.session_state.current_search = ""

st.title("Search Products")

# Search and filter sidebar
with st.sidebar:
    st.header("Search & Filters")
    
    # Search history display
    if st.session_state.search_history:
        st.subheader("Recent Searches")
        st.caption("Click on a recent search to reuse it")
        
        # Show last 5 searches (most recent first)
        recent_searches = st.session_state.search_history[-5:][::-1]
        
        for idx, (search_term, timestamp) in enumerate(recent_searches):
            col1, col2 = st.columns([4, 1])
            with col1:
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M') if isinstance(timestamp, datetime) else str(timestamp)
                if st.button(f"{search_term}", key=f"history_{idx}", use_container_width=True, 
                            help=f"Searched on {timestamp_str}"):
                    st.session_state.current_search = search_term
                    if "search_input" in st.session_state:
                        st.session_state.search_input = search_term
                    st.rerun()
            with col2:
                if st.button("×", key=f"delete_{idx}", help="Remove from history"):
                    # Find the index in the full history list (recent_searches is reversed)
                    # Calculate reverse index
                    reverse_idx = len(recent_searches) - 1 - idx
                    if 0 <= reverse_idx < len(st.session_state.search_history):
                        # Map to actual history index (history is in chronological order)
                        actual_idx = len(st.session_state.search_history) - len(recent_searches) + reverse_idx
                        if 0 <= actual_idx < len(st.session_state.search_history):
                            st.session_state.search_history.pop(actual_idx)
                    st.rerun()
        
        st.divider()
    
    # Search bar with real-time search capability
    def update_search():
        """Callback to update search and add to history"""
        if st.session_state.search_input and st.session_state.search_input.strip():
            search_clean = st.session_state.search_input.strip()
            # Only add to history if it's different from current search
            if not st.session_state.search_history or st.session_state.search_history[-1][0] != search_clean:
                st.session_state.search_history.append((search_clean, datetime.now()))
                # Keep only last 20 searches
                if len(st.session_state.search_history) > 20:
                    st.session_state.search_history = st.session_state.search_history[-20:]
        st.session_state.current_search = st.session_state.search_input
    
    search_query = st.text_input(
        "Search", 
        placeholder="Type to search products...",
        value=st.session_state.current_search,
        key="search_input",
        on_change=update_search,
        help="Search by product name, description, or category. Press Enter or click outside to search."
    )
    
    # Ensure session state is synced
    if search_query != st.session_state.current_search:
        st.session_state.current_search = search_query
    
    # Clear search button
    if search_query:
        col_clear1, col_clear2 = st.columns(2)
        with col_clear1:
            if st.button("Clear", use_container_width=True, type="secondary", key="clear_search_btn"):
                st.session_state.current_search = ""
                st.session_state.search_input = ""
                st.rerun()
        with col_clear2:
            if st.button("Clear History", use_container_width=True, type="secondary", key="clear_history_btn"):
                st.session_state.search_history = []
                st.rerun()
    
    # Category filter
    all_products = get_products()
    categories = list(set([p.get("category", "Uncategorized") for p in all_products]))
    categories.sort()
    
    selected_category = st.selectbox("Category", ["All"] + categories)
    
    # Price range filter
    if all_products:
        prices = [p.get("price", 0) for p in all_products]
        min_price, max_price = st.slider(
            "Price Range (₹)",
            min_value=float(min(prices)) if prices else 0.0,
            max_value=float(max(prices)) if prices else 10000.0,
            value=(float(min(prices)) if prices else 0.0, float(max(prices)) if prices else 10000.0)
        )
    else:
        min_price, max_price = 0.0, 10000.0
    
    # Stock availability filter
    in_stock_only = st.checkbox("Show only in-stock items", value=True)
    
    # Location filter (basic - can be enhanced with Google Maps)
    if user and user.get("location"):
        st.divider()
        st.write(f"**Your Location:** {user.get('location')}")
        show_nearby_only = st.checkbox("Show nearby products only", value=False)
    else:
        show_nearby_only = False

# Apply filters
filtered_products = apply_all_filters(
    products=all_products,
    category=selected_category,
    min_price=min_price,
    max_price=max_price,
    in_stock_only=in_stock_only,
    seller_type="All",  # Seller type filter removed - always show all
    search_query=search_query
)

# Location-based filtering (basic implementation)
if show_nearby_only and user and user.get("location"):
    user_location = user.get("location").lower()
    location_filtered = []
    for product in filtered_products:
        seller = get_user_by_id(product.get("seller_id"))
        if seller and seller.get("location"):
            seller_location = seller.get("location").lower()
            # Simple location matching
            if user_location in seller_location or seller_location in user_location:
                location_filtered.append(product)
    filtered_products = location_filtered

# Display results
st.header("Search Results")

if search_query:
    st.caption(f'Searching for: "{search_query}"')

if filtered_products:
    st.write(f"Found **{len(filtered_products)}** product(s) matching your criteria.")
    
    # Sort options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_by = st.selectbox("Sort by", ["Price: Low to High", "Price: High to Low", "Name: A-Z", "Stock: High to Low"])
    
    # Apply sorting
    if sort_by == "Price: Low to High":
        filtered_products.sort(key=lambda x: x.get("price", 0))
    elif sort_by == "Price: High to Low":
        filtered_products.sort(key=lambda x: x.get("price", 0), reverse=True)
    elif sort_by == "Name: A-Z":
        filtered_products.sort(key=lambda x: x.get("name", "").lower())
    elif sort_by == "Stock: High to Low":
        filtered_products.sort(key=lambda x: x.get("stock", 0), reverse=True)
    
    # Display products
    display_product_grid(filtered_products, cols=3, show_add_to_cart=True)
else:
    # Enhanced "not found" message
    if search_query:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 2rem; background-color: #f8f9fa; border-radius: 12px; margin: 2rem 0;">
            <h3 style="color: #6c757d; margin-bottom: 1rem;">Not Available at the Moment</h3>
            <p style="color: #6c757d; font-size: 1.1rem; margin-bottom: 0.5rem;">
                We couldn't find any products matching "<strong>{}</strong>"
            </p>
            <p style="color: #999; font-size: 0.95rem;">
                Try searching with different keywords or adjust your filters.
            </p>
        </div>
        """.format(search_query), unsafe_allow_html=True)
        
        # Suggestions
        st.markdown("### Suggestions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Clear Search", use_container_width=True):
                st.session_state.current_search = ""
                st.rerun()
        with col2:
            if st.button("Clear All Filters", use_container_width=True):
                st.session_state.current_search = ""
                st.rerun()
        with col3:
            if st.button("View All Products", use_container_width=True):
                st.session_state.current_search = ""
                st.rerun()
    else:
        st.info("Enter a search term or adjust your filters to find products.")
        
        # Show all products when no search query
        if all_products:
            st.write(f"**Total Products Available:** {len(all_products)}")
            st.caption("Start typing in the search box to filter products")

# Quick stats
with st.sidebar:
    st.divider()
    st.write(f"**Total Products:** {len(all_products)}")
    st.write(f"**Filtered Results:** {len(filtered_products)}")

