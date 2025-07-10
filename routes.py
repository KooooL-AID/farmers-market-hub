import os # Import os module
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, jsonify, abort, current_app, send_from_directory, session) # Added current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user # type: ignore
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename # Import secure_filename
from urllib.parse import urlparse, urljoin # Import from standard library
from datetime import datetime
# Correct import:
from models import (db, User, MarketPrice, Crop, Livestock, MarketPriceHistory,
                    ProductListing, FarmerNote, Cart, CartItem, Order, OrderItem, Conversation, Message) # Added Cart, CartItem
from functools import wraps
import decimal
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

# --- Helper Function for Allowed Files ---
def allowed_file(filename):
    """Checks if the uploaded file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# --- Helper Function to Save File ---
def save_product_image(file):
    """Saves the uploaded product image and returns the secure filename."""
    if file and allowed_file(file.filename):
        # Generate a secure filename (prevents path traversal, etc.)
        filename = secure_filename(file.filename)
        # Create a unique filename (e.g., using UUID or timestamp) to avoid collisions (Optional but recommended)
        # import uuid
        # unique_filename = str(uuid.uuid4()) + "_" + filename
        # For simplicity, we'll use secure_filename directly for now, but collisions are possible.
        unique_filename = filename # Consider making this unique later

        # Get the configured upload path
        upload_folder = current_app.config['UPLOAD_FOLDER']
        # Ensure the upload folder exists (create if it doesn't)
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, unique_filename)
        try:
            file.save(filepath)
            return unique_filename # Return the filename saved
        except Exception as e:
            print(f"Error saving file {unique_filename}: {e}")
            flash(f"Error saving image file: {e}", "danger")
            return None
    elif file:
        # File was uploaded but extension not allowed
        flash("Invalid image file type. Allowed types are: {}.".format(
              ', '.join(current_app.config['ALLOWED_EXTENSIONS'])), "warning")
        return None
    return None # No file uploaded or error occurred

@main_bp.route("/products", methods=["GET"])
def browse_products():
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()
    # Changed join from 'users' to 'user' to match the renamed table (already done)
    query = ProductListing.query.filter_by(status='active').join(User, ProductListing.user_id == User.id)

    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(db.or_(ProductListing.name.ilike(search_term), ProductListing.description.ilike(search_term)))
    if category_filter:
        query = query.filter(ProductListing.category.ilike(f"%{category_filter}%"))

    categories = db.session.query(ProductListing.category).filter(ProductListing.category.isnot(None)).distinct().order_by(ProductListing.category).all()
    category_list = [cat[0] for cat in categories]

    products = query.order_by(ProductListing.created_at.desc()).all()

    # Get cart item count for display in navbar/header (optional)
    cart_item_count = 0
    if current_user.is_authenticated:
        user_cart = Cart.query.filter_by(user_id=current_user.id).first()
        if user_cart:
            cart_item_count = user_cart.items.count()

    return render_template("products_browse.html",
                           products=products,
                           search=search_query,
                           selected_category=category_filter,
                           categories=category_list,
                           cart_item_count=cart_item_count) # Pass count to template


# --- Core Routes ---
# (index, market_prices, browse_products remain unchanged)
@main_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@main_bp.route("/market-prices", methods=["GET"])
def market_prices():
    current_datetime_str = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p")
    search_query = request.args.get("search", "").strip()
    query = MarketPrice.query
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(db.or_(MarketPrice.name.ilike(search_term), MarketPrice.category.ilike(search_term)))
    official_prices = query.order_by(MarketPrice.category, MarketPrice.name).all()
    return render_template("market_prices.html", current_datetime=current_datetime_str, market_prices=official_prices, search=search_query)

# --- Authentication Routes ---
# (register, login, logout )

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    # ... (Keep existing register function code) ...
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form_data_on_error = {}
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password')
            phone_number = request.form.get('phone_number', '').strip()
            age_str = request.form.get('age', '').strip()
            gender = request.form.get('gender', '').strip()
            address = request.form.get('address', '').strip()
            form_role_selection = request.form.get('role')
            farmer_type = request.form.get('farmer_type', '').strip() if form_role_selection == 'farmer' else None
            form_data_on_error = request.form
            errors = []
            if not username: errors.append("Username is required.")
            if not email: errors.append("Email is required.")
            if not password: errors.append("Password is required.")
            if not form_role_selection: errors.append("Please select whether you are a Buyer or a Farmer.")
            elif form_role_selection == 'farmer' and not farmer_type: errors.append('Please specify your farmer type if registering as a farmer.')
            age = None
            if age_str:
                if age_str.isdigit():
                    age = int(age_str)
                    if age < 0: errors.append("Age cannot be negative.")
                else: errors.append("Age must be a number.")
            if not errors and User.query.filter((User.username == username) | (User.email == email)).first(): errors.append('Username or Email already exists.')
            if errors:
                for error in errors: flash(error, 'danger')
                return render_template('register.html', form_data=form_data_on_error)
            db_role = 'user' if form_role_selection == 'buyer' else 'farmer'
            user_data = {'username': username,'email': email,'phone_number': phone_number or None,'age': age,'gender': gender or None,'address': address or None,'role': db_role,'farmer_type': farmer_type}
            user = User(**user_data)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred during registration: {str(e)}', 'danger')
            print(f"Registration Error: {e}")
            return render_template('register.html', form_data=form_data_on_error)
    return render_template('register.html', form_data={})


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login successful!', 'success')

            next_param = request.args.get('next')
            redirect_url = None

            if next_param:
                # Use standard library urlparse
                parsed_next = urlparse(next_param)

                # Check if the path starts with /cart/add/
                if parsed_next.path and parsed_next.path.startswith('/cart/add/'):
                    # Redirect to products page instead of the POST-only route
                    redirect_url = url_for('main.browse_products')
                    flash('You are now logged in. Please add the item to your cart again.', 'info')
                else:
                    # Check if the next URL is safe (relative or same host)
                    # Use standard library urljoin
                    test_url = urljoin(request.host_url, next_param)
                    # Use urlparse again to check the netloc (host)
                    if urlparse(test_url).netloc == urlparse(request.host_url).netloc:
                         redirect_url = next_param
                    else:
                        # If 'next' URL is external or unsafe, ignore it
                         print(f"Ignoring unsafe next parameter: {next_param}")
                         redirect_url = None # Ensure it falls back to default

            # If no 'next' or it was unsafe/handled above, determine default redirect
            if not redirect_url:
                 redirect_url = url_for('main.admin_dashboard') if user.is_admin else \
                               url_for('main.farmer_manage_listings') if user.is_farmer else \
                               url_for('main.browse_products') if user.is_buyer else \
                               url_for('main.index') # Default fallback

            return redirect(redirect_url)

        else:
            flash('Invalid email or password.', 'danger')

    # GET request
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

# --- User/Farmer/Buyer Dashboard & Profile Routes ---
#User/Buyer Routes
@main_bp.route('/dashboard')
@login_required
def user_dashboard():
    # Redirect buyer to the product Browse page instead of a generic dashboard
    if current_user.is_admin:
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.is_farmer:
        return redirect(url_for('main.farmer_manage_listings'))
    elif current_user.is_buyer:
        # flash('Welcome! Browse products below.', 'info') # Optional flash message
        return redirect(url_for('main.browse_products')) # Redirect buyers here
    else:
         # Fallback for generic users if any exist
         flash('Accessing generic user dashboard.', 'info')
         # You might want a simple profile page here instead
         return render_template('user_profile.html', user=current_user)


# --- Farmer Product Listing Management ---
@main_bp.route('/farmer/listings')
@login_required
def farmer_manage_listings():
    if not current_user.is_farmer:
        flash('Access denied. This section is for farmers only.', 'warning')
        return redirect(url_for('main.index'))
    listings = ProductListing.query.filter_by(user_id=current_user.id).order_by(ProductListing.created_at.desc()).all()
    return render_template('farmer/manage_listings.html', listings=listings)

@main_bp.route('/farmer/listings/add', methods=['GET', 'POST'])
@login_required
def farmer_add_listing():
    if not current_user.is_farmer: abort(403)
    if request.method == 'POST':
        # --- Handle File Upload ---
        image_file = request.files.get('image_file')
        saved_filename = None
        if image_file and image_file.filename != '':
            saved_filename = save_product_image(image_file)
            if saved_filename is None:
                # An error occurred during saving (e.g., invalid type), return form
                 return render_template('farmer/add_listing.html', form_data=request.form)
        # --- End File Upload Handling ---

        try:
            # (Get other form data: name, desc, category, etc.)
            name = request.form.get('name', '').strip(); description = request.form.get('description', '').strip(); category = request.form.get('category', '').strip(); price_str = request.form.get('price', '').strip(); unit = request.form.get('unit', '').strip(); quantity_str = request.form.get('quantity_available', '').strip()
            errors = []; price = None; quantity = None
            # (Validation logic remains the same)
            if not name: errors.append("Product name required.")
            if not category: errors.append("Category required.")
            if not unit: errors.append("Unit required.")
            if not price_str: errors.append("Price required.")
            else: 
                try: price = float(price_str); assert price >= 0 
                except: errors.append("Invalid price.")
            if not quantity_str: errors.append("Quantity required.")
            else: 
                try: quantity = float(quantity_str); assert quantity >= 0 
                except: errors.append("Invalid quantity.")

            if errors:
                for e in errors: flash(e, 'danger')
                return render_template('farmer/add_listing.html', form_data=request.form)

            new_listing = ProductListing(
                name=name, description=description, category=category, price=price, unit=unit,
                quantity_available=quantity,
                image_filename=saved_filename, # Save the filename to the DB
                status='active',
                user_id=current_user.id
            )
            db.session.add(new_listing)
            db.session.commit()
            flash('Product listing added and is now active!', 'success')
            return redirect(url_for('main.farmer_manage_listings'))
        except Exception as e:
            db.session.rollback(); flash(f'Error adding listing: {str(e)}', 'danger'); print(f"Add Listing Error: {e}")
            # Clean up uploaded file if DB commit failed? (More advanced)
            return render_template('farmer/add_listing.html', form_data=request.form)
    return render_template('farmer/add_listing.html', form_data={})

@main_bp.route('/farmer/listings/edit/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def farmer_edit_listing(listing_id):
    listing = ProductListing.query.get_or_404(listing_id)
    if not current_user.is_farmer or listing.user_id != current_user.id: abort(403)

    if request.method == 'POST':
        saved_filename = listing.image_filename # Keep old filename by default
        remove_image_flag = request.form.get('remove_image') == '1'

        # --- Handle File Upload ---
        image_file = request.files.get('image_file')
        if image_file and image_file.filename != '':
            # User uploaded a new file
            new_filename = save_product_image(image_file)
            if new_filename:
                # TODO: Delete old image file if it exists and is different (optional cleanup)
                # if saved_filename and saved_filename != new_filename:
                #    old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
                #    if os.path.exists(old_filepath): os.remove(old_filepath)
                saved_filename = new_filename # Update filename to the new one
            else:
                # Error saving new file, return form
                return render_template('farmer/edit_listing.html', listing=listing, form_data=request.form)
        elif remove_image_flag:
             # TODO: Delete old image file if it exists (optional cleanup)
             # if saved_filename:
             #    old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
             #    if os.path.exists(old_filepath): os.remove(old_filepath)
             saved_filename = None # Remove filename from DB
        # --- End File Upload Handling ---

        try:
            # (Get other form data)
            name = request.form.get('name', '').strip(); description = request.form.get('description', '').strip(); category = request.form.get('category', '').strip(); price_str = request.form.get('price', '').strip(); unit = request.form.get('unit', '').strip(); quantity_str = request.form.get('quantity_available', '').strip(); new_status = request.form.get('status')
            errors = []; price = None; quantity = None
            # (Validation logic remains the same)
            if not name: errors.append("Product name required.")
            if not category: errors.append("Category required.")
            if not unit: errors.append("Unit required.")
            if not price_str: errors.append("Price required.")
            else: 
                try: price = float(price_str); assert price >= 0 
                except: errors.append("Invalid price.")
            if not quantity_str: errors.append("Quantity required.")
            else: 
                try: quantity = float(quantity_str); assert quantity >= 0 
                except: errors.append("Invalid quantity.")

            if errors:
                for e in errors: flash(e, 'danger')
                return render_template('farmer/edit_listing.html', listing=listing, form_data=request.form)

            # Update listing fields
            listing.name = name; listing.description = description; listing.category = category; listing.price = price; listing.unit = unit; listing.quantity_available = quantity;
            listing.image_filename = saved_filename # Update filename
            farmer_allowed_statuses = ['active', 'inactive', 'sold_out']
            if new_status in farmer_allowed_statuses:
                 listing.status = new_status
            listing.updated_at = datetime.utcnow()

            db.session.commit()
            flash('Product listing updated successfully!', 'success')
            return redirect(url_for('main.farmer_manage_listings'))
        except Exception as e:
            db.session.rollback(); flash(f'Error updating listing: {str(e)}', 'danger'); print(f"Edit Listing Error: {e}")
            return render_template('farmer/edit_listing.html', listing=listing, form_data=request.form)

    # GET request
    return render_template('farmer/edit_listing.html', listing=listing, form_data=listing.__dict__)

# (farmer_delete_listing - Consider deleting associated image file)
@main_bp.route('/farmer/listings/delete/<int:listing_id>', methods=['POST'])
@login_required
def farmer_delete_listing(listing_id):
    listing = ProductListing.query.get_or_404(listing_id)
    if not current_user.is_farmer or listing.user_id != current_user.id: abort(403)
    image_to_delete = listing.image_filename # Get filename before deleting DB record
    try:
        db.session.delete(listing); db.session.commit()
        # --- Delete Image File After DB Commit ---
        if image_to_delete:
            try:
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], image_to_delete)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Deleted image file: {filepath}")
            except Exception as img_del_e:
                 print(f"Error deleting image file {image_to_delete}: {img_del_e}")
        # --- End Delete Image File ---
        flash('Product listing deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error deleting listing: {str(e)}', 'danger'); print(f"Delete Listing Error: {e}")
    return redirect(url_for('main.farmer_manage_listings'))


# --- Route to Serve Uploaded Images ---
@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serves files from the UPLOAD_FOLDER."""
    # Use send_from_directory for security
    # It prevents accessing files outside the specified directory
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        abort(404) # Or log an error - upload folder not configured
    # Check if file exists to provide a cleaner 404 if needed
    if not os.path.exists(os.path.join(upload_folder, filename)):
         abort(404)
    return send_from_directory(upload_folder, filename)


