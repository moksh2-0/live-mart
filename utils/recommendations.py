"""
Product Recommendations System
Provides personalized recommendations based on customer order history
"""
from typing import List, Dict, Any
from utils.database import (
    get_orders_by_customer, get_products, get_product_by_id,
    get_products_by_seller
)

def get_customer_order_history(customer_id: str) -> List[Dict[str, Any]]:
    """Get all orders for a customer."""
    orders = get_orders_by_customer(customer_id)
    return orders

def get_products_customer_has_bought(customer_id: str) -> List[str]:
    """Get list of product IDs that customer has purchased."""
    orders = get_orders_by_customer(customer_id)
    purchased_product_ids = []
    
    for order in orders:
        # Only count delivered or confirmed orders
        if order.get("status") in ["confirmed", "processing", "shipped", "delivered"]:
            for item in order.get("items", []):
                product_id = item.get("product_id")
                if product_id and product_id not in purchased_product_ids:
                    purchased_product_ids.append(product_id)
    
    return purchased_product_ids

def get_customer_preferred_categories(customer_id: str) -> Dict[str, int]:
    """Get categories customer has bought from, with purchase counts."""
    orders = get_orders_by_customer(customer_id)
    category_counts = {}
    
    for order in orders:
        if order.get("status") in ["confirmed", "processing", "shipped", "delivered"]:
            for item in order.get("items", []):
                product = get_product_by_id(item.get("product_id"))
                if product:
                    category = product.get("category", "Uncategorized")
                    category_counts[category] = category_counts.get(category, 0) + item.get("quantity", 1)
    
    return category_counts

def get_customer_preferred_sellers(customer_id: str) -> List[str]:
    """Get seller IDs that customer has bought from frequently."""
    orders = get_orders_by_customer(customer_id)
    seller_counts = {}
    
    for order in orders:
        if order.get("status") in ["confirmed", "processing", "shipped", "delivered"]:
            for item in order.get("items", []):
                product = get_product_by_id(item.get("product_id"))
                if product:
                    seller_id = product.get("seller_id")
                    if seller_id:
                        seller_counts[seller_id] = seller_counts.get(seller_id, 0) + item.get("quantity", 1)
    
    # Return top 3 sellers
    sorted_sellers = sorted(seller_counts.items(), key=lambda x: x[1], reverse=True)
    return [seller_id for seller_id, count in sorted_sellers[:3]]

def get_customer_price_range(customer_id: str) -> tuple[float, float]:
    """Get the price range of products customer usually buys."""
    orders = get_orders_by_customer(customer_id)
    prices = []
    
    for order in orders:
        if order.get("status") in ["confirmed", "processing", "shipped", "delivered"]:
            for item in order.get("items", []):
                price = item.get("price", 0)
                if price > 0:
                    prices.append(price)
    
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = max(0, avg_price * 0.5)  # 50% below average
        max_price = avg_price * 2.0  # 200% above average
        return (min_price, max_price)
    
    # Default range if no purchase history
    return (0.0, 10000.0)

def get_recommended_products(customer_id: str, limit: int = 6) -> List[Dict[str, Any]]:
    """
    Get recommended products for a customer based on their order history.
    
    Strategy:
    1. Recommend products from categories they've bought from
    2. Recommend products from sellers they've bought from
    3. Recommend products in similar price range
    4. Exclude products they've already bought
    """
    all_products = get_products()
    
    # Get customer data
    purchased_product_ids = get_products_customer_has_bought(customer_id)
    preferred_categories = get_customer_preferred_categories(customer_id)
    preferred_sellers = get_customer_preferred_sellers(customer_id)
    min_price, max_price = get_customer_price_range(customer_id)
    
    # Score products for recommendation
    product_scores = {}
    
    for product in all_products:
        product_id = product.get("product_id")
        
        # Skip products customer has already bought
        if product_id in purchased_product_ids:
            continue
        
        # Skip out of stock products
        if product.get("stock", 0) <= 0:
            continue
        
        score = 0
        
        # Category match (weight: 3 points per purchase in category)
        category = product.get("category", "")
        if category in preferred_categories:
            score += preferred_categories[category] * 3
        
        # Seller match (weight: 2 points if from preferred seller)
        seller_id = product.get("seller_id")
        if seller_id in preferred_sellers:
            score += 2
        
        # Price range match (weight: 1 point if in range)
        price = product.get("price", 0)
        if min_price <= price <= max_price:
            score += 1
        
        # Stock availability bonus (prefer items in stock)
        if product.get("stock", 0) > 5:
            score += 0.5
        
        product_scores[product_id] = {
            'product': product,
            'score': score
        }
    
    # Sort by score and return top recommendations
    sorted_products = sorted(
        product_scores.values(),
        key=lambda x: x['score'],
        reverse=True
    )
    
    # Return top recommendations
    recommended = [item['product'] for item in sorted_products[:limit]]
    
    # If not enough recommendations, add popular products from any category
    if len(recommended) < limit:
        remaining = limit - len(recommended)
        for product in all_products:
            if len(recommended) >= limit:
                break
            if product.get("product_id") not in purchased_product_ids:
                if product.get("product_id") not in [p.get("product_id") for p in recommended]:
                    if product.get("stock", 0) > 0:
                        recommended.append(product)
    
    return recommended

def get_similar_products(product_id: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Get products similar to a given product.
    Based on category, seller, and price range.
    """
    product = get_product_by_id(product_id)
    if not product:
        return []
    
    all_products = get_products()
    similar = []
    
    category = product.get("category")
    seller_id = product.get("seller_id")
    price = product.get("price", 0)
    price_range = (price * 0.7, price * 1.3)  # ±30% price range
    
    for p in all_products:
        if p.get("product_id") == product_id:
            continue  # Skip the same product
        
        if p.get("stock", 0) <= 0:
            continue  # Skip out of stock
        
        similarity_score = 0
        
        # Same category (high priority)
        if p.get("category") == category:
            similarity_score += 3
        
        # Same seller (medium priority)
        if p.get("seller_id") == seller_id:
            similarity_score += 2
        
        # Similar price (low priority)
        p_price = p.get("price", 0)
        if price_range[0] <= p_price <= price_range[1]:
            similarity_score += 1
        
        if similarity_score > 0:
            similar.append((p, similarity_score))
    
    # Sort by similarity and return top results
    similar.sort(key=lambda x: x[1], reverse=True)
    return [p for p, score in similar[:limit]]

def get_trending_products(limit: int = 6) -> List[Dict[str, Any]]:
    """Get trending/popular products based on order frequency."""
    from utils.database import get_orders
    
    all_products = get_products()
    product_order_counts = {}
    
    # Count how many times each product appears in orders
    orders = get_orders()
    for order in orders:
        if order.get("status") in ["confirmed", "processing", "shipped", "delivered"]:
            for item in order.get("items", []):
                product_id = item.get("product_id")
                product_order_counts[product_id] = product_order_counts.get(product_id, 0) + item.get("quantity", 1)
    
    # Sort products by order count
    products_with_orders = []
    for product in all_products:
        product_id = product.get("product_id")
        if product.get("stock", 0) > 0:
            order_count = product_order_counts.get(product_id, 0)
            products_with_orders.append((product, order_count))
    
    products_with_orders.sort(key=lambda x: x[1], reverse=True)
    return [p for p, count in products_with_orders[:limit]]

