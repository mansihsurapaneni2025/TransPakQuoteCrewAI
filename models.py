from app import db
from datetime import datetime
from sqlalchemy import Text, JSON, Index
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid

class Shipment(db.Model):
    """Model to store shipment information"""
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)  # Optional for backward compatibility
    item_description = db.Column(Text, nullable=False)
    dimensions = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.String(50), nullable=False)
    origin = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    fragility = db.Column(db.String(50), default='Standard')
    special_requirements = db.Column(Text)
    timeline = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to quotes
    quotes = db.relationship('Quote', backref='shipment', lazy=True, cascade='all, delete-orphan')
    
    # Add database indexes for performance
    __table_args__ = (
        Index('idx_shipment_origin_dest', 'origin', 'destination'),
        Index('idx_shipment_created_at', 'created_at'),
        Index('idx_shipment_user_id', 'user_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_description': self.item_description,
            'dimensions': self.dimensions,
            'weight': self.weight,
            'origin': self.origin,
            'destination': self.destination,
            'fragility': self.fragility,
            'special_requirements': self.special_requirements,
            'timeline': self.timeline,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# User Management Models for Enterprise Features
class User(UserMixin, db.Model):
    """User model for customer accounts and authentication"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    company_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(64), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    shipments = db.relationship('Shipment', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        """Generate unique API key for programmatic access"""
        import secrets
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Quote(db.Model):
    """Model to store AI-generated quotes"""
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    quote_content = db.Column(Text, nullable=False)  # Full AI-generated quote
    agent_results = db.Column(JSON)  # Store individual agent results
    status = db.Column(db.String(50), default='generated')  # generated, accepted, declined
    total_cost = db.Column(db.Float)  # Extracted total cost if available
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'quote_content': self.quote_content,
            'agent_results': self.agent_results,
            'status': self.status,
            'total_cost': self.total_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_agent_results(self, results_dict):
        """Helper method to store agent results as JSON"""
        self.agent_results = results_dict
    
    def get_agent_results(self):
        """Helper method to retrieve agent results"""
        return self.agent_results or {}

class QuoteHistory(db.Model):
    """Model to track quote history and analytics"""
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, viewed, downloaded, accepted, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_info = db.Column(JSON)  # Store user agent, IP, etc. for analytics
    
    def to_dict(self):
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'action': self.action,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_info': self.user_info
        }