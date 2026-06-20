# Inventory Management Workflow - LiveMART

## Overview
LiveMART follows a **three-tier inventory system**: **Customer → Retailer → Wholesaler**. Customers always purchase from retailers, and retailers source products from wholesalers when needed. Stock is managed at both retailer and wholesaler levels.

---

## 1. Product Inventory Structure

### 1.1 Product Identification
- Each product has a unique `product_id` across the entire system
- The same `product_id` can exist at both retailer and wholesaler levels
- Example: Product "Coffee Maker" (ID: `abc123`) can be listed by:
  - Retailer A with stock: 50 units
  - Retailer B with stock: 30 units
  - Wholesaler X with stock: 200 units

### 1.2 Stock Aggregation
- **Retailer Stock**: Sum of stock across all retailers who have that product
- **Wholesaler Stock**: Sum of stock across all wholesalers who have that product
- Example: If 3 retailers have "Coffee Maker" with stocks 50, 30, 20 → Retailer Stock = 100 units

### 1.3 Product Display to Customers
- Customers see **one product card** per `product_id`
- Displays:
  - **Retailer Stock**: Aggregated across all retailers (e.g., "Retailer Stock: 100 units")
  - **Wholesaler Stock**: Aggregated across all wholesalers (e.g., "Wholesaler Stock: 200 units")
- If retailer stock = 0 but wholesaler has stock, shows: "Wholesaler Stock: 200 units (available, +3 days delivery)"

---

## 2. Inventory Initial Setup

### 2.1 Wholesaler Adds Product
**Location**: Wholesaler Dashboard → Add Product tab

**Process**:
1. Wholesaler fills product form:
   - Product Name, Category, Description
   - Price, Stock Quantity
   - Image URL
2. System saves product with:
   - `seller_type`: "wholesaler"
   - `seller_id`: Wholesaler's user ID
   - `product_id`: Auto-generated UUID
   - `stock`: Initial stock quantity

**Automatic Actions**:
- If product is **only listed by wholesaler** (no retailer has it):
  - System sends email to **ALL retailers** notifying them of new product
  - Email includes: Product details, suggestion to add to inventory

### 2.2 Retailer Adds Product
**Location**: Retailer Dashboard → Add Product tab

**Process**:
1. Retailer fills product form (same as wholesaler)
2. System saves product with:
   - `seller_type`: "retailer"
   - `seller_id`: Retailer's user ID
   - `product_id`: **Same as wholesaler's product_id** (if adding existing product) or new UUID
   - `stock`: Initial stock quantity

**Note**: Retailer can add:
- Same product as wholesaler (uses same `product_id`)
- New product not available from wholesaler

---

## 3. Customer Order Flow

### 3.1 Customer Places Order
**Location**: Customer Dashboard → Add to Cart → Checkout

**Process**:
1. Customer adds products to cart
2. At checkout, system:
   - Calculates total amount
   - **Assigns order to nearest retailer** with sufficient stock
   - If multiple retailers, selects nearest one
   - If only one retailer, assigns to that retailer

3. Order is created with:
   - `customer_id`: Customer's user ID
   - `seller_id`: Assigned retailer's ID
   - `order_type`: "customer_to_retailer"
   - `status`: "pending"
   - `items`: List of products with quantities

### 3.2 Stock Check During Order Creation
For each product in order:
- System checks:
  - Assigned retailer's stock for that product
  - Wholesaler stock for that product

**Scenarios**:

**Scenario A: Retailer Has Stock**
- Order status: "pending"
- Retailer stock: Decreases after order confirmation
- Delivery time: Based on distance (1-5 days)
- No extra delay

**Scenario B: Retailer Stock = 0, Wholesaler Has Stock**
- Order status: "pending" (initially)
- Order flag: `needs_wholesaler_order` = True
- Delivery time: Base distance + 2 days (wholesaler delay)
- **Email sent to retailer**: "Restock Alert" with product details and wholesaler stock availability

---

## 4. Retailer Order Management