# --- Admin Routes ---
# (admin_required decorator remains the same)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# (admin_dashboard, admin_manage_listings, admin_update_listing_status remain unchanged)
@main_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    user_count = User.query.count()
    active_listings = ProductListing.query.filter_by(status='active').count()
    inactive_listings = ProductListing.query.filter_by(status='inactive').count()
    return render_template('admin/admin_dashboard.html', user_count=user_count, active_listings=active_listings, inactive_listings=inactive_listings)

@main_bp.route('/admin/listings', methods=['GET'])
@login_required
@admin_required
def admin_manage_listings():
    status_filter = request.args.get('status', '').strip()
    query = ProductListing.query.join(User, ProductListing.user_id == User.id).order_by(ProductListing.created_at.desc())
    if status_filter: query = query.filter(ProductListing.status == status_filter)
    listings = query.all()
    possible_statuses = ['active', 'inactive', 'rejected', 'sold_out']
    return render_template('admin/manage_listings.html', listings=listings, possible_statuses=possible_statuses, selected_status=status_filter)

@main_bp.route('/admin/listings/update_status/<int:listing_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_listing_status(listing_id):
    listing = ProductListing.query.get_or_404(listing_id)
    new_status = request.form.get('status')
    allowed_statuses = ['active', 'inactive', 'rejected', 'sold_out']
    if new_status not in allowed_statuses:
        flash('Invalid status provided.', 'danger')
        return redirect(url_for('main.admin_manage_listings', status=listing.status))
    try:
        listing.status = new_status; listing.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Listing "{listing.name}" status updated to {new_status}.', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error updating listing status: {str(e)}', 'danger'); print(f"Admin Update Status Error: {e}")
    redirect_url = url_for('main.admin_manage_listings', status=request.args.get('status_filter', ''))
    return redirect(redirect_url)


