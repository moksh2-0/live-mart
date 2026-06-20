"""
Email Service Utility
Supports multiple email providers: Gmail SMTP, SendGrid, AWS SES, etc.
Currently configured for Gmail SMTP (easiest to set up)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
import streamlit as st

# Email configuration - can be set via environment variables or config file
def get_email_config():
    """Get email configuration from environment variables or config."""
    # Check environment variables first
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL', '')
    sender_password = os.getenv('SENDER_PASSWORD', '')  # Gmail App Password
    
    # Check Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'email' in st.secrets:
            smtp_server = st.secrets.email.get('smtp_server', smtp_server)
            smtp_port = st.secrets.email.get('smtp_port', smtp_port)
            sender_email = st.secrets.email.get('sender_email', sender_email)
            sender_password = st.secrets.email.get('sender_password', sender_password)
    except:
        pass
    
    # Check config file
    try:
        from config_email import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
        return {
            'smtp_server': SMTP_SERVER,
            'smtp_port': SMTP_PORT,
            'sender_email': SENDER_EMAIL,
            'sender_password': SENDER_PASSWORD
        }
    except ImportError:
        pass
    
    return {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'sender_email': sender_email,
        'sender_password': sender_password
    }

def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> Tuple[bool, str]:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
    
    Returns:
        (success: bool, message: str)
    """
    config = get_email_config()
    
    # Check if email is configured
    if not config.get('sender_email') or not config.get('sender_password'):
        # Return mock mode
        print(f"[MOCK EMAIL] To: {to_email}")
        print(f"[MOCK EMAIL] Subject: {subject}")
        print(f"[MOCK EMAIL] Body: {body}")
        return False, "Email not configured. Running in mock mode."
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config['sender_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add plain text and HTML parts
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()  # Enable encryption
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True, "Email sent successfully"
    
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Check your email and app password."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def send_otp_email(email: str, otp: str, purpose: str = "verification") -> Tuple[bool, str]:
    """
    Send OTP via email.
    
    Args:
        email: Recipient email
        otp: 6-digit OTP code
        purpose: Purpose of OTP (verification, login, etc.)
    
    Returns:
        (success: bool, message: str)
    """
    subject = f"Your LiveMART {purpose.title()} OTP"
    
    body = f"""
Hello,

Your OTP for {purpose} is: {otp}

This OTP is valid for 10 minutes.

If you didn't request this OTP, please ignore this email.

Best regards,
LiveMART Team
    """
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">LiveMART {purpose.title()} OTP</h2>
                <p>Hello,</p>
                <p>Your OTP for {purpose} is:</p>
                <div style="background-color: #f8f9fa; border: 2px solid #28a745; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #28a745; margin: 0; font-size: 2.5rem; letter-spacing: 5px;">{otp}</h1>
                </div>
                <p>This OTP is valid for 10 minutes.</p>
                <p style="color: #666; font-size: 0.9rem;">If you didn't request this OTP, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 0.8rem;">Best regards,<br>LiveMART Team</p>
            </div>
        </body>
    </html>
    """
    
    return send_email(email, subject, body, html_body)

def send_order_confirmation_email(email: str, customer_name: str, order_id: str, order_details: dict) -> Tuple[bool, str]:
    """Send order confirmation email."""
    subject = f"Order Confirmation - #{order_id[:8]}"
    
    items_html = ""
    for item in order_details.get('items', []):
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{item.get('name', 'Product')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 0)}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">₹{item.get('price', 0):.2f}</td>
        </tr>
        """
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">Order Confirmation</h2>
                <p>Dear {customer_name},</p>
                <p>Thank you for your order! Your order has been confirmed.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Order ID:</strong> #{order_id[:8]}</p>
                    <p><strong>Total Amount:</strong> ₹{order_details.get('total_amount', 0):.2f}</p>
                    <p><strong>Estimated Delivery:</strong> {order_details.get('estimated_delivery_date', '5-7 business days')}</p>
                </div>
                
                <h3>Order Items:</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Item</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">Quantity</th>
                            <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <p style="margin-top: 20px;">You'll receive real-time updates about your order status.</p>
                <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART Team</p>
            </div>
        </body>
    </html>
    """
    
    body = f"""
Dear {customer_name},

Thank you for your order! Your order has been confirmed.

Order ID: #{order_id[:8]}
Total Amount: ₹{order_details.get('total_amount', 0):.2f}
Estimated Delivery: {order_details.get('estimated_delivery_date', '5-7 business days')}

You'll receive real-time updates about your order status.

Best regards,
LiveMART Team
    """
    
    return send_email(email, subject, body, html_body)

def send_order_status_update_email(email: str, customer_name: str, order_id: str, status: str) -> Tuple[bool, str]:
    """Send order status update email."""
    status_messages = {
        "confirmed": "Your order has been confirmed and is being prepared!",
        "processing": "Your order is now being processed.",
        "shipped": "Great news! Your order has been shipped and is on its way.",
        "delivered": "Your order has been delivered successfully!"
    }
    
    message = status_messages.get(status, f"Your order status has been updated to: {status}")
    subject = f"Order #{order_id[:8]} Status Update"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #007bff;">Order Status Update</h2>
                <p>Dear {customer_name},</p>
                <p>{message}</p>
                <div style="background-color: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; border-radius: 4px; margin: 20px 0;">
                    <p><strong>Order ID:</strong> #{order_id[:8]}</p>
                    <p><strong>Status:</strong> {status.title()}</p>
                </div>
                <p>Track your order in your dashboard.</p>
                <p style="color: #666; font-size: 0.9rem;">Best regards,<br>LiveMART Team</p>
            </div>
        </body>
    </html>
    """
    
    body = f"""
Dear {customer_name},

{message}

Order ID: #{order_id[:8]}
Status: {status.title()}

Track your order in your dashboard.

Best regards,
LiveMART Team
    """
    
    return send_email(email, subject, body, html_body)

def send_delivery_confirmation_email(email: str, customer_name: str, order_id: str, order_details: dict) -> Tuple[bool, str]:
    """Send delivery confirmation email."""
    subject = f"Order #{order_id[:8]} - Delivered Successfully!"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">Your Order Has Been Delivered!</h2>
                <p>Dear {customer_name},</p>
                <p>Great news! Your order has been delivered successfully.</p>
                <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; border-radius: 4px; margin: 20px 0;">
                    <p><strong>Order ID:</strong> #{order_id[:8]}</p>
                    <p><strong>Total Amount:</strong> ₹{order_details.get('total_amount', 0):.2f}</p>
                    <p><strong>Delivery Date:</strong> {order_details.get('delivery_date', 'Today')}</p>
                </div>
                <p>We hope you're satisfied with your purchase! Please leave a review if you'd like.</p>
                <p style="color: #666; font-size: 0.9rem;">Thank you for shopping with LiveMART!<br>Best regards,<br>LiveMART Team</p>
            </div>
        </body>
    </html>
    """
    
    body = f"""
Dear {customer_name},

Great news! Your order has been delivered successfully.

Order ID: #{order_id[:8]}
Total Amount: ₹{order_details.get('total_amount', 0):.2f}
Delivery Date: {order_details.get('delivery_date', 'Today')}

We hope you're satisfied with your purchase!

Thank you for shopping with LiveMART!
Best regards,
LiveMART Team
    """
    
    return send_email(email, subject, body, html_body)

