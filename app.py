import os # Import os
from flask import Flask
from config import Config # Import Config class
from extensions import db, login_manager, migrate
from datetime import datetime
from commands import register_commands

def create_app():
    app = Flask(__name__, instance_relative_config=True) # instance_relative_config=True is good practice
    app.config.from_object(Config) # Load config from Config class

    # --- Ensure Upload Folder Exists ---
    # It's generally safer to create the upload folder here or within the route
    # than directly in config.py. Using instance_path is recommended.
    # upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(app.instance_path, 'uploads')) # Default to instance path
    # For simplicity with static serving later, let's keep it relative to app root for now
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        try:
            os.makedirs(upload_folder)
            print(f"Created upload folder: {upload_folder}")
        except OSError as e:
            print(f"Error creating upload folder {upload_folder}: {e}")
    # --- End Folder Check ---


    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'main.login'

    # Set up user_loader
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_id_int = int(user_id)
            return User.query.get(user_id_int)
        except (ValueError, TypeError):
            return None
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {e}")
            return None


    # --- Add Context Processor ---
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}
    # --- End Context Processor ---


    # Import and register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    # Register CLI commands
    register_commands(app)

    return app

# The run.py file should handle creating and running the app instance
