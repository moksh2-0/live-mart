# LiveMART — Multi-Role Online Delivery Platform

A Streamlit web app that models a three-tier e-commerce supply chain — **Customers**,
**Retailers**, and **Wholesalers** — in one platform. Retailers source stock from
wholesalers and sell to customers; the app handles auth, catalog browsing, search,
cart/checkout, mock payments, and order tracking across all three roles.

Originally built as a group project for a university Object-Oriented Programming
course. See [`docs/ACADEMIC_REPORT.md`](docs/ACADEMIC_REPORT.md) for the full
architecture write-up submitted with the assignment.

## Contributors
- Moksh Ahuja
- Pranay Garg
- Aarya Tripathi
- Tirth Kamdar

## Features

- **Multi-role auth** — Customer / Retailer / Wholesaler registration and login,
  mock OTP verification, optional real Google/Facebook OAuth (simulated if unconfigured)
- **Role-specific dashboards** — browsing & cart (Customer), inventory + customer
  order management + wholesaler ordering (Retailer), inventory + retailer order
  management (Wholesaler)
- **Search & filtering** — by name/description/category, price range, stock, seller
  type, with optional location-based sorting
- **Cart & checkout** — with a mock payment gateway (Luhn-validated card numbers,
  simulated success/failure rates, transaction IDs and receipts)
- **Order lifecycle tracking** — pending → confirmed → processing → shipped → delivered
- **Product feedback/ratings system**
- **Email notifications** — via Gmail SMTP if configured, otherwise logged locally

All data is persisted to JSON files in `data/` rather than a real database — a
deliberate simplification for the scope of the assignment, not an oversight (see
[Known Limitations](#known-limitations) below).

## Quick Start

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. No configuration is required to try it —
OAuth, email, and maps all fall back to mock/simulated behavior out of the box.

To enable the real versions of those integrations (real Google login, real emails,
real geocoding), see [`docs/SETUP.md`](docs/SETUP.md).

## Project Structure

```
.
├── app.py                  # Entry point / home page
├── pages/                  # One file per app screen (Streamlit auto-routes these)
│   ├── 1_Registration.py
│   ├── 2_Customer_Dashboard.py
│   ├── 3_Retailer_Dashboard.py
│   ├── 4_Wholesaler_Dashboard.py
│   ├── 5_Search.py
│   ├── 6_Orders.py
│   ├── 7_Cart.py
│   ├── 8_Product_Detail.py
│   └── 9_OAuth_Callback.py
├── utils/                  # Business logic, one module per concern
│   ├── auth.py              # Login/session handling
│   ├── database.py          # JSON read/write layer
│   ├── orders.py             # Order lifecycle
│   ├── payments.py            # Mock payment gateway
│   ├── oauth.py / email_service.py / maps.py / geocoding.py
│   ├── filters.py / recommendations.py / feedback.py
│   └── retailer_notifications.py / retailer_wholesaler_orders.py / product_aggregation.py
├── components/
│   └── product_cards.py     # Reusable UI components
├── data/                    # JSON "database" (sample data)
├── config_oauth.py / config_email.py / config_maps.py   # Read from .env, see docs/SETUP.md
├── scripts/                 # One-off maintenance/migration scripts (not part of the running app)
├── docs/
│   ├── SETUP.md                       # OAuth / email / maps configuration
│   ├── TESTING_GUIDE.md               # Manual test cases
│   ├── INVENTORY_MANAGEMENT_WORKFLOW.md
│   └── ACADEMIC_REPORT.md             # Original project report
└── requirements.txt
```

## Usage

1. **Register/Login** — pick a role (Customer, Retailer, Wholesaler); use the
   on-screen mock OTP or a password
2. **Customer** — browse, search, add to cart, checkout with a mock card payment
3. **Retailer** — stock inventory by ordering from wholesalers, manage pricing,
   fulfill customer orders
4. **Wholesaler** — stock inventory, manage pricing for retailers, fulfill
   retailer orders

### Testing payments
Any Luhn-valid card number works, e.g. `4532 1234 5678 9010`, any future expiry
(`12/25`), any 3–4 digit CVV. The mock gateway simulates a realistic ~92% success
rate.

## Known Limitations

This was built under course time constraints, so a few things are intentionally
simple rather than production-grade:

- **JSON files instead of a real database** — fine for a class demo, would need a
  real DB (Postgres/SQLite) for concurrent users or production use
- **SHA-256 password hashing without salting** — sufficient to demonstrate the
  concept, not production-grade (would use bcrypt/argon2 in a real system)
- **OTP and some features are mocked/simulated** by design where a real third-party
  integration (SMS, etc.) was out of scope for the assignment

## Tech Stack

Python, Streamlit, JSON file storage, Authlib (OAuth), Geopy (geocoding), Pillow.

## License

MIT — see [LICENSE](LICENSE). Built for educational purposes.
