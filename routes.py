import os
import logging
from datetime import datetime
import time
from flask import render_template, request, flash, redirect, url_for, jsonify, make_response
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity, jwt_required
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app import app, db, limiter
from crew_manager import TransPakCrewManager
from direct_quote_generator import DirectQuoteGenerator
from models import Shipment, Quote, QuoteHistory, User
from security_middleware import SecurityMiddleware
from cache_manager import CacheManager
from analytics_dashboard import analytics_bp
from monitoring_config import system_monitor, get_deployment_readiness
from real_time_agent_monitor import agent_monitor
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

security = SecurityMiddleware()
cache_manager = CacheManager()
crew_manager = TransPakCrewManager()

# Register analytics blueprint
app.register_blueprint(analytics_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Initialize the crew manager
crew_manager = TransPakCrewManager()
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """
    Main page for shipment information input
    """
    return render_template('index.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint"""
    if request.method == 'POST':
        email = request.form.get('email')
        company_name = request.form.get('company_name')
        contact_name = request.form.get('contact_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            email=email,
            company_name=company_name,
            contact_name=contact_name,
            phone=phone
        )
        user.set_password(password)
        user.generate_api_key()
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout endpoint"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with quote history"""
    user_shipments = Shipment.query.filter_by(user_id=current_user.id).order_by(Shipment.created_at.desc()).limit(10).all()
    return render_template('dashboard.html', shipments=user_shipments)

# API Authentication
@app.route('/api/token', methods=['POST'])
@limiter.limit("5 per minute")
def get_api_token():
    """Generate JWT token for API access"""
    email = request.json.get('email')
    password = request.json.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token, 'api_key': user.api_key})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/generate_quote', methods=['POST'])
@limiter.limit("10 per minute")
@security.rate_limit(max_requests=5, window_minutes=1)
def generate_quote():
    """
    Process shipment information and generate quote using AI agents
    """
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
        
        # Initialize direct quote generator
        quote_generator = DirectQuoteGenerator()
        
        logger.info(f"Received quote request: {shipment_info}")
        
        # Validate input
        validation, missing_fields = quote_generator.validate_shipment_info(shipment_info)
        if not validation:
            flash(f"Please provide the following required information: {', '.join(missing_fields)}", 'error')
            return render_template('index.html', form_data=shipment_info)
        
        # Save shipment to database
        shipment = Shipment(
            item_description=shipment_info['item_description'],
            dimensions=shipment_info['dimensions'],
            weight=shipment_info['weight'],
            origin=shipment_info['origin'],
            destination=shipment_info['destination'],
            fragility=shipment_info['fragility'],
            special_requirements=shipment_info['special_requirements'],
            timeline=shipment_info['timeline']
        )
        db.session.add(shipment)
        db.session.commit()
        
        # Generate quote using AI agents with full traceability
        try:
            result = quote_generator.generate_quote(shipment_info)
            
            if result['success']:
                quote_content = result['quote_content']
                agent_activity = result.get('agent_activity', {})
                cost_breakdown = result.get('cost_breakdown', {})
                
                # Save quote to database
                quote = Quote(
                    shipment_id=shipment.id,
                    quote_content=str(quote_content),
                    status='generated'
                )
                quote.set_agent_results({
                    'agent_activity': agent_activity,
                    'cost_breakdown': cost_breakdown
                })
                db.session.add(quote)
                db.session.commit()
                
                # Track quote creation
                history = QuoteHistory(
                    quote_id=quote.id,
                    action='created',
                    user_info={'user_agent': request.headers.get('User-Agent', '')}
                )
                db.session.add(history)
                db.session.commit()
                
                return render_template('quote_result.html', 
                                     quote=quote_content, 
                                     shipment_info=shipment_info,
                                     agent_activity=agent_activity,
                                     cost_breakdown=cost_breakdown,
                                     quote_id=quote.id)
            else:
                logger.error(f"Quote generation failed: {result['message']}")
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

@app.route('/new_quote')
def new_quote():
    """
    Start a new quote (redirect to main page)
    """
    return redirect(url_for('index'))