### 4.1 Customer Orders Tab
**Location**: Retailer Dashboard → Customer Orders tab

**What Retailer Sees**:
- All orders from customers assigned to them
- Order status: pending, confirmed, processing, shipped, delivered
- Special status: **"Pending wholesaler order"** (if retailer needs to order from wholesaler)

**Order Statuses**:
- `pending`: Customer order received, retailer needs to process
- `pending wholesaler order`: Retailer needs to order from wholesaler (high priority)
- `confirmed`: Retailer has stock, order confirmed
- `processing`: Order being prepared
- `shipped`: Order dispatched
- `delivered`: Order completed

### 4.2 Order from Wholesaler Tab
**Location**: Retailer Dashboard → Order from Wholesaler tab

**Two Sub-tabs**:

#### Sub-tab 1: Place New Order

**Section A: High Priority Orders (Linked to Customer Orders)**
- Shows customer orders where retailer stock = 0
- Displays:
  - Customer Order ID
  - Customer Name
  - Required products and quantities
- For each product:
  - Shows available wholesalers
  - Shows per-wholesaler pricing
  - Shows stock availability
  - **"Place High Priority Order"** button (matches customer order quantity exactly)

**Section B: All Products from Wholesalers**
- Shows all products available from wholesalers
- **Grouped by product_id**, showing each wholesaler separately
- Displays:
  - Wholesaler name
  - Price per unit (per-wholesaler pricing)
  - Stock available
- Retailer can order any quantity (independent order)

**Section C: Products Only from Retailers**
- Shows products available ONLY from retailers (not from wholesalers)
- Useful for price comparison and inventory insights

#### Sub-tab 2: Order History
- Shows all orders placed by retailer to wholesalers
- Filters:
  - By status: pending, confirmed, processing, shipped, delivered
  - By priority: High Priority, Normal
- Displays:
  - Order ID, Date, Status
  - Wholesaler name
  - Linked customer order ID (if high priority)
  - Items and quantities

### 4.3 Retailer Places Order to Wholesaler

**Process**:

**Case 1: High Priority Order (Linked to Customer Order)**
1. Retailer clicks "Place High Priority Order" in High Priority section
2. System:
   - Verifies quantity matches customer order exactly
   - Checks wholesaler stock availability
   - Creates order with:
     - `order_type`: "retailer_to_wholesaler"
     - `is_high_priority`: True
     - `linked_customer_order_id`: Customer order ID
     - `priority`: "high"
   - **Automatically updates stock**:
     - Decreases wholesaler stock
     - Increases retailer stock (or creates retailer product entry)
   - Updates customer order status: "pending" → **"pending wholesaler order"**
   - Sends email notifications:
     - To wholesaler: "New Order [HIGH PRIORITY - Customer Order Linked]"
     - To retailer: "Order Placed - Stock Updated Successfully"

**Case 2: Independent Order (Inventory Restocking)**
1. Retailer selects product and quantity in "All Products" section
2. System:
   - Checks wholesaler stock
   - Creates order with:
     - `order_type`: "retailer_to_wholesaler"
     - `is_high_priority`: False
     - `linked_customer_order_id`: None
     - `priority`: "normal"
   - **Automatically updates stock**:
     - Decreases wholesaler stock
     - Increases retailer stock
   - Sends email notifications (same as high priority, but without priority flag)

---

## 5. Wholesaler Order Management

### 5.1 Retailer Orders Tab
**Location**: Wholesaler Dashboard → Retailer Orders tab

**What Wholesaler Sees**:
- **Only orders from retailers** (customer orders are filtered out)
- Orders sorted by:
  1. **High Priority first** (linked to customer orders)
  2. Then by date (newest first)

**Display Features**:
- **High Priority Badge**: Orders with `is_high_priority = True` show "[HIGH PRIORITY]"
- **Warning Banner**: Shows count of high priority orders at top
- **Auto-expand**: High priority orders expanded by default
- **Customer Order Details**: For high priority orders, shows:
  - Linked customer order ID
  - Customer name
  - Note: "Please prioritize this order"

