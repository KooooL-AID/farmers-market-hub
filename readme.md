# Farm Market Hub

## 1. Overview

Farm Market Hub is a web application designed to connect local farmers directly with consumers. It provides a platform for farmers to list their produce and for buyers to browse, purchase, and communicate with farmers. The application also includes admin functionalities for managing the platform, official market prices, and user activities.

## 2. Key Features

- **User Roles:**
  - **Buyer:** Can browse products, add items to a cart, checkout, view order history, and message farmers.
  - **Farmer:** Can manage their product listings (add, edit, delete), manage their profile, write private notes, and communicate with buyers.
  - **Admin:** Can manage users, all product listings (approve/reject/update status), and official market prices.
- **Product Listings:**
  - Farmers can list products with details like name, description, category, price, unit, quantity available, and an image.
  - Buyers can browse and search these listings.
- **Official Market Prices:**
  - Admins can manage a list of official market prices for various commodities.
  - Users can view these official prices and compare them with farmer listings.
- **Shopping Cart:**
  - Buyers can add products to a shopping cart.
  - Cart contents can be updated (quantity) or items removed.
- **Checkout Process:**
  - Buyers can proceed to checkout with items in their cart.
  - Includes shipping information and simulated payment methods (COD, GCash, Maya).
  - Order creation and basic inventory reduction (decrementing `quantity_available`).
- **Order History:**
  - Buyers can view their past orders.
- **Messaging System:**
  - Buyers can initiate conversations with farmers regarding specific product listings.
  - Both buyers and farmers can send and receive messages within these conversations.
  - Navbar notification for unread messages.
- **Farmer Notes:**
  - Farmers have a private section to write and save notes (e.g., farming plans, reminders).
  - Notes can be downloaded as a `.txt` file.
- **Admin Panel:**
  - Dashboard with platform statistics.
  - Management of all farmer product listings (update status).
  - Management of official market prices (add, edit, delete).
  - Management of user accounts (view, edit roles, delete).
- **Responsive Design:**
  - User interface designed to be usable across various devices (desktops, tablets, mobile).
- **Image Uploads:**
  - Farmers can upload images for their product listings.

## 3. Technology Stack

- **Backend:**
  - Python
  - Flask (Web Framework)
  - Flask-SQLAlchemy (ORM for database interaction)
  - Flask-Migrate (for database schema migrations using Alembic)
  - Flask-Login (for user session management)
  - Flask-Bcrypt (for password hashing - though `werkzeug.security` is used directly in the provided code)
  - Werkzeug (WSGI utility library, used for password hashing and secure filenames)
- **Database:**
  - PostgreSQL (implied by `psycopg2-binary` in `requirements.txt`, though SQLAlchemy makes it adaptable to other SQL databases)
- **Frontend:**
  - HTML5
  - CSS3 (with custom `styles.css`)
  - Bootstrap 5.3 (CSS Framework)
  - JavaScript (for client-side interactions like modals, form validation, image previews)
  - Jinja2 (Templating Engine for Flask)
  - Font Awesome (for icons)
  - Google Fonts (Poppins)
- **Development Tools:**
  - Virtual Environment (`venv`)
  - `pip` for package management
  - `python-dotenv` for environment variable management

## 4. Setup and Installation

### Prerequisites

- Python 3.x
- pip (Python package installer)
- Virtualenv (recommended for isolating project dependencies)
- A PostgreSQL database instance (or adapt `SQLALCHEMY_DATABASE_URI` in `config.py` for another database).

### Steps

1.  **Clone the Repository (Example):**

    ```bash
    git clone <your-repository-url>
    cd farm-market-hub
    ```

2.  **Create and Activate a Virtual Environment:**
    You can also create a virtual environment by selecting your interpreter an creating a Virtualenv by it
    Activate it by file directory in terminal for Example in my case: ".\.venv\Scripts\activate"

    ```bash
    python -m venv .venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**

    - Create a `.env` file in the root directory of the project.
    - Add the following necessary variables (refer to `config.py` for all possible configurations):
      ```env
      FLASK_APP=run.py  # Or app.py if that's your entry point
      FLASK_ENV=development
      SECRET_KEY='your_super_secret_key_here' # Change this to a random, strong key
      SQLALCHEMY_DATABASE_URI='postgresql://username:password@host:port/database_name' # Replace with your DB details
      UPLOAD_FOLDER='uploads/products' # Or your preferred upload path relative to static or instance folder
      ALLOWED_EXTENSIONS='png,jpg,jpeg,gif'
      ```
    - **Note:** The `UPLOAD_FOLDER` should be accessible by the web server. If it's relative to the app root, ensure your routes serve files from there correctly or place it within the `static` folder. The current `routes.py` uses `current_app.config['UPLOAD_FOLDER']` and `send_from_directory`, which implies it's a direct path.

5.  **Database Setup:**

    - Ensure your PostgreSQL server is running and the database specified in `SQLALCHEMY_DATABASE_URI` exists.
    - Initialize the database and apply migrations:
      ```bash
      flask db init  # Only if you haven't initialized migrations before
      flask db migrate -m "Initial migration" # Or a descriptive message
      flask db upgrade
      ```

6.  **Create Admin User (Optional - Recommended):**

    - The application has an `admin_required` decorator. You might need to create an admin user manually in the database or add a CLI command for this.
    - A `create_admin` command is registered in `commands.py` (referenced in `app.py`). You can run it:
      ```bash
      flask create_admin <username> <email> <password>
      ```
      Replace `<username>`, `<email>`, and `<password>` with desired credentials.

7.  **Run the Application:**
    ```bash
    flask run
    ```
    The application should now be running, typically at `http://127.0.0.1:5000/`.

