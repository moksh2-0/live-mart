import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.database import get_product_by_id
from utils.feedback import (
    display_product_feedbacks, submit_feedback, can_submit_feedback,
    get_product_average_rating, get_product_rating_count
)
from utils.recommendations import get_similar_products
from components.product_cards import add_to_cart

st.set_page_config(page_title="LiveMART - Product Detail", page_icon=None, layout="wide")

# Require authentication
require_auth("customer")

user = get_current_user()

# Get product_id from query params or session state
product_id = st.query_params.get("product_id") or st.session_state.get("view_product_id")

if not product_id:
    st.error("Product not found. Please select a product to view.")
    if st.button("Back to Dashboard"):
        st.switch_page("pages/2_Customer_Dashboard.py")
else:
    product = get_product_by_id(product_id)
    
    if not product:
        st.error("Product not found.")
        if st.button("Back to Dashboard"):
            st.switch_page("pages/2_Customer_Dashboard.py")
    else:
        # Product details
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Product image
            image_url = product.get('image_url', '')
            if not image_url or not image_url.startswith('http'):
                image_url = 'https://via.placeholder.com/400x500/E8E8E8/999999?text=No+Image'
            
            st.image(image_url, use_container_width=True)
        
        with col2:
            st.title(product.get('name', 'Unnamed Product'))
            
            # Rating and review count
            avg_rating = get_product_average_rating(product_id)
            rating_count = get_product_rating_count(product_id)
            
            if rating_count > 0:
                st.markdown(f"**Rating:** {avg_rating:.1f}/5 ({rating_count} review{'s' if rating_count > 1 else ''})")
            else:
                st.markdown("**No reviews yet**")
            
            st.markdown(f"**Category:** {product.get('category', 'N/A')}")
            
            # Retailer/Seller information
            seller_id = product.get('seller_id')
            if seller_id:
                from utils.database import get_user_by_id
                seller = get_user_by_id(seller_id)
                if seller:
                    seller_name = seller.get('name', 'Unknown Seller')
                    seller_type = product.get('seller_type', '').lower()
                    seller_type_display = 'Retailer' if seller_type == 'retailer' else 'Wholesaler' if seller_type == 'wholesaler' else 'Seller'
                    st.markdown(f"**{seller_type_display}:** {seller_name}")
            
            st.markdown(f"**Price:** ₹{product.get('price', 0):,.2f}")
            st.markdown(f"**Stock:** {product.get('stock', 0)} units")
            
            if product.get('description'):
                st.markdown("---")
                st.subheader("Description")
                st.write(product.get('description'))
            
            st.markdown("---")
            
            # Add to cart section
            col_qty, col_btn = st.columns([1, 2])
            with col_qty:
                quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=product.get("stock", 1),
                    value=1,
                    key="product_detail_qty"
                )
            with col_btn:
                if st.button("Add to Cart", type="primary", use_container_width=True):
                    add_to_cart(product, quantity)
                    st.success(f"Added {quantity} x {product.get('name')} to cart!")
                    st.rerun()
        
        st.markdown("---")
        
        # Check if we came from Orders page with a specific order
        review_order_id = st.session_state.get("review_order_id", "")
        show_review_tab = st.session_state.get("show_review_tab", False)
        
        # Feedback/Reviews section
        if show_review_tab and review_order_id:
            # If coming from Orders page, show review tab first
            tab1, tab2 = st.tabs(["✍️ Write a Review", "📝 Reviews & Feedback"])
            # Show info about the order
            from utils.database import get_order_by_id
            review_order = get_order_by_id(review_order_id)
            if review_order:
                st.info(f"📦 **Reviewing product from Order #{review_order_id[:8]}** - {review_order.get('created_at', '')[:10]}")
            
            # Write Review tab (shown first when coming from Orders)
            with tab1:
                st.subheader("Share Your Experience")
                
                # Check if user can submit feedback
                can_submit, reason = can_submit_feedback(user.get("user_id"), product_id)
                
                if not can_submit:
                    st.info(f"ℹ️ {reason}")
                    st.info("💡 You can leave a review after purchasing and receiving this product.")
                else:
                    with st.form("feedback_form"):
                        st.markdown("#### Rate this Product")
                        
                        # Rating input
                        rating = st.slider(
                            "Rating",
                            min_value=1,
                            max_value=5,
                            value=5,
                            help="Rate this product from 1 to 5 stars"
                        )
                        st.markdown(f"**Rating:** {rating}/5")
                        
                        # Review text
                        review_text = st.text_area(
                            "Your Review",
                            placeholder="Share your experience with this product...",
                            height=150,
                            help="Optional: Write a detailed review"
                        )
                        
                        # Feedback type
                        feedback_type = st.selectbox(
                            "Feedback Type",
                            ["review", "complaint", "query"],
                            help="Select the type of feedback"
                        )
                        
                        # Order is pre-selected (from Orders page)
                        order_id = review_order_id
                        st.info(f"📦 This review will be linked to Order #{review_order_id[:8]}")
                        
                        # Submit button
                        submitted = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)
                        
                        if submitted:
                            if rating < 1 or rating > 5:
                                st.error("Please select a valid rating (1-5 stars)")
                            else:
                                success = submit_feedback(
                                    customer_id=user.get("user_id"),
                                    product_id=product_id,
                                    rating=rating,
                                    review_text=review_text,
                                    feedback_type=feedback_type,
                                    order_id=order_id
                                )
                                
                                if success:
                                    st.success("✅ Thank you for your feedback! Your review has been submitted.")
                                    st.balloons()
                                    # Clear the review flags
                                    if "review_order_id" in st.session_state:
                                        del st.session_state.review_order_id
                                    if "show_review_tab" in st.session_state:
                                        del st.session_state.show_review_tab
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to submit feedback. Please try again.")
            
            # Reviews & Feedback tab
            with tab2:
                display_product_feedbacks(product_id)
        else:
            # Normal flow - not from Orders page
            tab1, tab2 = st.tabs(["📝 Reviews & Feedback", "✍️ Write a Review"])
            
            with tab1:
                display_product_feedbacks(product_id)
            
            with tab2:
                st.subheader("Share Your Experience")
                
                # Check if user can submit feedback
                can_submit, reason = can_submit_feedback(user.get("user_id"), product_id)
                
                if not can_submit:
                    st.info(f"ℹ️ {reason}")
                    st.info("💡 You can leave a review after purchasing and receiving this product.")
                else:
                    with st.form("feedback_form"):
                        st.markdown("#### Rate this Product")
                        
                        # Rating input
                        rating = st.slider(
                            "Rating",
                            min_value=1,
                            max_value=5,
                            value=5,
                            help="Rate this product from 1 to 5 stars"
                        )
                        st.markdown(f"**Rating:** {rating}/5")
                        
                        # Review text
                        review_text = st.text_area(
                            "Your Review",
                            placeholder="Share your experience with this product...",
                            height=150,
                            help="Optional: Write a detailed review"
                        )
                        
                        # Feedback type
                        feedback_type = st.selectbox(
                            "Feedback Type",
                            ["review", "complaint", "query"],
                            help="Select the type of feedback"
                        )
                        
                        # Order selection (optional)
                        from utils.database import get_orders_by_customer
                        orders = get_orders_by_customer(user.get("user_id"))
                        
                        # Filter orders that contain this product and are delivered
                        relevant_orders = []
                        for order in orders:
                            if order.get("status") == "delivered":
                                for item in order.get("items", []):
                                    if item.get("product_id") == product_id:
                                        relevant_orders.append(order)
                                        break
                        
                        order_id = ""
                        if relevant_orders:
                            order_options = [f"Order #{o.get('order_id', '')[:8]} - {o.get('created_at', '')[:10]}" for o in relevant_orders]
                            selected_order = st.selectbox(
                                "Related Order (Optional)",
                                ["None"] + order_options,
                                help="Link this review to a specific order"
                            )
                            if selected_order != "None":
                                order_index = order_options.index(selected_order)
                                order_id = relevant_orders[order_index].get("order_id", "")
                        
                        # Submit button
                        submitted = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)
                        
                        if submitted:
                            if rating < 1 or rating > 5:
                                st.error("Please select a valid rating (1-5 stars)")
                            else:
                                success = submit_feedback(
                                    customer_id=user.get("user_id"),
                                    product_id=product_id,
                                    rating=rating,
                                    review_text=review_text,
                                    feedback_type=feedback_type,
                                    order_id=order_id
                                )
                                
                                if success:
                                    st.success("✅ Thank you for your feedback! Your review has been submitted.")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to submit feedback. Please try again.")
        
        # Similar/Recommended Products Section
        st.markdown("---")
        similar_products = get_similar_products(product_id, limit=4)
        
        if similar_products:
            st.markdown('<h2 style="margin-bottom: 2rem; font-size: 2rem; font-weight: 700;">🛍️ You May Also Like</h2>', unsafe_allow_html=True)
            st.caption("Similar products you might be interested in")
            
            cols_per_row = 4
            for i in range(0, len(similar_products), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(similar_products):
                        similar_product = similar_products[i + j]
                        with col:
                            image_url = similar_product.get('image_url', '')
                            if not image_url or not image_url.startswith('http'):
                                image_url = 'https://via.placeholder.com/200x250/E8E8E8/999999?text=No+Image'
                            
                            st.markdown(f"""
                            <div class="product-card" style="margin-bottom: 1rem; cursor: pointer;">
                                <div class="product-image-container">
                                    <img src="{image_url}" 
                                         alt="{similar_product.get('name', 'Product')}" 
                                         class="product-image" 
                                         style="width: 100%; height: 200px; object-fit: cover; border-radius: 12px 12px 0 0;" />
                                </div>
                                <div class="product-info" style="padding: 1rem;">
                                    <div class="product-name" style="font-size: 1rem;">{similar_product.get('name', 'Unnamed Product')}</div>
                                    <div class="product-price" style="font-size: 1.2rem;">₹{similar_product.get('price', 0):,.2f}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("View", key=f"similar_view_{similar_product.get('product_id')}", use_container_width=True):
                                st.session_state.view_product_id = similar_product.get('product_id')
                                st.switch_page("pages/8_Product_Detail.py")
        
        # Back button
        st.markdown("---")
        if st.button("← Back to Products", use_container_width=True):
            st.switch_page("pages/2_Customer_Dashboard.py")

