from app import db
from datetime import datetime
from sqlalchemy import Text, JSON
import json

class Shipment(db.Model):
    """Model to store shipment information"""
    id = db.Column(db.Integer, primary_key=True)
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

class Quote(db.Model):
    """Model to store AI-generated quotes"""
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=False)
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