## 5. Project Structure

farm-market-hub/
├── app.py # Flask application factory and core initialization
├── config.py # Configuration settings (database URI, secret key, etc.)
├── extensions.py # Flask extension instantiations (db, login_manager, migrate)
├── models.py # SQLAlchemy database models
├── routes.py # Flask routes and view functions (Blueprint: main_bp)
├── commands.py # Custom Flask CLI commands (e.g., create_admin)
├── requirements.txt # Python package dependencies
├── .env # Environment variables (not committed to Git)
├── instance/ # Instance-specific configuration (if used)
│ └── uploads/ # (If UPLOAD_FOLDER is configured here)
├── static/
│ ├── css/
│ │ └── styles.css # Custom stylesheets
│ ├── images/
│ │ └── market-bg.jpg # Background image, placeholder images, etc.
│ └── js/ # Custom JavaScript files (if any)
├── templates/
│ ├── admin/ # Templates for the admin panel
│ │ ├── admin_dashboard.html
│ │ ├── manage_listings.html
│ │ ├── manage_prices.html
│ │ ├── add_price.html
│ │ ├── edit_price.html
│ │ └── users.html
│ │ └── edit_user.html
│ ├── auth/ # (If you had separate auth templates, e.g., login.html, register.html - currently they are top-level)
│ ├── cart/
│ │ └── view_cart.html
│ ├── checkout/
│ │ ├── checkout.html
│ │ └── order_confirmation.html
│ │ └── order_history.html
│ ├── errors/ # Error page templates (403, 404, 500)
│ │ ├── 403.html
│ │ ├── 404.html
│ │ └── 500.html
│ ├── farmer/ # Templates for farmer-specific views
│ │ ├── manage_listings.html
│ │ ├── add_listing.html
│ │ ├── edit_listing.html
│ │ └── notes.html
│ ├── messages/ # Templates for the messaging system
│ │ ├── conversation_list.html
│ │ └── conversation_detail.html
│ ├── base.html # Base template for common layout
│ ├── index.html # Homepage
│ ├── login.html
│ ├── market_prices.html
│ ├── products_browse.html
│ ├── register.html
│ └── \_flash_messages.html # Partial for displaying flashed messages
├── uploads/ # Directory for user-uploaded files (e.g., product images)
│ └── products/ # (If UPLOAD_FOLDER is set to 'uploads/products')
└── venv/ # Python virtual environment (not committed to Git)

## 6. Key Functionalities in Detail

### User Authentication

- **Registration:** Users can register as "Buyers" or "Farmers". Farmers provide a `farmer_type`.
- **Login/Logout:** Secure login using hashed passwords and session management via Flask-Login.
- **Role-Based Access:** Different parts of the application are accessible based on user roles (`is_buyer`, `is_farmer`, `is_admin` properties in the `User` model).

### Farmer Features

- **Product Listing Management:**
  - View their own listed products (`/farmer/listings`).
  - Add new products with details and image uploads (`/farmer/listings/add`).
  - Edit existing product details, image, and status (`/farmer/listings/edit/<id>`).
  - Delete their product listings (`/farmer/listings/delete/<id>`).
- **Notes:**
  - A private section for farmers to take and save notes (`/farmer/notes`).
  - Notes can be downloaded as a `.txt` file.

### Buyer Features

- **Browse Products:** View all active farmer listings with search and category filtering (`/products`).
- **Market Prices:** View official market prices and compare them with farmer listings (`/market-prices`).
- **Shopping Cart:** Add products, view cart, update quantities, remove items (`/cart/...`).
- **Checkout:** Secure checkout process with shipping details and simulated payment (`/checkout`).
- **Order History:** View past orders (`/orders`).

### Messaging System

- Buyers can initiate conversations with farmers about specific products.
- A dedicated inbox (`/messages`) lists all conversations for a user.
- Users can view individual conversations and send messages (`/messages/<id>`).
- Unread message notifications are available in the navbar.

### Admin Panel

- **Dashboard:** Overview of users and listings (`/admin/dashboard`).
- **Manage Farmer Listings:** View all listings, filter by status, and update listing status (e.g., approve, reject, mark inactive) (`/admin/listings`).
- **Manage Official Market Prices:** Add, edit, and delete official market prices. Price changes are logged in `MarketPriceHistory` (`/admin/prices/...`).
- **Manage Users:** View all users, edit their details (including roles), and delete users (`/admin/users/...`).

## 📸 Screenshots

### 🏠 Homepage

![Homepage](screenshots/homepage.png)

### 📊 Market Prices

![Market Prices](screenshots/market-prices.png)

## 🧑‍🌾 Farmers Produce Listings

![Produce Listings](screenshots/farmers-market.png)
