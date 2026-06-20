"""
Utility script to remove products that were added directly by retailers.
This script removes all retailer products that don't have a corresponding 
wholesaler product with the same product_id (indicating they weren't sourced 
from a wholesaler).

Run this script to clean up products added directly by retailers.
"""
from utils.database import read_json, write_json, get_products

def remove_retailer_added_products():
    """
    Remove all products that were added directly by retailers.
    Keeps only products from wholesalers, and retailer products that have 
    a matching wholesaler product (indicating they were sourced from wholesalers).
    """
    # Read products directly to get full product data
    from utils.database import DATA_DIR
    import os
    
    filepath = os.path.join(DATA_DIR, "products.json")
    data = read_json("products.json")
    products = data.get("products", [])
    
    # Find all wholesaler product IDs
    wholesaler_product_ids = set()
    for product in products:
        if product.get("seller_type", "").lower() == "wholesaler":
            product_id = product.get("product_id")
            if product_id:
                wholesaler_product_ids.add(product_id)
    
    # Find retailer products that don't have a matching wholesaler product
    retailer_products_to_remove = []
    products_to_keep = []
    
    for product in products:
        if product.get("seller_type", "").lower() == "retailer":
            product_id = product.get("product_id")
            # If this product_id doesn't exist in wholesaler products,
            # it means the retailer added it directly (not sourced from wholesaler)
            if product_id and product_id not in wholesaler_product_ids:
                retailer_products_to_remove.append(product)
            else:
                # Keep retailer products that have matching wholesaler products (sourced from wholesalers)
                products_to_keep.append(product)
        else:
            # Keep all non-retailer products (wholesaler products)
            products_to_keep.append(product)
    
    # Remove the retailer-added products
    removed_count = len(retailer_products_to_remove)
    
    print(f"Found {removed_count} retailer products added directly (not from wholesalers).")
    print(f"Found {len(products_to_keep)} products to keep (wholesalers + retailer products sourced from wholesalers).")
    print("\nRemoving retailer-added products...")
    
    for product in retailer_products_to_remove:
        product_id = product.get("product_id", "Unknown")
        product_name = product.get("name", "Unknown")
        seller_id = product.get("seller_id", "Unknown")
        print(f"  - Removing: {product_name} (Product ID: {product_id[:8] if len(str(product_id)) > 8 else product_id}..., Seller: {seller_id[:8] if len(str(seller_id)) > 8 else seller_id}...)")
    
    # Update products list - keep only products that should be kept
    data["products"] = products_to_keep
    success = write_json("products.json", data)
    
    if success:
        print(f"\n[SUCCESS] Cleanup complete!")
        print(f"   - Removed: {removed_count} retailer products")
        print(f"   - Kept: {len(products_to_keep)} products (wholesalers + retailer products sourced from wholesalers)")
        print(f"\nNote: Only retailer products without matching wholesaler products were removed.")
    else:
        print(f"\n[ERROR] Failed to save changes to products.json")

if __name__ == "__main__":
    print("=" * 60)
    print("Remove Retailer-Added Products Utility")
    print("=" * 60)
    print("\nThis script will remove all products added directly by retailers.")
    print("Products sourced from wholesalers (matching product_id with wholesaler products) will be kept.\n")
    
    # Run automatically without confirmation
    remove_retailer_added_products()

