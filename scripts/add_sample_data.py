"""
Script to add sample products for testing LiveMART.
Run this script once to populate the database with sample products.
"""
from utils.database import save_product, get_users
from datetime import datetime, timedelta

def add_sample_products():
    """Add sample products for testing."""
    users = get_users()
    
    # Find retailer and wholesaler users
    retailer = None
    wholesaler = None
    
    for user in users:
        if user.get("role") == "retailer" and not retailer:
            retailer = user
        elif user.get("role") == "wholesaler" and not wholesaler:
            wholesaler = user
    
    if not retailer:
        print("No retailer found. Please create a retailer account first.")
        return
    
    if not wholesaler:
        print("No wholesaler found. Please create a wholesaler account first.")
        return
    
    # Sample products for retailer
    retailer_products = [
        {
            "name": "Wireless Bluetooth Headphones",
            "category": "Electronics",
            "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life.",
            "price": 2999.00,
            "stock": 50,
            "seller_id": retailer.get("user_id"),
            "seller_type": "retailer",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&h=500&fit=crop"
        },
        {
            "name": "Smart Watch Pro",
            "category": "Electronics",
            "description": "Feature-rich smartwatch with fitness tracking, heart rate monitor, and GPS.",
            "price": 8999.00,
            "stock": 30,
            "seller_id": retailer.get("user_id"),
            "seller_type": "retailer",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&h=500&fit=crop"
        },
        {
            "name": "Cotton T-Shirt",
            "category": "Clothing",
            "description": "Comfortable 100% cotton t-shirt, available in multiple colors.",
            "price": 499.00,
            "stock": 100,
            "seller_id": retailer.get("user_id"),
            "seller_type": "retailer",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop"
        },
        {
            "name": "Running Shoes",
            "category": "Footwear",
            "description": "Lightweight running shoes with cushioned sole and breathable mesh upper.",
            "price": 2499.00,
            "stock": 40,
            "seller_id": retailer.get("user_id"),
            "seller_type": "retailer",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop"
        },
        {
            "name": "Coffee Maker",
            "category": "Home & Kitchen",
            "description": "Programmable coffee maker with thermal carafe, makes up to 12 cups.",
            "price": 3999.00,
            "stock": 25,
            "seller_id": retailer.get("user_id"),
            "seller_type": "retailer",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1517668808823-f6b4909b0e8a?w=500&h=500&fit=crop"
        }
    ]
    
    # Sample products for wholesaler
    wholesaler_products = [
        {
            "name": "Bulk Electronics Components",
            "category": "Electronics",
            "description": "Assorted electronic components pack - resistors, capacitors, LEDs, and more.",
            "price": 1999.00,
            "stock": 200,
            "seller_id": wholesaler.get("user_id"),
            "seller_type": "wholesaler",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=500&h=500&fit=crop"
        },
        {
            "name": "Wholesale T-Shirt Pack",
            "category": "Clothing",
            "description": "Pack of 10 plain t-shirts, perfect for retail businesses.",
            "price": 2999.00,
            "stock": 50,
            "seller_id": wholesaler.get("user_id"),
            "seller_type": "wholesaler",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=500&h=500&fit=crop"
        },
        {
            "name": "Bulk Coffee Beans",
            "category": "Food & Beverages",
            "description": "Premium coffee beans, 5kg pack, ideal for cafes and restaurants.",
            "price": 4999.00,
            "stock": 30,
            "seller_id": wholesaler.get("user_id"),
            "seller_type": "wholesaler",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop"
        },
        {
            "name": "Office Supplies Bundle",
            "category": "Office Supplies",
            "description": "Complete office supplies bundle - pens, notebooks, folders, and more.",
            "price": 1499.00,
            "stock": 75,
            "seller_id": wholesaler.get("user_id"),
            "seller_type": "wholesaler",
            "availability_date": datetime.now().strftime("%Y-%m-%d"),
            "image_url": "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=500&h=500&fit=crop"
        }
    ]
    
    # Add retailer products
    print("Adding retailer products...")
    for product in retailer_products:
        if save_product(product):
            print(f"✓ Added: {product['name']}")
        else:
            print(f"✗ Failed to add: {product['name']}")
    
    # Add wholesaler products
    print("\nAdding wholesaler products...")
    for product in wholesaler_products:
        if save_product(product):
            print(f"✓ Added: {product['name']}")
        else:
            print(f"✗ Failed to add: {product['name']}")
    
    print("\n✅ Sample products added successfully!")
    print(f"Retailer: {retailer.get('name')} ({retailer.get('email')})")
    print(f"Wholesaler: {wholesaler.get('name')} ({wholesaler.get('email')})")

if __name__ == "__main__":
    add_sample_products()