@app.route('/quote/<int:quote_id>')
def view_quote(quote_id):
    """
    View a specific quote by ID
    """
    quote = Quote.query.get_or_404(quote_id)
    shipment = quote.shipment
    
    # Track quote view
    history = QuoteHistory(
        quote_id=quote.id,
        action='viewed',
        user_info={'user_agent': request.headers.get('User-Agent', '')}
    )
    db.session.add(history)
    db.session.commit()
    
    return render_template('quote_result.html', 
                         quote=quote.quote_content, 
                         shipment_info=shipment.to_dict(),
                         quote_id=quote.id)

@app.route('/quotes')
def list_quotes():
    """
    List all quotes with pagination
    """
    page = request.args.get('page', 1, type=int)
    quotes = Quote.query.order_by(Quote.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('quotes_list.html', quotes=quotes)

@app.route('/download_quote/<int:quote_id>')
def download_quote(quote_id):
    """
    Download quote as text file
    """
    quote = Quote.query.get_or_404(quote_id)
    
    # Track download
    history = QuoteHistory(
        quote_id=quote.id,
        action='downloaded',
        user_info={'user_agent': request.headers.get('User-Agent', '')}
    )
    db.session.add(history)
    db.session.commit()
    
    from flask import Response
    return Response(
        quote.quote_content,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename=transpak-quote-{quote.id}.txt'}
    )

# API Endpoints for External Integration
@app.route('/api/v1/quotes', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def api_generate_quote():
    """API endpoint for generating quotes programmatically"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid or inactive user'}), 401
        
        data = request.get_json()
        
        # Validate API input
        is_valid, error_message = security.validate_shipment_input(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Check cache
        shipment_hash = cache_manager.generate_shipment_hash(data)
        cached_quote = cache_manager.get_cached_quote(shipment_hash)
        
        if cached_quote:
            return jsonify({
                'success': True,
                'quote': cached_quote,
                'cached': True,
                'processing_time': 0.1
            })
        
        # Generate new quote
        start_time = time.time()
        quote_result = crew_manager.generate_quote(data)
        processing_time = time.time() - start_time
        
        # Cache result
        cache_manager.cache_quote(shipment_hash, quote_result)
        cache_manager.update_agent_metrics("api_quote_generation", processing_time, True)
        
        # Create database records
        shipment = Shipment(
            user_id=user.id,
            item_description=data['item_description'],
            dimensions=data['dimensions'],
            weight=data['weight'],
            origin=data['origin'],
            destination=data['destination'],
            fragility=data.get('fragility', 'Standard'),
            special_requirements=data.get('special_requirements', ''),
            timeline=data.get('timeline', '')
        )
        db.session.add(shipment)
        db.session.flush()
        
        quote = Quote(
            shipment_id=shipment.id,
            quote_content=quote_result,
            status='generated'
        )
        db.session.add(quote)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'quote_id': quote.id,
            'shipment_id': shipment.id,
            'quote': quote_result,
            'cached': False,
            'processing_time': processing_time
        })
        
    except Exception as e:
        cache_manager.update_agent_metrics("api_quote_generation", 0, False)
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/quotes/<int:quote_id>', methods=['GET'])
@jwt_required()
def api_get_quote(quote_id):
    """API endpoint to retrieve a specific quote"""
    user_id = get_jwt_identity()
    
    quote = Quote.query.join(Shipment).filter(
        Quote.id == quote_id,
        Shipment.user_id == user_id
    ).first()
    
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404
    
    return jsonify({
        'success': True,
        'quote': quote.to_dict(),
        'shipment': quote.shipment.to_dict()
    })

@app.route('/api/v1/quotes', methods=['GET'])
@jwt_required()
def api_list_quotes():
    """API endpoint to list user's quotes"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    quotes = Quote.query.join(Shipment).filter(
        Shipment.user_id == user_id
    ).order_by(Quote.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'quotes': [quote.to_dict() for quote in quotes.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': quotes.total,
            'pages': quotes.pages
        }
    })