### 5.2 Wholesaler Updates Order Status

**Process**:
1. Wholesaler selects new status from dropdown:
   - pending → confirmed → processing → shipped → delivered

2. When status updated to **"confirmed"**:
   - If order is high priority (linked to customer order):
     - Customer order status changes: "pending wholesaler order" → **"pending"**
     - System sends email to retailer and customer about status update
   - Stock has already been updated when order was placed (automatic)

3. Email notifications sent:
   - To retailer: Order status update
   - To customer: If linked to customer order

---

## 6. Automatic Stock Management

### 6.1 Stock Update Rules

**When Retailer Orders from Wholesaler** (Automatic):
1. **Wholesaler Stock**: Decreases by ordered quantity
   ```
   wholesaler_stock_new = wholesaler_stock_old - quantity_ordered
   ```

2. **Retailer Stock**: Increases by ordered quantity
   ```
   If retailer product exists:
     retailer_stock_new = retailer_stock_old + quantity_ordered
   Else:
     Create new retailer product entry with stock = quantity_ordered
   ```

3. **Email Sent**: Confirmation to both parties

**When Customer Order is Confirmed** (After Payment):
1. **Retailer Stock**: Decreases by ordered quantity
   ```
   retailer_stock_new = retailer_stock_old - quantity_ordered
   ```

2. **No direct stock decrease from wholesaler** (already handled when retailer ordered)

### 6.2 Stock Update Timing

**Immediate Updates**:
- ✅ Stock updates happen **instantly** when retailer places order to wholesaler
- ✅ No delivery delay simulation for stock updates
- ✅ Both retailer and wholesaler see updated stock immediately

**Email Notifications**:
- Sent immediately after stock update
- Includes:
  - Order ID
  - Products and quantities
  - Updated stock levels
  - Status information

---

## 7. Status Transition Workflow

### 7.1 Customer Order Status Flow

```
1. Customer Places Order
   ↓
   Status: "pending"
   (Retailer receives order)

2a. If Retailer Has Stock:
   ↓
   Retailer Confirms
   ↓
   Status: "confirmed" → "processing" → "shipped" → "delivered"

2b. If Retailer Stock = 0, Wholesaler Has Stock:
   ↓
   Status: "pending"
   Flag: needs_wholesaler_order = True
   (Email sent to retailer: Restock Alert)
   ↓
   Retailer Places Order to Wholesaler
   ↓
   Status: "pending wholesaler order"
   (Stock automatically updated)
   ↓
   Wholesaler Confirms Order
   ↓
   Status: "pending wholesaler order" → "pending"
   (Back to retailer processing)
   ↓
   Status: "confirmed" → "processing" → "shipped" → "delivered"
```

### 7.2 Retailer-to-Wholesaler Order Status Flow

```
1. Retailer Places Order
   ↓
   Status: "pending"
   (Stock automatically updated)
   (Email sent to wholesaler)
   ↓
2. Wholesaler Confirms
   ↓
   Status: "confirmed" → "processing" → "shipped" → "delivered"
   
   If High Priority:
     - Customer order status also updated
     - Customer receives email notification
```

---

## 8. Email Notification System

### 8.1 Notification Types

**1. Restock Alert (Retailer)**
- **Trigger**: Customer places order, retailer stock = 0, wholesaler has stock
- **Sent to**: Retailer
- **Content**: 
  - Product name, ID
  - Wholesaler stock available
  - Customer order details
  - Note: +3 days delivery delay

**2. New Product Available (All Retailers)**
- **Trigger**: Wholesaler adds product that no retailer has
- **Sent to**: All retailers
- **Content**:
  - Product details
  - Suggestion to add to inventory

**3. High Priority Order Alert (Wholesaler)**
- **Trigger**: Retailer places high priority order (linked to customer order)
- **Sent to**: Wholesaler
- **Content**:
  - Order details
  - Customer order ID
  - Customer name
  - Priority flag

