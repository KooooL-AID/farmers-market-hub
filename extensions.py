from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt # type: ignore
from flask_login import LoginManager # type: ignore
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
