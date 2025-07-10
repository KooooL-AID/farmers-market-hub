import os
from dotenv import load_dotenv
load_dotenv()
# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for session management, CSRF protection, etc.
    # IMPORTANT: Change this to a random, secret value in production!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-you-should-change'

    # Database configuration (adjust as needed)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Disable modification tracking

    # --- Upload Configuration ---
    # Define the folder where uploads will be stored relative to the app's instance path
    # The instance path is typically outside the main app package for security.
    # Flask creates it automatically if it doesn't exist.
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads', 'product_images')

    # Ensure the upload folder exists when the app starts
    # Note: This might be better placed in app factory (__init__.py or app.py)
    # os.makedirs(UPLOAD_FOLDER, exist_ok=True) # See note below

    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Optional: Maximum file size (e.g., 16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 Megabytes

    # --- End Upload Configuration ---

# Note on os.makedirs: Creating the directory directly in config.py might run
# prematurely during imports. It's often safer to ensure the directory exists
# within your application factory (`create_app` in app.py) or just before
# saving a file in your route. We'll add the check in the route logic.
