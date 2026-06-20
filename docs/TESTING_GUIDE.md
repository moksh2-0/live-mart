# LiveMART - Comprehensive Testing Guide

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Customer Testing Scenarios](#customer-testing-scenarios)
3. [Retailer Testing Scenarios](#retailer-testing-scenarios)
4. [Wholesaler Testing Scenarios](#wholesaler-testing-scenarios)
5. [End-to-End Flow Testing](#end-to-end-flow-testing)
6. [Edge Cases and Error Scenarios](#edge-cases-and-error-scenarios)

---

## Initial Setup

### Step 1: Start the Application
```bash
cd C:\Users\LENOVO\Documents\OneDrive\Desktop\Streamlit
streamlit run app.py
```

### Step 2: Verify Application Loads
- Application should open in browser at `http://localhost:8501`
- Home page should display with featured products
- No errors in terminal

---

## Customer Testing Scenarios

### Test Case 1: Customer Registration (Email/Password)

**Steps**:
1. Click on "Login/Register" or navigate to Registration page
2. Click "Register" tab
3. Fill in details:
   - Name: "John Customer"
   - Email: "john@example.com"
   - Password: "password123"
   - Phone: "9876543210"
   - Role: Select "Customer"
   - Location: Enter "Hyderabad, Telangana, India" (must include comma)
4. Click "Register"
5. Check email for OTP (or check terminal/console for mock OTP)
6. Enter OTP
7. Click "Verify OTP"

**Expected Results**:
- ✅ Registration successful
- ✅ OTP sent to email
- ✅ Redirected to Customer Dashboard after OTP verification
- ✅ Location geocoded automatically (if API key configured)

**Test Location Validation**:
- Try registering with location without comma: "Hyderabad India" (should show error)
- Try registering with proper format: "Hyderabad, Telangana, India" (should work)

---

### Test Case 2: Customer Registration (Google Login)

**Steps**:
1. Click "Continue with Google" button
2. Complete Google OAuth flow
3. If new user, fill additional details (phone, location)
4. Submit

**Expected Results**:
- ✅ OAuth redirect works
- ✅ User logged in successfully
- ✅ Sidebar visible after login
- ✅ Navigate between pages without losing login (no re-login needed)

---

### Test Case 3: Customer - Browse Products

**Steps**:
1. Login as customer
2. Navigate to Customer Dashboard
3. View "All Products" section

**Expected Results**:
- ✅ Products displayed in grid (3 columns)
- ✅ Each product shows:
  - Product image
  - Product name (capitalized)
  - Category (capitalized)
  - **Retailer Stock**: Aggregated stock (e.g., "Retailer Stock: 100 units")
  - **Wholesaler Stock**: Separate stock (e.g., "Wholesaler Stock: 200 units")
  - Price
  - Rating (if available)
- ✅ If retailer stock = 0 but wholesaler has stock: Shows "(available, +2 days delivery)"
- ✅ No raw HTML code visible on product cards

**Check Stock Display**:
- Product with both retailer and wholesaler stock → Shows both
- Product with only retailer stock → Shows only retailer stock
- Product with only wholesaler stock → Shows wholesaler stock with "+2 days delivery" note
- Product with no stock → Shows "Out of Stock"

---

### Test Case 4: Customer - Search Products

**Steps**:
1. Login as customer
2. Navigate to "Search" page (or use search in Customer Dashboard)
3. Type product name in search box
4. Check "Recent Searches" sidebar

**Expected Results**:
- ✅ Real-time search as you type
- ✅ Search history saved in sidebar
- ✅ Can click on recent searches to search again
- ✅ "Clear History" button works
- ✅ If no products found, shows styled "Not Available at the Moment" message with:
  - Searched query
  - Suggestions (Clear Search, Clear All Filters, View All Products)

**Test Search Scenarios**:
- Search for existing product → Should find it
- Search for non-existent product → Should show "Not Available" message
- Search with filters applied → Should respect filters

---

### Test Case 5: Customer - Add Product to Cart (With Animation)

**Steps**:
1. Login as customer
2. Browse products on Customer Dashboard
3. Select quantity for a product
4. Click "Add to Cart" button

**Expected Results**:
- ✅ Product added to cart successfully
- ✅ **Bounce animation** appears with green success message
- ✅ Message shows: "✓ Added [quantity] x [product name] to cart!"
- ✅ Page refreshes and cart updates

**Test Different Scenarios**:
- Add product with retailer stock > 0 → Should work normally
- Add product with retailer stock = 0 but wholesaler has stock → Should still work (will need wholesaler sourcing)
- Try to add quantity > available stock → Should limit to max available

---

### Test Case 6: Customer - Distance Filter

**Steps**:
1. Login as customer
2. Ensure location is set (check sidebar)
3. In sidebar, enable "Filter by distance from my location"
4. Set "Maximum Distance (km)" to a value (e.g., 50 km)
5. View products

**Expected Results**:
- ✅ Only products from retailers within 50 km are shown
- ✅ Products show distance: "X.XX km away (nearest retailer)"
- ✅ Products sorted by distance (nearest first)
- ✅ Products only from wholesaler show: "Available from wholesaler (+2 days)"

**Test Scenarios**:
- Enable filter with location set → Should filter correctly
- Enable filter without location set → Should show warning, prompt to update location
- Change distance value → Should update filtered results

---

### Test Case 7: Customer - Update Location

**Steps**:
1. Login as customer
2. In sidebar, scroll to "Update Location" section
3. Click "Edit Location" expander
4. Enter new location: "Mumbai, Maharashtra, India"
5. Click "Update Location"

**Expected Results**:
- ✅ Location updated successfully
- ✅ Location geocoded automatically (if API key configured)
- ✅ Coordinates saved to user profile
- ✅ Success message shown with formatted address

**Test Location Validation**:
- Try invalid format (no comma) → Should show error
- Try valid format → Should work

---

### Test Case 8: Customer - View Product Details

**Steps**:
1. Login as customer
2. Browse products
3. Click "View Details" on any product

**Expected Results**:
- ✅ Navigate to Product Detail page
- ✅ Shows full product information:
  - Product name, category, description
  - Retailer Stock and Wholesaler Stock (separately)
  - Price
  - Seller/Retailer information
  - Customer reviews/feedback
  - "You May Also Like" section with similar products

---

### Test Case 9: Customer - Place Order (Online Payment) - Retailer Has Stock

**Prerequisites**:
- Product in cart
- Retailer has stock for the product

**Steps**:
1. Login as customer
2. Add product(s) to cart
3. Navigate to "Cart" page
4. Review cart items
5. Select payment method: "online"
6. Click "Place Order"
7. Fill payment details:
   - Card Number: `4532 1234 5678 9010` (passes Luhn validation)
   - Expiry: `12/25`
   - CVV: `123`
   - Cardholder Name: "John Customer"
8. Click "Pay Now"

**Expected Results**:
- ✅ Payment processed (with 1-3 second delay simulation)
- ✅ **"Order Successful!" message displayed with balloons**
- ✅ Order confirmation shows:
  - Order ID
  - Total Amount
  - Estimated Delivery Date
  - Total Delivery Days (1-5 days based on distance)
  - Delivery Breakdown per item (if available)
- ✅ Email sent to customer with order confirmation
- ✅ Cart cleared
- ✅ Order visible in "Orders" page

**Check Delivery Time**:
- If retailer has stock → Base distance time only (1-5 days)
- If retailer stock = 0, wholesaler has stock → Base distance + 2 days

---

### Test Case 10: Customer - Place Order (Online Payment) - Retailer Stock = 0

**Prerequisites**:
- Product in cart
- Retailer stock = 0 for the product
- Wholesaler has stock for the product

**Steps**:
1. Login as customer
2. Add product to cart (where retailer stock = 0)
3. Navigate to "Cart" page
4. Review cart items
5. Notice delivery time breakdown shows "+2 days for wholesaler sourcing"
6. Select payment method: "online"
7. Click "Place Order"
8. Complete payment

**Expected Results**:
- ✅ Order placed successfully
- ✅ Order confirmation shows **delivery time = base distance + 2 days**
- ✅ Delivery breakdown shows:
  - Base delivery days (distance-based)
  - "+2 days for wholesaler sourcing" note
- ✅ **Email sent to ALL retailers** with "Product Demand Alert"
- ✅ Order status: "pending wholesaler order" (after payment)
- ✅ Email to all retailers includes:
  - Product name and details
  - Wholesaler stock available
  - Note: Customer order received but assigned retailer has no stock
  - Recommendation to add product to inventory
  - Customer order reference

**Note**: When the assigned retailer's stock = 0 (regardless of whether other retailers have stock), ALL retailers receive an email notification. This ensures all retailers are aware of product demand and can add it to their inventory.

---

### Test Case 11: Customer - Place Order (Offline Payment)

**Steps**:
1. Login as customer
2. Add products to cart
3. Navigate to "Cart" page
4. Select payment method: "offline"
5. Click "Place Order"

**Expected Results**:
- ✅ Order placed successfully
- ✅ Message: "Order placed successfully! Payment will be collected on delivery."
- ✅ Cart cleared
- ✅ Order visible in "Orders" page with payment status: "pending"

---

### Test Case 12: Customer - View Orders

**Steps**:
1. Login as customer
2. Navigate to "Orders" page
3. View order list

**Expected Results**:
- ✅ All customer orders displayed
- ✅ Order details show:
  - Order ID
  - Status with timeline visualization
  - Estimated delivery date
  - Delivery breakdown (distance + wholesaler delay if applicable)
  - Items ordered
  - Payment status
- ✅ Can filter orders by status
- ✅ Delivery breakdown shows:
  - Base delivery days (distance)
  - "+2 days wholesaler delay" if applicable
  - Total days

---

### Test Case 13: Customer - Forgot Password Flow

**Steps**:
1. Go to Login/Register page
2. In Login tab, click "Forgot Password?"
3. Enter email address
4. Click "Send OTP"
5. Check email for OTP
6. Enter OTP
7. Verify OTP

**Expected Results**:
- ✅ OTP sent to email
- ✅ Can log in after OTP verification
- ✅ Works even if user forgot password

---

### Test Case 14: Customer - Recommended Products

**Prerequisites**:
- Customer has placed at least one order previously

**Steps**:
1. Login as customer with order history
2. View Customer Dashboard
3. Scroll to "Recommended For You" section

**Expected Results**:
- ✅ Recommended products based on previous orders
- ✅ Products from similar categories
- ✅ Products in similar price range
- ✅ "Recommended" badge on product cards

**Test for New Customer**:
- New customer with no orders → Should see "Trending Products" instead

---

## Retailer Testing Scenarios

### Test Case 15: Retailer Registration

**Steps**:
1. Go to Registration page
2. Click "Register" tab
3. Fill in details:
   - Name: "ABC Retail Store"
   - Email: "retailer@example.com"
   - Password: "password123"
   - Phone: "9876543210"
   - Role: Select "Retailer"
   - Location: "Bangalore, Karnataka, India"
4. Click "Register"
5. Verify OTP

**Expected Results**:
- ✅ Registration successful
- ✅ Redirected to Retailer Dashboard
- ✅ **No "Add Product" tab visible** (retailers cannot add their own products)

---

### Test Case 16: Retailer - View Inventory

**Steps**:
1. Login as retailer
2. Go to "Inventory Management" tab

**Expected Results**:
- ✅ Shows products in retailer's inventory (initially empty)
- ✅ Message: "You don't have any products in your inventory yet. Order products from wholesalers in the 'Order from Wholesaler' tab to add them to your inventory."
- ✅ Can edit/delete existing products
- ✅ Cannot add new products (no Add Product tab)

---

### Test Case 17: Retailer - View Customer Orders

**Steps**:
1. Login as retailer
2. Go to "Customer Orders" tab
3. View orders

**Expected Results**:
- ✅ Shows only orders from customers (not retailer-to-wholesaler orders)
- ✅ Order details show:
  - Customer name
  - Order items
  - Order status
  - Payment information
- ✅ Can update order status: pending → confirmed → processing → shipped → delivered
- ✅ Customer receives email on status update

**Test Status Updates**:
- Update status → Customer should receive email
- Check for orders with status "pending wholesaler order" → Should show high priority indicator

---

### Test Case 18: Retailer - Place High Priority Order to Wholesaler (Linked to Customer Order)

**Prerequisites**:
- Customer has placed order for product where retailer stock = 0
- Wholesaler has that product in stock
- Order status is "pending wholesaler order"

**Steps**:
1. Login as retailer
2. Go to "Order from Wholesaler" tab
3. Go to "Place New Order" sub-tab
4. View "High Priority: Orders Linked to Customer Orders" section
5. See customer order listed with required products
6. Click "Place High Priority Order to [Wholesaler Name]" for a product
7. Verify quantity matches customer order exactly

**Expected Results**:
- ✅ Order placed to wholesaler successfully
- ✅ **Stock automatically updated**:
  - Wholesaler stock decreased
  - Retailer stock increased (or product added to retailer inventory)
- ✅ Customer order status updated: "pending wholesaler order" → "pending" (after wholesaler confirms)
- ✅ **Email sent to wholesaler** with:
  - Order details
  - **HIGH PRIORITY flag**
  - Linked customer order ID
  - Customer name
- ✅ **Email sent to retailer** with:
  - Stock update confirmation
  - Linked customer order reference
- ✅ Order visible in "Order History" sub-tab

---

### Test Case 19: Retailer - Place Independent Order to Wholesaler

**Steps**:
1. Login as retailer
2. Go to "Order from Wholesaler" tab
3. Go to "Place New Order" sub-tab
4. Scroll to "All Products from Wholesalers" section
5. Browse products (grouped by product_id, showing each wholesaler separately)
6. For a product, see:
   - Wholesaler name
   - Price per unit (per-wholesaler pricing)
   - Stock available
7. Select quantity (any amount)
8. Click "Place Order"

**Expected Results**:
- ✅ Order placed successfully
- ✅ **Stock automatically updated**:
  - Wholesaler stock decreased
  - Retailer stock increased
- ✅ Email sent to both parties
- ✅ Order visible in "Order History" sub-tab
- ✅ Order shows priority: "Normal" (not high priority)

**Test Product Display**:
- Same product from multiple wholesalers → Shows separately with different prices
- Can order from any wholesaler
- Stock updates reflect in retailer inventory immediately

---

### Test Case 20: Retailer - View Order History

**Steps**:
1. Login as retailer
2. Go to "Order from Wholesaler" tab
3. Go to "Order History" sub-tab
4. View orders

**Expected Results**:
- ✅ All orders placed to wholesalers displayed
- ✅ Shows:
  - Order ID, Date, Status
  - Wholesaler name
  - Items and quantities
  - Priority (High Priority or Normal)
  - Linked customer order ID (if high priority)
- ✅ Can filter by:
  - Status: All, pending, confirmed, processing, shipped, delivered
  - Priority: All, High Priority, Normal
- ✅ Orders sorted by date (newest first)

---

### Test Case 21: Retailer - View Products Only from Retailers Section

**Steps**:
1. Login as retailer
2. Go to "Order from Wholesaler" tab
3. Scroll to "Products Available Only from Retailers" section

**Expected Results**:
- ✅ Shows products that are **only** listed by retailers (not available from wholesalers)
- ✅ Shows all retailers who have these products
- ✅ Displays retailer name, price, and stock for each

---

### Test Case 22: Retailer - Receive Customer Order Requiring Wholesaler Sourcing

**Prerequisites**:
- Retailer has product with stock = 0
- Wholesaler has that product

**Steps**:
1. Login as retailer
2. **As customer**, place order for product where retailer stock = 0
3. **As retailer**, check email for "Restock Alert"
4. Go to "Customer Orders" tab
5. View the customer order

**Expected Results**:
- ✅ Order visible in Customer Orders tab
- ✅ Order status: "pending wholesaler order"
- ✅ Warning shown: "This order requires ordering from wholesaler"
- ✅ Product listed with quantity needed
- ✅ Retailer can click to go to "Order from Wholesaler" tab

---

## Wholesaler Testing Scenarios

### Test Case 23: Wholesaler Registration

**Steps**:
1. Go to Registration page
2. Register as Wholesaler with:
   - Name: "XYZ Wholesale Company"
   - Email: "wholesaler@example.com"
   - Role: "Wholesaler"
   - Location: "Delhi, Delhi, India"

**Expected Results**:
- ✅ Registration successful
- ✅ Redirected to Wholesaler Dashboard
- ✅ Can add products

---

### Test Case 24: Wholesaler - Add New Product

**Steps**:
1. Login as wholesaler
2. Go to "Add Product" tab
3. Fill product form:
   - Name: "Premium Coffee Beans"
   - Category: "Food & Beverages"
   - Description: "High-quality coffee beans"
   - Price: 1500.00
   - Stock: 100
   - Image URL: (optional)
4. Click "Add Product"

**Expected Results**:
- ✅ Product added successfully
- ✅ Product visible in "Manage Products" tab
- ✅ If product is only listed by wholesaler (no retailer has it):
  - **Email sent to ALL retailers** notifying them of new product
  - Email suggests retailers add it to their inventory

**Test New Product Notification**:
- Add product that no retailer has → All retailers receive email
- Add product that a retailer already has → No notification sent

---

### Test Case 25: Wholesaler - View Retailer Orders

**Steps**:
1. Login as wholesaler
2. **As retailer**, place order to wholesaler
3. **As wholesaler**, go to "Retailer Orders" tab
4. View orders

**Expected Results**:
- ✅ Shows **only** orders from retailers (customer orders filtered out)
- ✅ Orders sorted by:
  1. **High Priority first** (linked to customer orders)
  2. Then by date (newest first)
- ✅ High priority orders show:
  - "[HIGH PRIORITY]" badge in title
  - **Auto-expanded** in list
  - **Warning banner at top** showing count of high priority orders
  - Linked customer order details:
    - Customer Order ID
    - Customer name
    - Note: "Please prioritize this order"
- ✅ Regular orders show normally (no priority badge)

---

### Test Case 26: Wholesaler - Process High Priority Order

**Prerequisites**:
- Retailer has placed high priority order (linked to customer order)

**Steps**:
1. Login as wholesaler
2. Go to "Retailer Orders" tab
3. Find high priority order (should be at top, auto-expanded)
4. View order details including:
   - Retailer name
   - Linked customer order ID
   - Customer name
   - Items and quantities
5. Update status from "pending" to "confirmed"

**Expected Results**:
- ✅ Order status updated successfully
- ✅ **Customer order status updated**: "pending wholesaler order" → "pending"
- ✅ Email sent to retailer about status update
- ✅ Email sent to customer about status update (if linked)
- ✅ Stock already updated when order was placed (automatic)

**Test Status Flow**:
- pending → confirmed → processing → shipped → delivered
- Each status update sends email notifications

---

### Test Case 27: Wholesaler - Process Normal Priority Order

**Prerequisites**:
- Retailer has placed independent order (not linked to customer order)

**Steps**:
1. Login as wholesaler
2. Go to "Retailer Orders" tab
3. Find normal priority order
4. Update status through workflow

**Expected Results**:
- ✅ Order processed normally
- ✅ No customer order linked
- ✅ Email sent to retailer on status updates
- ✅ Stock already updated when order was placed

---

## End-to-End Flow Testing

### Test Case 28: Complete Flow - Customer Order with Wholesaler Sourcing

**Scenario**: Customer orders product, retailer has no stock, retailer orders from wholesaler

**Steps**:

**Phase 1: Setup**
1. **Wholesaler**: Login → Add product "Test Product" with stock: 50 units
2. **Retailer**: Login → Verify no inventory yet

**Phase 2: Customer Order**
3. **Customer**: Login → Add "Test Product" to cart → Place order with online payment
4. **Customer**: Check order confirmation
   - ✅ Delivery time shows: Base distance + 2 days
   - ✅ Delivery breakdown shows wholesaler delay

**Phase 3: Retailer Action**
5. **Retailer**: Check email → See "Restock Alert" email
6. **Retailer**: Login → Go to "Customer Orders" tab
   - ✅ See customer order with status: "pending wholesaler order"
   - ✅ Warning shown about needing wholesaler order
7. **Retailer**: Go to "Order from Wholesaler" → "Place New Order" sub-tab
   - ✅ See customer order in "High Priority" section
   - ✅ Required quantity matches customer order exactly
8. **Retailer**: Click "Place High Priority Order to [Wholesaler Name]"
   - ✅ Order placed successfully
   - ✅ Stock automatically updated:
     - Wholesaler stock: 50 → 48 units
     - Retailer stock: 0 → 2 units (product added to retailer inventory)

**Phase 4: Wholesaler Action**
9. **Wholesaler**: Login → Go to "Retailer Orders" tab
   - ✅ See high priority order at top (auto-expanded)
   - ✅ See customer order details linked
10. **Wholesaler**: Update order status to "confirmed"
    - ✅ Customer order status updated: "pending wholesaler order" → "pending"
    - ✅ Emails sent to retailer and customer

**Phase 5: Retailer Processes Customer Order**
11. **Retailer**: Go to "Customer Orders" tab
    - ✅ Customer order status now: "pending"
    - ✅ Retailer has stock now (2 units)
12. **Retailer**: Update customer order status: confirmed → processing → shipped → delivered
    - ✅ Customer receives email updates at each status change

**Phase 6: Customer Receives Order**
13. **Customer**: Check "Orders" page
    - ✅ Order status: "delivered"
    - ✅ Delivery confirmation email received

**Expected Final State**:
- ✅ Customer order: "delivered"
- ✅ Retailer stock: 2 → 0 units (after customer order fulfillment)
- ✅ Wholesaler stock: 50 → 48 units
- ✅ All emails sent correctly
- ✅ All status transitions correct

---

### Test Case 29: Complete Flow - Retailer Independent Ordering

**Scenario**: Retailer proactively orders from wholesaler for inventory

**Steps**:
1. **Wholesaler**: Login → Ensure product exists with stock
2. **Retailer**: Login → Go to "Order from Wholesaler" tab
3. **Retailer**: Browse "All Products from Wholesalers" section
4. **Retailer**: Select product, quantity: 10 units (independent order)
5. **Retailer**: Click "Place Order"

**Expected Results**:
- ✅ Order placed successfully
- ✅ Stock automatically updated:
  - Wholesaler stock decreased by 10
  - Retailer stock increased by 10 (or product added)
- ✅ Order visible in "Order History" with priority: "Normal"
- ✅ Email confirmations sent

---

## Edge Cases and Error Scenarios

### Test Case 30: Customer Orders Product with Zero Stock

**Steps**:
1. Login as customer
2. Try to add product with:
   - Retailer stock = 0
   - Wholesaler stock = 0
3. Try to place order

**Expected Results**:
- ✅ Product may still be addable to cart (with max quantity = 1)
- ✅ Order can be placed
- ✅ Retailer receives notification (but no stock available)
- ✅ System handles gracefully

---

### Test Case 31: Retailer Orders More Than Wholesaler Has

**Steps**:
1. Login as retailer
2. Go to "Order from Wholesaler" tab
3. Try to order quantity > wholesaler stock
4. Place order

**Expected Results**:
- ✅ Input limited to max available stock
- ✅ If order quantity > stock, shows error: "Insufficient stock. Available: X, Requested: Y"

---

### Test Case 32: Multiple Retailers Order Same Product

**Steps**:
1. **Retailer A**: Place order for product from wholesaler (quantity: 5)
2. **Retailer B**: Place order for same product from wholesaler (quantity: 10)
3. Check wholesaler stock

**Expected Results**:
- ✅ Both orders processed
- ✅ Wholesaler stock decreased by total (15 units)
- ✅ Each retailer's stock increased independently
- ✅ Each retailer sees only their own orders in history

---

### Test Case 33: Customer Order Assigned to Nearest Retailer

**Steps**:
1. Create multiple retailers with different locations
2. Create multiple products from different retailers (same product_id)
3. Login as customer
4. Enable distance filter
5. Place order

**Expected Results**:
- ✅ Order assigned to nearest retailer with sufficient stock
- ✅ If only one retailer has stock, assigns to that retailer
- ✅ Delivery time based on distance to assigned retailer

---

### Test Case 34: Order Status Transitions

**Test Customer Order Status Flow**:
1. Place order → Status: "pending"
2. (If retailer stock = 0) → Status: "pending wholesaler order"
3. Retailer orders from wholesaler → Status remains: "pending wholesaler order"
4. Wholesaler confirms → Status: "pending" (back to retailer)
5. Retailer confirms → Status: "confirmed"
6. Retailer updates → Status: "processing"
7. Retailer updates → Status: "shipped"
8. Retailer updates → Status: "delivered"

**Expected Results**:
- ✅ Each status transition sends email
- ✅ Status displayed correctly in UI
- ✅ Timeline visualization updates

---

### Test Case 35: Stock Update Verification

**Steps**:
1. **Wholesaler**: Add product with stock: 100 units
2. **Retailer**: Place order for 10 units
3. **Check stocks**:
   - Wholesaler inventory → Should show: 90 units
   - Retailer inventory → Should show: 10 units (product added)
4. **Customer**: Place order for 5 units (through retailer)
5. **Check stocks**:
   - Retailer inventory → Should show: 5 units (10 - 5)
   - Wholesaler inventory → Still 90 units (no change)

**Expected Results**:
- ✅ All stock updates correct
- ✅ No negative stock values
- ✅ Stock reflects immediately after orders

---

### Test Case 36: Email Notification Testing

**Check All Email Scenarios**:

1. **Customer Registration OTP** → Email received?
2. **Forgot Password OTP** → Email received?
3. **Order Confirmation** → Email received with order details?
4. **Order Status Update** → Email received on each status change?
5. **Restock Alert (Retailer)** → Email received when customer orders but retailer stock = 0?
6. **New Product Available (All Retailers)** → Email received when wholesaler adds product?
7. **High Priority Order (Wholesaler)** → Email received with priority flag?
8. **Stock Update Confirmation (Retailer)** → Email received after ordering from wholesaler?
9. **Delivery Confirmation** → Email received when order delivered?

**Expected Results**:
- ✅ All emails sent correctly
- ✅ Email content accurate
- ✅ Links and formatting correct

---

### Test Case 37: Location and Distance Testing

**Test Cases**:

1. **Customer with valid location**:
   - Enable distance filter → Should work
   - View nearby stores → Should show distance

2. **Customer with invalid location**:
   - Try to enable distance filter → Should show error
   - Prompt to update location

3. **Update location during session**:
   - Change location → Distance filter should update
   - Product distances should recalculate

4. **Retailer/Wholesaler location**:
   - Update location → Should geocode
   - Should affect distance calculations for customers

---

### Test Case 38: Cart Functionality

**Test Scenarios**:

1. **Add multiple products**:
   - Add Product A (quantity: 2)
   - Add Product B (quantity: 3)
   - Check cart → Should show both with correct quantities

2. **Add same product twice**:
   - Add Product A (quantity: 1)
   - Add Product A again (quantity: 2)
   - Check cart → Should combine quantities (total: 3)

3. **Remove from cart**:
   - Remove item → Cart updates
   - Empty cart → Shows empty cart message

4. **Update quantity in cart**:
   - Change quantity → Cart updates
   - Try quantity > stock → Should limit to max

5. **Navigate between pages with cart**:
   - Add to cart → Navigate to other pages → Cart persists
   - Cart maintained across session

---

### Test Case 39: Payment Testing

**Test Scenarios**:

1. **Valid payment**:
   - Use valid card (passes Luhn): `4532 1234 5678 9010`
   - Future expiry: `12/25`
   - Valid CVV: `123`
   - Payment should succeed (92% success rate)

2. **Payment failure**:
   - Payment may fail (8% chance)
   - Should show realistic error message
   - Order remains pending

3. **Offline payment**:
   - Select offline payment
   - Order placed without payment processing
   - Payment status: "pending"

---

### Test Case 40: Search and Filter Combinations

**Test Scenarios**:

1. **Search + Category Filter**:
   - Search for "coffee"
   - Filter by category: "Food"
   - Should show only coffee products in Food category

2. **Search + Price Filter**:
   - Search for product
   - Set price range: 1000-5000
   - Should show only products in that price range

3. **Search + Stock Filter**:
   - Search for product
   - Enable "Show only in-stock items"
   - Should show only available products

4. **Search + Distance Filter**:
   - Search for product
   - Enable distance filter
   - Should show only products within distance

5. **Search + Multiple Filters**:
   - Apply all filters together
   - Should respect all filters

---

## Testing Checklist

### ✅ Customer Features
- [ ] Registration (Email/Password)
- [ ] Registration (Google OAuth)
- [ ] Login
- [ ] Forgot Password with OTP
- [ ] Browse Products (aggregated stock display)
- [ ] Search Products (real-time, history)
- [ ] Add to Cart (with bounce animation)
- [ ] View Cart
- [ ] Place Order (Online Payment)
- [ ] Place Order (Offline Payment)
- [ ] View Orders
- [ ] Order Status Updates
- [ ] Distance Filter
- [ ] Update Location
- [ ] View Product Details
- [ ] Recommended Products
- [ ] Trending Products (for new users)

### ✅ Retailer Features
- [ ] Registration
- [ ] View Inventory (empty state)
- [ ] View Customer Orders
- [ ] Update Customer Order Status
- [ ] Place High Priority Order (linked to customer order)
- [ ] Place Independent Order to Wholesaler
- [ ] View Order History
- [ ] View Products from Wholesalers (per-wholesaler pricing)
- [ ] View Products Only from Retailers
- [ ] Receive Restock Alert Email
- [ ] Receive New Product Notification Email
- [ ] Stock Updates (automatic)

### ✅ Wholesaler Features
- [ ] Registration
- [ ] Add Product
- [ ] Update Product
- [ ] Delete Product
- [ ] View Retailer Orders (only retailer orders)
- [ ] View High Priority Orders
- [ ] Update Order Status
- [ ] Process High Priority Orders
- [ ] Process Normal Priority Orders
- [ ] Email Notifications

### ✅ System Integration
- [ ] Stock Aggregation (retailer + wholesaler)
- [ ] Automatic Stock Updates
- [ ] Order Assignment (nearest retailer)
- [ ] Delivery Time Calculation (1-5 days range)
- [ ] Wholesaler Delay (+2 days)
- [ ] Order Linking (retailer order to customer order)
- [ ] Status Transitions
- [ ] Email Notifications (all types)
- [ ] Location Geocoding
- [ ] Distance Calculations

---

## Quick Test Scenarios Summary

### Scenario 1: Happy Path
1. Wholesaler adds product
2. Retailer orders product from wholesaler
3. Customer places order
4. Retailer confirms
5. Order delivered

### Scenario 2: Wholesaler Sourcing Required
1. Customer places order
2. Retailer stock = 0
3. Retailer receives restock alert
4. Retailer places high priority order
5. Wholesaler confirms
6. Retailer processes customer order
7. Order delivered

### Scenario 3: Multiple Retailers
1. Multiple retailers order same product from wholesaler
2. Each retailer's stock updates independently
3. Customers order from different retailers
4. Each retailer fulfills their own customer orders

---

## Notes for Testing

1. **Use Different Browsers/Incognito** for testing different roles simultaneously
2. **Check Email** (or terminal) for OTP and email notifications
3. **Verify Stock Updates** in both retailer and wholesaler dashboards
4. **Check Order Statuses** in all relevant dashboards
5. **Test Distance Calculations** with valid location coordinates
6. **Verify Email Notifications** are sent for all events

---

## Common Issues to Watch For

1. **Session Loss**: After OAuth login, navigate within same tab (not new tab)
2. **Stock Mismatch**: Verify stock updates after each order
3. **Status Sync**: Check that order status updates reflect everywhere
4. **Email Delivery**: Check spam folder or terminal output for emails
5. **Distance Calculations**: Ensure locations are geocoded correctly

---

This testing guide covers all major functionality of the LiveMART system. Follow these test cases systematically to ensure everything works as expected.

