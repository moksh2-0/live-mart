import random
import streamlit as st
import time
from utils.orders import update_order_status, update_stock_after_order
from utils.database import update_order

def process_mock_payment(order_id: str, amount: float, payment_method: str = "online", card_details: dict = None):
    """
    Simulate realistic payment processing.
    Returns (success: bool, transaction_id: str, error_message: str)
    """
    # Simulate payment processing delay (1-3 seconds)
    processing_time = random.uniform(1.0, 3.0)
    time.sleep(processing_time)
    
    # Realistic payment success rate (92% success, 8% failure)
    success = random.random() > 0.08
    
    if success:
        # Generate realistic transaction ID
        transaction_id = f"TXN{random.randint(100000000, 999999999)}"
        
        # Update order payment status
        update_order(order_id, {
            "payment_status": "completed",
            "transaction_id": transaction_id,
            "payment_date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Check for restock notifications before confirming order
        from utils.retailer_notifications import check_and_send_restock_notifications
        
        # Check if retailer needs to restock (stock = 0 but wholesaler has stock)
        check_and_send_restock_notifications(order_id)
        
        # If payment is successful, confirm the order
        update_order_status(order_id, "confirmed")
        
        # Update stock
        update_stock_after_order(order_id)
        
        return True, transaction_id, None
    else:
        # Realistic failure reasons
        failure_reasons = [
            "Insufficient funds",
            "Card declined by bank",
            "Transaction timeout",
            "Invalid card details",
            "Network error. Please try again"
        ]
        error_message = random.choice(failure_reasons)
        return False, None, error_message

def validate_card_number(card_number: str) -> bool:
    """Validate card number format. For demo purposes, accepts any 13-19 digit number."""
    # Remove spaces and non-digits
    card_number = ''.join(filter(str.isdigit, card_number))
    
    # Check length (13-19 digits for valid card numbers)
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Check if all digits (should already be true after filter, but double-check)
    if not card_number.isdigit():
        return False
    
    # For demo/mock payment system, accept any valid length card number
    # In production, you would use Luhn algorithm validation
    # For now, we'll accept any 13-19 digit number for easier testing
    return True
    
    # Optional: Uncomment below for strict Luhn algorithm validation
    # def luhn_check(card_num):
    #     digits = [int(d) for d in str(card_num)]
    #     digits.reverse()
    #     checksum = 0
    #     for i, digit in enumerate(digits):
    #         if i % 2 == 1:  # Even positions (0-indexed)
    #             doubled = digit * 2
    #             checksum += doubled if doubled < 10 else doubled - 9
    #         else:  # Odd positions
    #             checksum += digit
    #     return checksum % 10 == 0
    # return luhn_check(card_number)

def validate_expiry_date(expiry: str):
    """Validate expiry date format MM/YY. Returns (is_valid: bool, error_message: str)."""
    if not expiry or len(expiry) != 5:
        return False, "Invalid format. Use MM/YY"
    
    try:
        month, year = expiry.split('/')
        month = int(month)
        year = int(year)
        
        if month < 1 or month > 12:
            return False, "Invalid month (1-12)"
        
        # Check if card is expired
        current_year = int(time.strftime("%y"))
        current_month = int(time.strftime("%m"))
        
        if year < current_year or (year == current_year and month < current_month):
            return False, "Card has expired"
        
        return True, "Valid"
    except:
        return False, "Invalid format. Use MM/YY"

def validate_cvv(cvv: str) -> bool:
    """Validate CVV (3 or 4 digits)."""
    return cvv.isdigit() and (len(cvv) == 3 or len(cvv) == 4)

def display_payment_form(order_id: str, amount: float, payment_method: str = "online"):
    """Display realistic mock payment form."""
    st.subheader("💳 Payment")
    
    # Payment summary
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Order ID:** `{order_id[:8]}`")
        st.write(f"**Amount:** ₹{amount:,.2f}")
    with col2:
        st.write(f"**Payment Method:** {payment_method.title()}")
        st.write(f"**Status:** Pending")
    
    st.divider()
    
    if payment_method == "online":
        st.markdown("### Secure Payment Gateway")
        st.info("🔒 Your payment is secured with 256-bit SSL encryption")
        
        # Show test card numbers for demo
        with st.expander("💡 Test Card Numbers (for demo)", expanded=False):
            st.markdown("""
            **For demo purposes, you can use any 13-19 digit card number.**
            
            **Example test cards:**
            - `4111 1111 1111 1111` (16 digits)
            - `5555 5555 5555 4444` (16 digits)
            - `1234 5678 9012 3456` (16 digits)
            
            **Expiry:** Any future date (e.g., 12/25, 06/26)  
            **CVV:** Any 3-4 digits (e.g., 123, 4567)
            """)
        
        with st.form("payment_form", clear_on_submit=False):
            st.markdown("#### Card Details")
            
            # Card number with formatting
            card_number = st.text_input(
                "Card Number *",
                placeholder="1234 5678 9012 3456",
                max_chars=19,
                help="Enter your 16-digit card number"
            )
            
            # Expiry and CVV in same row
            col_exp, col_cvv = st.columns(2)
            with col_exp:
                expiry = st.text_input(
                    "Expiry Date (MM/YY) *",
                    placeholder="12/25",
                    max_chars=5,
                    help="Format: MM/YY"
                )
            with col_cvv:
                cvv = st.text_input(
                    "CVV *",
                    placeholder="123",
                    max_chars=4,
                    type="password",
                    help="3 or 4 digit security code"
                )
            
            # Cardholder name
            cardholder_name = st.text_input(
                "Cardholder Name *",
                placeholder="John Doe",
                help="Name as it appears on your card"
            )
            
            # Billing address (optional but realistic)
            st.markdown("#### Billing Address")
            billing_address = st.text_area(
                "Billing Address",
                placeholder="Enter your billing address (optional)",
                height=80
            )
            
            # Payment button
            st.divider()
            col_btn, col_info = st.columns([2, 1])
            with col_btn:
                submit_payment = st.form_submit_button(
                    "🔒 Pay ₹{:.2f}".format(amount),
                    type="primary",
                    use_container_width=True
                )
            with col_info:
                st.caption("💡 This is a demo payment gateway")
            
            if submit_payment:
                # Validation
                errors = []
                
                if not card_number:
                    errors.append("Card number is required")
                elif not validate_card_number(card_number):
                    errors.append("Invalid card number")
                
                if not expiry:
                    errors.append("Expiry date is required")
                else:
                    valid, msg = validate_expiry_date(expiry)
                    if not valid:
                        errors.append(f"Expiry date: {msg}")
                
                if not cvv:
                    errors.append("CVV is required")
                elif not validate_cvv(cvv):
                    errors.append("Invalid CVV (must be 3 or 4 digits)")
                
                if not cardholder_name:
                    errors.append("Cardholder name is required")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                    return False
                
                # Process payment
                with st.spinner("Processing payment... Please wait"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate payment processing steps
                    steps = [
                        "Validating card details...",
                        "Connecting to bank...",
                        "Processing transaction...",
                        "Verifying payment..."
                    ]
                    
                    for i, step in enumerate(steps):
                        status_text.text(step)
                        progress_bar.progress((i + 1) / len(steps))
                        time.sleep(0.5)
                    
                    # Process payment
                    card_details = {
                        'card_number': card_number.replace(" ", ""),
                        'expiry': expiry,
                        'cvv': cvv,
                        'cardholder': cardholder_name
                    }
                    
                    success, transaction_id, error_msg = process_mock_payment(
                        order_id, amount, payment_method, card_details
                    )
                    
                    progress_bar.progress(1.0)
                    
                    if success:
                        status_text.success("✅ Payment processed successfully!")
                        st.success(f"**Payment Successful!**")
                        st.balloons()
                        
                        # Payment details
                        st.markdown("---")
                        st.markdown("### Payment Receipt")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Transaction ID:** `{transaction_id}`")
                            st.write(f"**Order ID:** `{order_id[:8]}`")
                            st.write(f"**Amount Paid:** ₹{amount:,.2f}")
                        with col2:
                            st.write(f"**Payment Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**Payment Method:** Card ending in `{card_number[-4:]}`")
                            st.write(f"**Status:** ✅ Completed")
                        
                        # Order success message - this will be displayed in Cart.py after payment_success returns True
                        st.markdown("---")
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                            <h2 style="color: white; margin-bottom: 0.5rem;">🎉 Payment Successful!</h2>
                            <p style="color: white; margin: 0;">Your order will be processed shortly.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("📧 You will receive an order confirmation email with tracking details. You'll also receive real-time status updates via email as your order progresses.")
                        
                        return True
                    else:
                        status_text.error("❌ Payment failed")
                        st.error(f"**Payment Failed:** {error_msg}")
                        st.info("💡 Please check your card details and try again, or contact your bank.")
                        return False
    else:
        # Offline payment
        st.info("💵 **Cash on Delivery / Offline Payment**")
        st.write("You can complete the payment when your order is delivered.")
        
        if st.button("Confirm Offline Payment", type="primary", use_container_width=True):
            # Mark as pending - will be confirmed later
            update_order(order_id, {
                "payment_status": "pending",
                "payment_method": "offline"
            })
            st.success("✅ Order placed successfully!")
            st.info("Payment will be collected at the time of delivery.")
            return True
    
    return False

def simulate_payment_gateway(order_id: str, amount: float) -> dict:
    """Simulate a payment gateway response."""
    success = random.random() > 0.08  # 92% success rate
    
    response = {
        "success": success,
        "transaction_id": f"TXN{random.randint(100000000, 999999999)}" if success else None,
        "message": "Payment successful" if success else "Payment failed",
        "amount": amount,
        "order_id": order_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return response
