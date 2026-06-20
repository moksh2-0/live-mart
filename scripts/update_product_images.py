"""
Script to update existing products with image URLs.
Run this to add images to products that don't have them.
"""
from utils.database import get_products, update_product

def update_product_images():
    """Update products with image URLs based on category."""
    products = get_products()
    
    # Image mapping by category/name
    image_map = {
        "Wireless Bluetooth Headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&h=500&fit=crop",
        "Smart Watch Pro": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&h=500&fit=crop",
        "Cotton T-Shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop",
        "Running Shoes": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop",
        "Coffee Maker": "https://images.unsplash.com/photo-1517668808823-f6b4909b0e8a?w=500&h=500&fit=crop",
        "Bulk Electronics Components": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=500&h=500&fit=crop",
        "Wholesale T-Shirt Pack": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=500&h=500&fit=crop",
        "Bulk Coffee Beans": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop",
        "Office Supplies Bundle": "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=500&h=500&fit=crop",
    }
    
    # Category-based fallback images
    category_images = {
        "Electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=500&h=500&fit=crop",
        "Clothing": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=500&h=500&fit=crop",
        "Footwear": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop",
        "Food & Beverages": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&h=500&fit=crop",
        "Home & Kitchen": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop",
        "Office Supplies": "https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=500&h=500&fit=crop",
    }
    
    updated_count = 0
    for product in products:
        product_name = product.get("name", "")
        current_image = product.get("image_url", "")
        
        # Skip if already has an image URL
        if current_image and current_image.startswith("http"):
            continue
        
        # Try to get image from name mapping
        image_url = image_map.get(product_name)
        
        # Fallback to category-based image
        if not image_url:
            category = product.get("category", "")
            image_url = category_images.get(category)
        
        # Update product if we found an image
        if image_url:
            if update_product(product.get("product_id"), {"image_url": image_url}):
                print(f"✓ Updated: {product_name}")
                updated_count += 1
            else:
                print(f"✗ Failed to update: {product_name}")
    
    print(f"\n✅ Updated {updated_count} product(s) with images!")

if __name__ == "__main__":
    update_product_images()