**4. Stock Update Confirmation (Retailer)**
- **Trigger**: Retailer places order to wholesaler
- **Sent to**: Retailer
- **Content**:
  - Order ID
  - Stock updated confirmation
  - Linked customer order (if applicable)

**5. Order Status Update (Customer/Retailer)**
- **Trigger**: Order status changes
- **Sent to**: Customer (for customer orders), Retailer (for retailer orders)
- **Content**: Status update and order details

**6. Delivery Confirmation (Customer)**
- **Trigger**: Order status = "delivered"
- **Sent to**: Customer
- **Content**: Delivery confirmation with order details

---

## 9. Inventory Management Best Practices

### 9.1 For Retailers

**Monitor Stock Levels**:
- Regularly check "Customer Orders" tab for orders requiring wholesaler restocking
- Use "Order from Wholesaler" → "Order History" to track past orders

**Optimize Inventory**:
- Order from wholesalers proactively when stock is low
- Use independent orders for bulk restocking
- Link orders to customer orders only when necessary (high priority)

**Manage Customer Expectations**:
- Be aware of +3 days delivery delay for products needing wholesaler sourcing
- Update order status promptly after receiving from wholesaler

### 9.2 For Wholesalers

**Prioritize Orders**:
- Check for [HIGH PRIORITY] orders first
- Confirm high priority orders quickly to maintain customer satisfaction
- Regular orders can be processed in sequence

**Stock Management**:
- Keep accurate stock levels
- Update product availability promptly
- Notify retailers of new products

### 9.3 For Customers

**Understand Delivery Times**:
- Standard delivery: 1-8 days based on distance
- Wholesaler delay: +3 days if retailer needs to source from wholesaler
- Check estimated delivery date on order confirmation

---

## 10. System Integration Points

### 10.1 Key Functions

**Order Creation** (`utils/orders.py`):
- `create_order()`: Creates customer order, assigns to retailer
- `assign_order_to_retailer()`: Finds nearest retailer with stock

**Retailer Orders** (`utils/retailer_wholesaler_orders.py`):
- `create_retailer_to_wholesaler_order()`: Creates retailer order, updates stock
- `update_stock_for_retailer_order()`: Handles automatic stock updates
- `get_retailer_orders_from_wholesalers()`: Retrieves order history

**Product Aggregation** (`utils/product_aggregation.py`):
- `get_product_stock_info()`: Gets aggregated stock per product_id
- `get_aggregated_products()`: Groups products by product_id
- `find_nearest_retailer_with_stock()`: Finds retailer for order assignment

**Email Notifications** (`utils/retailer_notifications.py`, `utils/email_service.py`):
- `send_restock_notification()`: Alerts retailer to restock
- `send_new_product_notification_to_all_retailers()`: Notifies about new wholesaler products
- `send_retailer_order_notifications()`: Confirms retailer orders

**Database Operations** (`utils/database.py`):
- `save_product()`: Saves product (triggers new product notifications)
- `update_product()`: Updates product (including stock)
- `save_order()`: Saves order
- `update_order()`: Updates order (including status)

---

## 11. Example Scenarios

### Scenario 1: Simple Order (Retailer Has Stock)

**Setup**:
- Retailer A has "Coffee Maker" with stock: 50 units
- Wholesaler X has "Coffee Maker" with stock: 200 units
- Customer C places order for 2 units

**Flow**:
1. Customer adds 2 units to cart
2. Order assigned to Retailer A (has stock)
3. Order status: "pending"
4. Customer pays → Order status: "confirmed"
5. Retailer A stock: 50 → 48 units (decreased automatically)
6. Order processed → delivered

**Result**: Quick delivery (no wholesaler delay)

---

### Scenario 2: Order Requiring Wholesaler Sourcing

**Setup**:
- Retailer A has "Coffee Maker" with stock: 0 units
- Wholesaler X has "Coffee Maker" with stock: 200 units
- Customer C places order for 2 units

