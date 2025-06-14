"""
Fixed routes with direct quote generation (bypasses CrewAI timeout issues)
"""

import os
import logging
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, jsonify, make_response
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity, jwt_required
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app import app, db, limiter
from direct_quote_generator import DirectQuoteGenerator
from models import Shipment, Quote, QuoteHistory, User
from security_middleware import SecurityMiddleware
from cache_manager import CacheManager

# Initialize components
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

security = SecurityMiddleware()
cache_manager = CacheManager()

logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def index():
    """Main page for shipment information input"""
    return render_template('index.html')

@app.route('/generate_quote', methods=['POST'])
@limiter.limit("10 per minute")
@security.rate_limit(max_requests=5, window_minutes=1)
def generate_quote():
    """Process shipment information and generate quote using enhanced pricing engine"""
    
    try:
        # Extract form data
        shipment_info = {
            'item_description': request.form.get('item_description', '').strip(),
            'dimensions': request.form.get('dimensions', '').strip(),
            'weight': request.form.get('weight', '').strip(),
            'origin': request.form.get('origin', '').strip(),
            'destination': request.form.get('destination', '').strip(),
            'fragility': request.form.get('fragility', 'Standard'),
            'special_requirements': request.form.get('special_requirements', '').strip(),
            'timeline': request.form.get('timeline', '').strip()
        }
        
        logger.info(f"Received quote request: {shipment_info}")
        
        # Initialize direct quote generator
        quote_generator = DirectQuoteGenerator()
        
        # Validate input
        validation, missing_fields = quote_generator.validate_shipment_info(shipment_info)
        if not validation:
            flash(f"Please provide the following required information: {', '.join(missing_fields)}", 'error')
            return render_template('index.html', form_data=shipment_info)
        
        # Save shipment to database
        shipment = Shipment()
        shipment.item_description = shipment_info['item_description']
        shipment.dimensions = shipment_info['dimensions']
        shipment.weight = shipment_info['weight']
        shipment.origin = shipment_info['origin']
        shipment.destination = shipment_info['destination']
        shipment.fragility = shipment_info['fragility']
        shipment.special_requirements = shipment_info['special_requirements']
        shipment.timeline = shipment_info['timeline']
        
        db.session.add(shipment)
        db.session.commit()
        
        # Generate quote using enhanced pricing engine
        try:
            result = quote_generator.generate_quote(shipment_info)
            
            if result['success']:
                quote_content = result['quote_content']
                agent_activity = result.get('agent_activity', {})
                cost_breakdown = result.get('cost_breakdown', {})
                
                # Save quote to database
                quote = Quote()
                quote.shipment_id = shipment.id
                quote.quote_content = str(quote_content)
                quote.status = 'generated'
                quote.set_agent_results({
                    'agent_activity': agent_activity,
                    'cost_breakdown': cost_breakdown
                })
                
                db.session.add(quote)
                db.session.commit()
                
                # Track quote creation
                history = QuoteHistory()
                history.quote_id = quote.id
                history.action = 'created'
                history.user_info = {'user_agent': request.headers.get('User-Agent', '')}
                
                db.session.add(history)
                db.session.commit()
                
                logger.info(f"Quote generated successfully for shipment {shipment.id}")
                
                return render_template('quote_result.html', 
                                     quote=quote_content, 
                                     shipment_info=shipment_info,
                                     agent_activity=agent_activity,
                                     cost_breakdown=cost_breakdown,
                                     quote_id=quote.id)
            else:
                error_msg = result.get('error', 'Unknown error occurred')
                logger.error(f"Quote generation failed: {error_msg}")
                flash("Quote generation failed. Please try again.", 'error')
                return render_template('index.html', form_data=shipment_info)
        
        except Exception as quote_error:
            logger.error(f"Quote generation failed: {str(quote_error)}")
            flash("Quote generation is currently unavailable. Please try again later.", 'error')
            return render_template('index.html', form_data=shipment_info)
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in generate_quote route: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        flash("An unexpected error occurred. Please try again.", 'error')
        return render_template('index.html', form_data=shipment_info if 'shipment_info' in locals() else {})

@app.route('/quote/<int:quote_id>')
def view_quote(quote_id):
    """View a specific quote by ID"""
    quote = Quote.query.get_or_404(quote_id)
    shipment = quote.shipment
    
    # Get agent results
    agent_results = quote.get_agent_results() or {}
    agent_activity = agent_results.get('agent_activity', {})
    cost_breakdown = agent_results.get('cost_breakdown', {})
    
    # Track quote view
    history = QuoteHistory()
    history.quote_id = quote.id
    history.action = 'viewed'
    history.user_info = {'user_agent': request.headers.get('User-Agent', '')}
    db.session.add(history)
    db.session.commit()
    
    return render_template('quote_result.html',
                         quote=quote.quote_content,
                         shipment_info=shipment.to_dict(),
                         agent_activity=agent_activity,
                         cost_breakdown=cost_breakdown,
                         quote_id=quote.id)

@app.route('/health')
def health_check():
    """System health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500