import os
import logging
from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
load_dotenv()
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "max_overflow": 0,
        "pool_timeout": 30
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = True
    
    # Apply proxy fix for HTTPS in production
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models to ensure tables are created
        from models import User, Product, Allergen, UserAllergen, ProductAllergen, HealthNews
        
        # Create all tables
        db.create_all()
        
        # Import and register routes
        from routes import register_routes
        register_routes(app)
        
        # Seed database with initial data
        from seed_data import seed_database
        seed_database()
    
    return app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
