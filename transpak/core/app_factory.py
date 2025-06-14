"""
Application factory for TransPak AI Quoter
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import config_map


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()


def create_app(config_name=None):
    """Create and configure the Flask application"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    config_class = config_map.get(config_name, config_map['default'])
    app.config.from_object(config_class)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'DEBUG')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Proxy fix for production
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    # Register blueprints
    from ..routes.main_routes import main_bp
    from ..routes.quote_routes import quote_bp
    from ..routes.api_routes import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(quote_bp, url_prefix='/quotes')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        from ..models.database_models import User, Shipment, Quote, QuoteHistory
        db.create_all()
    
    return app