# --- Admin Management Routes ---
# (admin_manage_prices, edit_price, delete_price)
@main_bp.route('/admin/prices')
@login_required
@admin_required
def admin_manage_prices():
    prices = MarketPrice.query.order_by(MarketPrice.category, MarketPrice.name).all()
    return render_template('admin/manage_prices.html', prices=prices)

@main_bp.route('/admin/prices/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_price():
    if request.method == 'POST':
        try:
            name = request.form.get('name','').strip()
            category = request.form.get('category','').strip()
            price_str = request.form.get('price','').strip()
            unit = request.form.get('unit','').strip()
            location = request.form.get('location','').strip() or None
            errors = []
            price = None

            if not name: errors.append("Name required.")
            if not category: errors.append("Category required.")
            if not unit: errors.append("Unit required.")

            # --- Corrected Price Validation ---
            if not price_str:
                errors.append("Price required.")
            else:
                # Indent try/except block correctly
                try:
                    price = float(price_str)
                    if price < 0: errors.append("Price cannot be negative.")
                except ValueError:
                    errors.append("Invalid price format.")
            # --- End Corrected Price Validation ---

            if errors:
                for e in errors: flash(e, 'danger')
                return render_template('admin/add_price.html', form_data=request.form)

            new_price = MarketPrice(name=name, category=category, price=price, unit=unit, location=location)
            db.session.add(new_price); db.session.commit()
            flash('Market price added successfully!', 'success')
            return redirect(url_for('main.admin_manage_prices'))
        except Exception as e:
            db.session.rollback(); flash(f'Error adding market price: {str(e)}', 'danger'); print(f"Add Price Error: {e}")
            return render_template('admin/add_price.html', form_data=request.form)
    return render_template('admin/add_price.html', form_data={})

@main_bp.route('/admin/prices/edit/<int:price_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_price(price_id):
    price = MarketPrice.query.get_or_404(price_id)
    if request.method == 'POST':
        try:
            # Add validation similar to add_price if needed
            historical_entry = MarketPriceHistory(market_price_id=price.id, price=price.price, date=price.updated_at)
            db.session.add(historical_entry)
            price.name = request.form.get('name','').strip(); price.category = request.form.get('category','').strip(); price.price = float(request.form.get('price',0)); price.unit = request.form.get('unit','').strip(); price.location = request.form.get('location','').strip() or None; price.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Market price updated successfully!', 'success')
            return redirect(url_for('main.admin_manage_prices'))
        except Exception as e:
            db.session.rollback(); flash(f'Error updating market price: {str(e)}', 'danger'); print(f"Edit Price Error: {e}")
            return render_template('admin/edit_price.html', price=price, form_data=request.form)
    return render_template('admin/edit_price.html', price=price, form_data=price.__dict__)

@main_bp.route('/admin/prices/delete/<int:price_id>', methods=['POST'])
@login_required
@admin_required
def delete_price(price_id):
    price = MarketPrice.query.get_or_404(price_id)
    try:
        MarketPriceHistory.query.filter_by(market_price_id=price.id).delete()
        db.session.delete(price); db.session.commit()
        flash('Market price deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error deleting market price: {str(e)}', 'danger'); print(f"Delete Price Error: {e}")
    return redirect(url_for('main.admin_manage_prices'))


# --- Farmers Management Routes ---

@main_bp.route('/farm/crops/add', methods=['GET', 'POST'])
@login_required
def add_crop():
    if not current_user.is_farmer: flash("Only registered farmers can manage crops.", "warning"); return redirect(url_for('main.user_dashboard'))
    if request.method == 'POST':
        try: name = request.form['name']; quantity = float(request.form['quantity']); unit = request.form['unit']; new_crop = Crop(name=name, quantity=quantity, unit=unit, user_id=current_user.id); db.session.add(new_crop); db.session.commit(); flash('Crop added successfully!', 'success')
        except Exception as e: db.session.rollback(); flash(f'Error adding crop: {e}', 'danger')
        return redirect(url_for('main.user_dashboard'))
    # Ensure 'farm/add_crop.html' exists
    return render_template('farm/add_crop.html')

@main_bp.route('/farm/crops/edit/<int:crop_id>', methods=['GET', 'POST'])
@login_required
def edit_crop(crop_id): crop = Crop.query.get_or_404(crop_id); flash("Edit crop functionality not implemented.", "info"); return redirect(url_for('main.user_dashboard'))

@main_bp.route('/farm/crops/delete/<int:crop_id>', methods=['POST'])
@login_required
def delete_crop(crop_id): crop = Crop.query.get_or_404(crop_id); flash("Delete crop functionality not implemented.", "info"); return redirect(url_for('main.user_dashboard'))

@main_bp.route('/farm/livestock/add', methods=['GET', 'POST'])
@login_required
def add_livestock(): flash("Add livestock functionality not implemented.", "info"); return redirect(url_for('main.user_dashboard'))

@main_bp.route('/farm/livestock/edit/<int:livestock_id>', methods=['GET', 'POST'])
@login_required
def edit_livestock(livestock_id): livestock = Livestock.query.get_or_404(livestock_id); flash("Edit livestock functionality not implemented.", "info"); return redirect(url_for('main.user_dashboard'))

@main_bp.route('/farm/livestock/delete/<int:livestock_id>', methods=['POST'])
@login_required
def delete_livestock(livestock_id): livestock = Livestock.query.get_or_404(livestock_id); flash("Delete livestock functionality not implemented.", "info"); return redirect(url_for('main.user_dashboard'))

@main_bp.route('/farmer/dashboard')
@login_required
def farmer_dashboard():
    if not current_user.is_farmer:
        flash('Access denied. This section is for farmers only.', 'warning')
        return redirect(url_for('main.index'))
    return render_template('farmer/dashboard.html')

@main_bp.route('/farmer/notes', methods=['GET', 'POST'])
@login_required
def farmer_notes():
    if not current_user.is_farmer:
        flash('Access denied. Farmers only.', 'danger')
        return redirect(url_for('main.index'))

    note = FarmerNote.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash('Note cannot be empty.', 'warning')
        else:
            if note:
                note.content = content
            else:
                note = FarmerNote(content=content, user_id=current_user.id)
                db.session.add(note)
            db.session.commit()
            flash('Note saved successfully.', 'success')
        return redirect(url_for('main.farmer_notes'))

    return render_template('farmer/notes.html', note=note)


# --- Admin User Management ---

@main_bp.route('/admin/users')
@login_required
@admin_required
def admin_users(): users = User.query.order_by(User.role, User.username).all(); return render_template('admin/users.html', users=users)

@main_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            new_role = request.form['role']
            if user.id == current_user.id and new_role != 'admin': flash('Cannot change your own role from admin.', 'danger'); return render_template('admin/edit_user.html', user=user)
            user.username = request.form['username']; user.email = request.form['email']; user.phone_number = request.form['phone_number']; user.role = new_role; user.age = int(request.form['age']) if request.form['age'] else None; user.gender = request.form['gender']; user.address = request.form['address']; user.farmer_type = request.form['farmer_type'] or None
            new_password = request.form.get('new_password')
            if new_password: user.set_password(new_password)
            db.session.commit(); flash('User updated successfully!', 'success')
            return redirect(url_for('main.admin_users'))
        except Exception as e: db.session.rollback(); flash(f'Error updating user: {str(e)}', 'danger'); print(f"Edit User Error: {e}"); return render_template('admin/edit_user.html', user=user)
    return render_template('admin/edit_user.html', user=user)

@main_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if current_user.id == user_id: flash('Cannot delete your own admin account!', 'danger'); return redirect(url_for('main.admin_users'))
    user = User.query.get_or_404(user_id)
    try: db.session.delete(user); db.session.commit(); flash('User deleted successfully!', 'success')
    except Exception as e: db.session.rollback(); flash(f'Error deleting user: {str(e)}', 'danger'); print(f"Delete User Error: {e}")
    return redirect(url_for('main.admin_users'))



# --- Cart && Order Routes ---

@main_bp.route('/cart/add/<int:listing_id>', methods=['POST'])
@login_required
def add_to_cart(listing_id):
    # --- Check if user is a buyer ---
    # print(f"DEBUG: Current User Role: {current_user.role}, Farmer Type: {current_user.farmer_type}, Is Buyer: {current_user.is_buyer}") # Optional Debugging
    if not current_user.is_buyer:
        flash("Only buyers can add items to the cart.", "warning")
        return redirect(request.referrer or url_for('main.browse_products'))

    product = ProductListing.query.get_or_404(listing_id)
    quantity_str = request.form.get('quantity', '1')

    try:
        quantity = float(quantity_str) # Or int()
        if quantity <= 0:
            flash("Quantity must be positive.", "warning")
            # Redirect back to the product page or browse page
            return redirect(request.referrer or url_for('main.browse_products'))

        # Check available quantity BEFORE checking if item is in cart
        if quantity > product.quantity_available:
            flash(f"Only {product.quantity_available} {product.unit} available.", "warning")
            # Redirect to referrer (likely product browse or detail page)
            return redirect(request.referrer or url_for('main.browse_products'))

    except ValueError:
        flash("Invalid quantity.", "danger")
        return redirect(request.referrer or url_for('main.browse_products'))

    # Check if product is active
    if product.status != 'active':
        flash("This product is no longer available.", "warning")
        return redirect(request.referrer or url_for('main.browse_products'))

    # Get or create user's cart
    user_cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not user_cart:
        user_cart = Cart(user_id=current_user.id)
        db.session.add(user_cart)
        # You might need to flush to get the cart ID if adding item immediately
        # db.session.flush() # Or commit later

    # Check if item already exists in cart
    # Ensure user_cart exists before accessing its id
    cart_item = None
    if user_cart:
         cart_item = CartItem.query.filter_by(cart_id=user_cart.id, product_id=product.id).first()


    if cart_item:
        # Update quantity
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.quantity_available:
            flash(f"Cannot add {quantity} {product.unit}; only {product.quantity_available - cart_item.quantity:.1f} more available (you have {cart_item.quantity:.1f} in cart, total {product.quantity_available}).", "warning")
            # Don't proceed if exceeds available
            return redirect(request.referrer or url_for('main.browse_products'))
        else:
            cart_item.quantity = new_quantity
            flash(f"Updated {product.name} quantity in cart.", "success")
    else:
        # Add new item (we already checked quantity > product.quantity_available earlier)
        # Check again just in case cart didn't exist before flush
        if quantity > product.quantity_available:
             flash(f"Cannot add {quantity} {product.unit}; only {product.quantity_available} available.", "warning")
             return redirect(request.referrer or url_for('main.browse_products')) # Add redirect here

        # Ensure user_cart has an ID before creating CartItem
        if not user_cart.id:
             db.session.flush() # Assigns ID to user_cart if it's new

        cart_item = CartItem(cart_id=user_cart.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)
        flash(f"Added {product.name} to cart.", "success")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding item to cart: {str(e)}", "danger")
        print(f"Cart Add Error: {e}") # Keep print for debugging

    # Redirect back to the page they came from
    return redirect(request.referrer or url_for('main.browse_products'))

@main_bp.route('/cart', methods=['GET'])
@login_required
def view_cart():
    if not current_user.is_buyer:
        flash("Only buyers can view the cart.", "warning")
        return redirect(url_for('main.index'))

    user_cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = []
    cart_total = 0.0

    if user_cart:
        cart_items = user_cart.items.options(
            db.joinedload(CartItem.product).joinedload(ProductListing.farmer)
        ).all()
        cart_total = user_cart.total_price

    return render_template('cart/view_cart.html', cart_items=cart_items, cart_total=cart_total)

@main_bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    if not current_user.is_buyer: abort(403) # Or redirect

    cart_item = CartItem.query.get_or_404(item_id)
    # Eager load product for quantity check
    cart_item = CartItem.query.options(db.joinedload(CartItem.product)).get(item_id)
    if not cart_item: abort(404)


    user_cart = Cart.query.filter_by(user_id=current_user.id).first()

    if not user_cart or cart_item.cart_id != user_cart.id:
        flash("Invalid cart item.", "danger")
        return redirect(url_for('main.view_cart'))

    quantity_str = request.form.get('quantity')
    try:
        quantity = float(quantity_str) 
        if quantity <= 0:
            db.session.delete(cart_item)
            flash("Item removed from cart.", "success")
        elif quantity > cart_item.product.quantity_available:
             flash(f"Cannot update: only {cart_item.product.quantity_available} {cart_item.product.unit} available.", "warning")

        else:
            cart_item.quantity = quantity
            flash("Cart updated.", "success")
        db.session.commit()
    except ValueError:
        flash("Invalid quantity.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating cart: {str(e)}", "danger")
        print(f"Cart Update Error: {e}") # Keep print for debugging

    return redirect(url_for('main.view_cart'))

@main_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_cart_item(item_id):
    if not current_user.is_buyer: abort(403)

    cart_item = CartItem.query.get_or_404(item_id)
    user_cart = Cart.query.filter_by(user_id=current_user.id).first()

    # Ensure the item belongs to the current user's cart
    if not user_cart or cart_item.cart_id != user_cart.id:
        flash("Invalid cart item.", "danger")
        return redirect(url_for('main.view_cart'))

    try:
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from cart.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing item: {str(e)}", "danger")
        print(f"Cart Remove Error: {e}")

    return redirect(url_for('main.view_cart'))

# --- Checkout and Order Routes ---

@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Ensure only buyers can checkout
    if not current_user.is_buyer:
        flash("Only buyers can proceed to checkout.", "warning")
        return redirect(url_for('main.browse_products'))

    # Get user's cart
    user_cart = Cart.query.filter_by(user_id=current_user.id).first()

    # Check if cart exists and has items
    if not user_cart or not user_cart.items.first():
        flash("Your cart is empty. Please add items before checking out.", "warning")
        # Redirect to product Browse or cart page
        return redirect(url_for('main.browse_products'))

    # Eager load products for display and price calculation
    cart_items = user_cart.items.options(db.joinedload(CartItem.product)).all()
    # Ensure cart_total uses Decimal if your total_price property returns it
    cart_total_decimal = decimal.Decimal(str(user_cart.total_price)) # Convert cart total safely to Decimal

    if request.method == 'POST':
        # --- Process the Checkout Form ---
        recipient_name = request.form.get('recipient_name', '').strip()
        recipient_phone = request.form.get('recipient_phone', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        payment_method = request.form.get('payment_method') # e.g., 'cod', 'gcash_simulated'

        # --- Basic Validation ---
        errors = []
        if not recipient_name: errors.append("Recipient name is required.")
        if not recipient_phone: errors.append("Recipient phone number is required.")
        # Add more specific phone validation if needed
        if not shipping_address: errors.append("Shipping address is required.")
        if not payment_method: errors.append("Please select a payment method.")

        if errors:
            for error in errors: flash(error, 'danger')
            # Re-render checkout page with errors and existing form data
            return render_template('checkout/checkout.html',
                                   cart_items=cart_items,
                                   cart_total=cart_total_decimal, # Pass Decimal total
                                   form_data=request.form, # Pass submitted data back
                                   user=current_user)
        # --- End Validation ---

        # --- Create Order (Transaction Block) ---
        try:
            # 1. Final Stock Check (Critical)
            for item in cart_items:
                # Refresh product data from DB within transaction
                # Using with_for_update() can lock rows in some DBs (e.g., PostgreSQL)
                # product = ProductListing.query.with_for_update().get(item.product_id)
                product = ProductListing.query.get(item.product_id) # Simpler approach first
                if not product or product.quantity_available < item.quantity:
                    # If stock is insufficient, rollback and redirect to cart with error
                    flash(f"Insufficient stock for '{item.product.name}'. Available: {product.quantity_available if product else 0}. Please update your cart.", "danger")
                    db.session.rollback()
                    return redirect(url_for('main.view_cart'))

            # 2. Simulate Payment
            print(f"Simulating payment via: {payment_method}")
            # In a real app: Call payment gateway API here. If it fails, raise Exception.
            payment_successful = True # Assume success for simulation

            if not payment_successful:
                 raise Exception("Simulated payment failed.")

            # 3. Create Order Record
            new_order = Order(
                user_id=current_user.id,
                total_price=cart_total_decimal, # Store the Decimal total
                status='Completed', # Set status (e.g., 'Pending' if payment needs async confirmation)
                recipient_name=recipient_name,
                recipient_phone=recipient_phone,
                shipping_address=shipping_address
                # payment_method = payment_method # Optionally store payment method
            )
            db.session.add(new_order)
            db.session.flush() # Assign ID to new_order for OrderItems

            # 4. Create OrderItem Records and Decrease Stock
            for item in cart_items:
                # Create OrderItem with snapshot data
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_listing_id=item.product_id,
                    product_name=item.product.name,
                    product_unit=item.product.unit,
                    quantity=item.quantity,
                    # Convert product price to Decimal for storing in OrderItem
                    price_per_unit=decimal.Decimal(str(item.product.price))
                )
                db.session.add(order_item)

                # Decrease stock in ProductListing (fetch again for safety within transaction)
                product = ProductListing.query.get(item.product_id)
                if product: # Should always be found based on earlier check
                    product.quantity_available -= item.quantity
                    # Optional: Prevent negative stock
                    if product.quantity_available < 0:
                        product.quantity_available = 0
                    # Optional: Update product status if stock runs out
                    # if product.quantity_available == 0:
                    #     product.status = 'sold_out'
                else:
                    # This case indicates a problem (product disappeared mid-transaction)
                    raise Exception(f"Product ID {item.product_id} not found during stock update.")


            # 5. Clear the Cart
            # Delete cart items efficiently. Deleting the cart cascades.
            db.session.delete(user_cart)

            # 6. Commit Transaction
            db.session.commit()

            flash('Order placed successfully!', 'success')
            # Redirect to confirmation page
            return redirect(url_for('main.order_confirmation', order_id=new_order.id))

        except Exception as e:
            # Rollback transaction if any part fails
            db.session.rollback()
            flash(f'Error placing order: {str(e)}', 'danger')
            print(f"Checkout Processing Error: {e}")
            # Redirect back to checkout or cart page
            return redirect(url_for('main.checkout'))

    # --- GET Request: Show Checkout Page ---
    # Pre-fill form data with user's info from profile if available
    default_form_data = {
        'recipient_name': current_user.username,
        'recipient_phone': current_user.phone_number or '',
        'shipping_address': current_user.address or ''
    }
    return render_template('checkout/checkout.html',
                           cart_items=cart_items,
                           cart_total=cart_total_decimal, # Pass Decimal total
                           form_data=default_form_data, # Pass defaults for GET
                           user=current_user)


@main_bp.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    # Fetch the specific order, ensuring it belongs to the current user (or admin)
    # Eager load items for display efficiency
    order = Order.query.options(
        db.joinedload(Order.items) # Use joinedload to fetch items in the same query
    ).filter(Order.id == order_id).first_or_404() # Find the order or return 404

    # Security check: Ensure user owns the order or is admin
    if order.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to view this order.", "danger")
        return redirect(url_for('main.index'))

    return render_template('checkout/order_confirmation.html', order=order)


@main_bp.route('/orders')
@login_required
def order_history():
    # Fetch all orders placed by the currently logged-in user
    orders = Order.query.filter_by(user_id=current_user.id)\
                 .order_by(Order.created_at.desc())\
                 .all() # Fetch all matching orders

    # Render the order history template
    return render_template('checkout/order_history.html', orders=orders)


# --- Messaging Routes ---

# --- Context Processor for Unread Messages ---
@main_bp.app_context_processor
def inject_unread_message_count():
    """Injects the count of unread messages into all templates for the current user."""
    if current_user.is_authenticated:
        unread_count = Message.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).count()
        return dict(unread_message_count_global=unread_count)
    return dict(unread_message_count_global=0)

@main_bp.route('/messages/start/<int:listing_id>', methods=['POST'])
@login_required
def start_conversation(listing_id):
    """
    Initiates a conversation with the farmer of a specific product listing.
    If a conversation already exists, it redirects to it.
    """
    if not current_user.is_buyer: # Only buyers can initiate about a product
        flash("Only buyers can initiate conversations about products.", "warning")
        return redirect(request.referrer or url_for('main.browse_products'))

    listing = ProductListing.query.get_or_404(listing_id)
    farmer = listing.farmer # Assuming 'farmer' is the backref from ProductListing to User

    if not farmer:
        flash("Farmer not found for this listing.", "danger")
        return redirect(request.referrer or url_for('main.browse_products'))

    if current_user.id == farmer.id:
        flash("You cannot start a conversation with yourself about your own listing.", "warning")
        return redirect(request.referrer or url_for('main.browse_products'))

    # Check if a conversation already exists for this product between these users
    conversation = Conversation.query.filter_by(
        product_listing_id=listing.id,
        buyer_id=current_user.id,
        farmer_id=farmer.id
    ).first()

    if not conversation:
        # Create a new conversation
        conversation = Conversation(
            product_listing_id=listing.id,
            buyer_id=current_user.id,
            farmer_id=farmer.id
        )
        db.session.add(conversation)
        # Optionally, send an initial message or a system message
        initial_message_content = request.form.get('initial_message', '').strip()
        if not initial_message_content:
            initial_message_content = f"Hi {farmer.username}, I'm interested in your product: {listing.name}."

        # Create the first message from the buyer
        first_message = Message(
            conversation_id=conversation.id, # Will be set after flush if conversation is new
            sender_id=current_user.id,
            recipient_id=farmer.id,
            content=initial_message_content
        )
        # If conversation is new, we need its ID for the message.
        # Flushing assigns the ID.
        db.session.flush() # Get conversation.id
        first_message.conversation_id = conversation.id # Ensure it's set
        db.session.add(first_message)

        conversation.updated_at = datetime.utcnow() # Update conversation timestamp

        try:
            db.session.commit()
            flash(f"Conversation started with {farmer.username} regarding '{listing.name}'.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error starting conversation: {str(e)}", "danger")
            print(f"Error starting conversation: {e}")
            return redirect(request.referrer or url_for('main.browse_products'))
    else:
        # Conversation already exists, just update its timestamp if a new message is implied
        # For now, just redirect. Sending a message will update timestamp.
        flash("Conversation already exists. Redirecting...", "info")


    return redirect(url_for('main.view_conversation', conversation_id=conversation.id))


@main_bp.route('/messages', methods=['GET'])
@login_required
def list_conversations():
    """
    Displays a list of all conversations (inbox) for the current user.
    """
    # Fetch conversations where the current user is either the buyer or the farmer
    conversations = Conversation.query.filter(
        or_(Conversation.buyer_id == current_user.id, Conversation.farmer_id == current_user.id)
    ).order_by(Conversation.updated_at.desc()).all()

    return render_template('messages/conversation_list.html', conversations=conversations)


@main_bp.route('/messages/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
def view_conversation(conversation_id):
    """
    Displays an individual conversation and allows sending new messages.
    """
    conversation = Conversation.query.get_or_404(conversation_id)

    # Security check: Ensure current user is part of this conversation
    if current_user.id != conversation.buyer_id and current_user.id != conversation.farmer_id:
        flash("You do not have permission to view this conversation.", "danger")
        return redirect(url_for('main.list_conversations'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash("Message content cannot be empty.", "warning")
        else:
            # Determine recipient
            recipient_user = conversation.get_other_user(current_user.id)
            if not recipient_user:
                flash("Could not determine message recipient.", "danger")
                return redirect(url_for('main.view_conversation', conversation_id=conversation.id))

            new_message = Message(
                conversation_id=conversation.id,
                sender_id=current_user.id,
                recipient_id=recipient_user.id,
                content=content
            )
            db.session.add(new_message)
            conversation.updated_at = datetime.utcnow() # Update conversation timestamp

            try:
                db.session.commit()
                # flash("Message sent!", "success") # Optional: Can be too noisy
            except Exception as e:
                db.session.rollback()
                flash(f"Error sending message: {str(e)}", "danger")
                print(f"Error sending message: {e}")

        # Redirect to the same page to show the new message (GET request)
        return redirect(url_for('main.view_conversation', conversation_id=conversation.id))

    # GET request: Mark messages as read by the current user in this conversation
    # This is a simplified approach. For unread counts, you'd compare message.recipient_id
    messages_to_mark_read = Message.query.filter_by(
        conversation_id=conversation.id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for msg in messages_to_mark_read:
        msg.is_read = True
    if messages_to_mark_read:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error marking messages as read: {e}")


    # Fetch all messages for display, already ordered by timestamp in model relationship
    messages = conversation.messages # Or .limit(50).all() for pagination later

    other_user = conversation.get_other_user(current_user.id)

    return render_template('messages/conversation_detail.html',
                           conversation=conversation,
                           messages=messages,
                           other_user=other_user)

# --- End Messaging Routes ---

# --- API Routes ---
# (get_price_history remains unchanged)
@main_bp.route('/api/prices/history/<int:price_id>', methods=['GET'])
@login_required
def get_price_history(price_id): price_info = MarketPrice.query.get(price_id); history = MarketPriceHistory.query.filter_by(market_price_id=price_id).order_by(MarketPriceHistory.date.asc()).all(); response = [{'price': float(h.price), 'date': h.date.strftime('%Y-%m-%d %H:%M:%S')} for h in history]; current_price_data = {'price': float(price_info.price), 'date': price_info.updated_at.strftime('%Y-%m-%d %H:%M:%S')}; return jsonify({'history': response, 'current': current_price_data})
# --- Error Handlers ---
# (forbidden_error, not_found_error remain unchanged)
@main_bp.app_errorhandler(403)
def forbidden_error(error): flash('You do not have permission to access this page.', 'danger'); return redirect(url_for('main.index') if current_user.is_authenticated else url_for('main.login'))
@main_bp.app_errorhandler(404)
def not_found_error(error): return render_template('errors/404.html'), 404
@main_bp.app_errorhandler(500)
def internal_error(error):
    print(f"Internal Server Error encountered: {error}")
    try:
        db.session.rollback()
        print("Database session rolled back.")
    except Exception as rb_error:
        print(f"Error during session rollback: {rb_error}")
    return render_template('errors/500.html'), 500