# Notification and Webhook System
@app.route('/api/v1/notifications/webhook', methods=['POST'])
@limiter.limit("100 per hour")
def webhook_handler():
    """Webhook endpoint for external systems"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        
        if event_type == 'quote_accepted':
            quote_id = data.get('quote_id')
            quote = Quote.query.get(quote_id)
            if quote:
                quote.status = 'accepted'
                db.session.commit()
                
                # Log the event
                history = QuoteHistory(
                    quote_id=quote_id,
                    action='accepted_via_webhook',
                    user_info={'webhook_source': data.get('source', 'unknown')}
                )
                db.session.add(history)
                db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    """
    Admin dashboard showing system statistics and health
    """
    try:
        stats = {
            'total_shipments': Shipment.query.count(),
            'total_quotes': Quote.query.count(),
            'recent_quotes': Quote.query.order_by(Quote.created_at.desc()).limit(5).all(),
            'quote_actions': db.session.query(QuoteHistory.action, db.func.count(QuoteHistory.id))
                               .group_by(QuoteHistory.action).all(),
            'system_status': 'healthy',
            'database_status': 'connected',
            'ai_agents_status': 'active'
        }
    except Exception as e:
        stats = {
            'total_shipments': 0,
            'total_quotes': 0,
            'recent_quotes': [],
            'quote_actions': [],
            'system_status': 'error',
            'database_status': 'disconnected',
            'ai_agents_status': 'unknown',
            'error_message': str(e)
        }
    
    return render_template('admin_dashboard.html', stats=stats)

@app.route('/ai-agents-process')
def ai_agents_process():
    """AI Agents Process explanation page"""
    return render_template('ai_agents_process.html')

@app.route('/health')
def health_check():
    """
    System health check endpoint for monitoring
    """
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        
        # Test AI agent availability (check OpenAI API key)
        import os
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': 'connected',
                'ai_agents': 'available' if openai_key else 'no_api_key',
                'web_server': 'running'
            },
            'version': '1.0.0'
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        health_status = {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'services': {
                'database': 'error',
                'ai_agents': 'unknown',
                'web_server': 'running'
            }
        }
        
        return jsonify(health_status), 500

@app.route('/api/test/quote', methods=['POST'])
def test_quote_generation():
    """
    Test endpoint for automated quote generation testing
    """
    try:
        test_data = {
            'item_description': 'Test Equipment for System Validation',
            'dimensions': '24 x 18 x 12 inches',
            'weight': '50 lbs',
            'origin': 'Austin, TX',
            'destination': 'Dallas, TX',
            'fragility': 'Standard',
            'special_requirements': 'Test shipment for system validation',
            'timeline': 'Test mode'
        }
        
        # Validate the test data
        validation = crew_manager.validate_shipment_info(test_data)
        
        if validation['valid']:
            return jsonify({
                'status': 'validation_passed',
                'message': 'Test data is valid for quote generation',
                'test_data': test_data
            }), 200
        else:
            return jsonify({
                'status': 'validation_failed',
                'missing_fields': validation['missing_fields']
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test_quote_display')
def test_quote_display():
    """Test quote display functionality without AI complexity"""
    test_shipment = {
        'item_description': 'Electronic testing device',
        'dimensions': '12 x 8 x 6',
        'weight': '10 lbs',
        'origin': 'San Francisco, CA',
        'destination': 'Los Angeles, CA',
        'fragility': 'Standard',
        'special_requirements': '',
        'timeline': '2-3 days'
    }
    
    test_quote = """TRANSPAK SHIPPING QUOTE

SHIPMENT DETAILS:
Item: Electronic testing device
Dimensions: 12 x 8 x 6 inches
Weight: 10 lbs
Route: San Francisco, CA → Los Angeles, CA

PACKAGING SOLUTION:
- Standard protective packaging
- Anti-static materials for electronics
- Professional handling labels

LOGISTICS PLAN:
- Ground transportation with tracking
- 2-3 business day delivery
- Signature confirmation required

COST BREAKDOWN:
Packaging: $25.00
Shipping: $35.00
Insurance: $5.00
------------------------
TOTAL: $65.00

Quote valid for 30 days."""
    
    return render_template('quote_result.html', 
                         quote=test_quote, 
                         shipment_info=test_shipment,
                         quote_id=1)

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    flash("An internal error occurred. Please try again.", 'error')
    return render_template('index.html'), 500