**Flow**:
1. Customer adds 2 units to cart
2. Order assigned to Retailer A (nearest retailer, even with 0 stock)
3. Order status: "pending"
4. Flag set: `needs_wholesaler_order = True`
5. **Email sent to Retailer A**: "Restock Alert - Customer ordered Coffee Maker"
6. Customer pays → Order status: "pending wholesaler order"
7. Retailer A places order to Wholesaler X for 2 units (high priority)
8. **Stock automatically updated**:
   - Wholesaler X stock: 200 → 198 units
   - Retailer A stock: 0 → 2 units (created)
9. Order status: "pending wholesaler order"
10. Wholesaler X confirms order → Order status: "pending wholesaler order" → "pending"
11. Retailer A processes order → delivered

**Result**: Delivery time = Base distance + 2 days (wholesaler delay)

---

### Scenario 3: Retailer Independent Ordering

**Setup**:
- Retailer A has "Coffee Maker" with stock: 10 units (low)
- Wholesaler X has "Coffee Maker" with stock: 200 units

**Flow**:
1. Retailer A goes to "Order from Wholesaler" tab
2. Selects "Coffee Maker" from Wholesaler X
3. Orders 50 units (independent order)
4. **Stock automatically updated**:
   - Wholesaler X stock: 200 → 150 units
   - Retailer A stock: 10 → 60 units
5. Email confirmations sent to both parties

**Result**: Retailer restocked proactively, ready for customer orders

---

## 12. Troubleshooting Common Issues

### Issue 1: Order Not Assigned to Retailer
**Cause**: No retailer has the product listed
**Solution**: 
- System assigns to nearest retailer anyway
- Retailer will need to order from wholesaler if stock = 0

### Issue 2: Stock Update Failed
**Cause**: Insufficient wholesaler stock or system error
**Solution**:
- Order is created but stock update fails
- Retailer receives error message
- Order status remains "pending"
- Retailer should check wholesaler stock manually

### Issue 3: Customer Order Stuck in "Pending Wholesaler Order"
**Cause**: Wholesaler hasn't confirmed order yet
**Solution**:
- Retailer should contact wholesaler
- Wholesaler should confirm order to update status

### Issue 4: Duplicate Product Entries
**Cause**: Retailer creates product with different product_id instead of using existing one
**Solution**:
- System handles via product aggregation
- Same product_id recommended for consistency

---

## 13. Data Flow Diagram

```
┌─────────────┐
│  Wholesaler │
│  Adds Product│
│  Stock: 200  │
└──────┬──────┘
       │
       │ (Retailer Orders)
       ▼
┌─────────────┐     ┌──────────────┐
│  Retailer   │────▶│ Stock Update │
│  Stock: 50  │     │ (Automatic)  │
└──────┬──────┘     └──────────────┘
       │
       │ (Customer Orders)
       ▼
┌─────────────┐
│  Customer   │
│  Purchases  │
└─────────────┘

Stock Flow:
Wholesaler (200) → Retailer Orders (50) → Retailer Stock (50)
Retailer Stock (50) → Customer Orders (2) → Retailer Stock (48)
```

---

## 14. Key Metrics Tracked

### For Retailers:
- Customer orders received
- Orders requiring wholesaler sourcing
- Stock levels per product
- Order history to wholesalers

### For Wholesalers:
- Orders from retailers
- High priority orders count
- Stock levels per product
- Customer order links

### For Customers:
- Estimated delivery date
- Delivery breakdown (distance + wholesaler delay)
- Order status updates

---

## Conclusion

This inventory management system ensures:
- ✅ **Clear separation**: Customer → Retailer → Wholesaler
- ✅ **Automatic stock management**: Real-time updates
- ✅ **Priority handling**: High priority orders linked to customers
- ✅ **Transparency**: All parties see relevant information
- ✅ **Efficient sourcing**: Retailers can proactively restock or source on-demand

The system maintains inventory accuracy while providing clear workflows for all stakeholders.

