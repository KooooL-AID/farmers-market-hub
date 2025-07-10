from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import decimal

from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    phone_number = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    farmer_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    crops = db.relationship('Crop', backref='owner', lazy=True, cascade="all, delete-orphan")
    livestock = db.relationship('Livestock', backref='owner', lazy=True, cascade="all, delete-orphan")
    product_listings = db.relationship('ProductListing', backref='farmer', lazy=True, cascade="all, delete-orphan")
    notes = db.relationship('FarmerNote', backref='user', lazy=True, cascade="all, delete-orphan")

    conversations_as_farmer = db.relationship(
        'Conversation',
        foreign_keys='Conversation.farmer_id',
        back_populates='farmer',
        cascade="all, delete",
        passive_deletes=True
    )

    conversations_as_buyer = db.relationship(
        'Conversation',
        foreign_keys='Conversation.buyer_id',
        back_populates='buyer',
        cascade="all, delete",
        passive_deletes=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_farmer(self):
        return bool(self.farmer_type)
    
    @property
    def is_buyer(self):
        return self.role == 'user' and not self.farmer_type


    @property
    def is_admin(self):
        return self.role == 'admin'

class FarmerNote(db.Model):
    __tablename__ = 'farmer_note'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Crop(db.Model):
    __tablename__ = 'crop'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Livestock(db.Model):
    __tablename__ = 'livestock'

    id = db.Column(db.Integer, primary_key=True)
    animal_name = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class ProductListing(db.Model):
    __tablename__ = 'product_listing'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    quantity_available = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='pending_approval')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketPrice(db.Model):
    __tablename__ = 'market_price'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketPriceHistory(db.Model):
    __tablename__ = 'market_price_history'

    id = db.Column(db.Integer, primary_key=True)
    market_price_id = db.Column(db.Integer, db.ForeignKey('market_price.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    market_price = db.relationship('MarketPrice', backref=db.backref('history', lazy=True))

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    product_listing_id = db.Column(db.Integer, db.ForeignKey('product_listing.id', ondelete='SET NULL'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product_listing = db.relationship('ProductListing', backref=db.backref('conversations', lazy=True))
    messages = db.relationship(
        'Message',
        back_populates='conversation',
        cascade="all, delete-orphan",
        lazy='dynamic'
    )

    # Updated relationships with back_populates
    buyer = db.relationship(
        'User',
        foreign_keys=[buyer_id],
        back_populates='conversations_as_buyer'
    )
    
    farmer = db.relationship(
        'User',
        foreign_keys=[farmer_id],
        back_populates='conversations_as_farmer'
    )

    def get_other_user(self, current_user_id):
        """
        Returns the other user in the conversation (not the current user).
        If current user is the buyer, returns the farmer. If current user is the farmer, returns the buyer.
        """
        if current_user_id == self.buyer_id:
            return self.farmer
        elif current_user_id == self.farmer_id:
            return self.buyer
        else:
            return None  # Current user is not part of this conversation

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    # ✅ Proper back reference to Conversation
    conversation = db.relationship(
        'Conversation',
        back_populates='messages'
    )

    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])


#Order and Cart Models

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True) # One cart per user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to User (one-to-one)
    user = db.relationship('User', backref=db.backref('cart', uselist=False))
    # Relationship to CartItem (one-to-many)
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def total_price(self):
        """Calculates the total price of all items in the cart."""
        total = decimal.Decimal(0.0)
        for item in self.items:
             # Ensure item.product and item.product.price are not None
            if item.product and item.product.price is not None and item.quantity is not None:
                 total += decimal.Decimal(item.product.price) * decimal.Decimal(item.quantity)
        # Convert back to float for compatibility if necessary, or keep as Decimal
        return float(total)


    def __repr__(self):
        return f"<Cart for User ID {self.user_id}>"

class CartItem(db.Model):
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product_listing.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1.0) # Or db.Integer if whole units only
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to ProductListing
    # Ensures we can easily access product details from the cart item
    product = db.relationship('ProductListing')

    def __repr__(self):
        return f"<CartItem Product ID {self.product_id} Qty {self.quantity} in Cart ID {self.cart_id}>"


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True) # Keep order history if user is deleted
    total_price = db.Column(db.Numeric(10, 2), nullable=False) # Use Numeric for precise currency values
    status = db.Column(db.String(50), nullable=False, default='Pending') # e.g., Pending, Processing, Shipped, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Shipping Information (Simplified)
    shipping_address = db.Column(db.Text, nullable=True)
    recipient_name = db.Column(db.String(100), nullable=True)
    recipient_phone = db.Column(db.String(30), nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('orders', lazy='dynamic'))
    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order ID: {self.id}, UserID: {self.user_id}, Status: {self.status}, Total: {self.total_price}>"

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False) # If order deleted, delete items
    product_listing_id = db.Column(db.Integer, db.ForeignKey('product_listing.id', ondelete='SET NULL'), nullable=True) # Keep item history even if product listing deleted

    # --- Snapshot of product details at time of order ---
    product_name = db.Column(db.String(120), nullable=False)
    product_unit = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False) # Or db.Numeric(10, 3) if precision needed
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False) # Price paid per unit

    # Relationships (backref 'order' defined in Order model)
    # Optional: Link back to original listing for navigation
    product_listing = db.relationship('ProductListing')
    
    @property
    def subtotal(self):
        # Calculate subtotal using Decimal for precision
        try:
            # Convert quantity (Float) and price_per_unit (Numeric/Decimal) safely
            qty_decimal = decimal.Decimal(str(self.quantity))
            price_decimal = decimal.Decimal(self.price_per_unit) # Numeric is already Decimal-like
            return (qty_decimal * price_decimal).quantize(decimal.Decimal("0.01"))
        except (decimal.InvalidOperation, TypeError, ValueError):
            # Handle potential conversion errors if data is unexpected
             print(f"Error calculating subtotal for OrderItem {self.id}")
             return decimal.Decimal("0.00")


    def __repr__(self):
        return f"<OrderItem ID: {self.id}, OrderID: {self.order_id}, Product: {self.product_name}, Qty: {self.quantity}>"