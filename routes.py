import os
import logging
from flask import render_template, request, flash, redirect, url_for, jsonify
from app import app, db
from crew_manager import TransPakCrewManager
from models import Shipment, Quote, QuoteHistory

# Initialize the crew manager
crew_manager = TransPakCrewManager()
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """
    Main page for shipment information input
    """
    return render_template('index.html')

@app.route('/generate_quote', methods=['POST'])
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
        
        logger.info(f"Received quote request: {shipment_info}")
        
        # Validate input
        validation = crew_manager.validate_shipment_info(shipment_info)
        if not validation['valid']:
            flash(f"Please provide the following required information: {', '.join(validation['missing_fields'])}", 'error')
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
        
        # Generate quote using AI agents
        result = crew_manager.generate_quote(shipment_info)
        
        if result['success']:
            # Save quote to database
            quote = Quote(
                shipment_id=shipment.id,
                quote_content=str(result['quote']),
                status='generated'
            )
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
                                 quote=result['quote'], 
                                 shipment_info=shipment_info,
                                 quote_id=quote.id)
        else:
            flash(f"Error generating quote: {result['message']}", 'error')
            return render_template('index.html', form_data=shipment_info)
            
    except Exception as e:
        logger.error(f"Error in generate_quote route: {str(e)}")
        flash("An unexpected error occurred. Please try again.", 'error')
        return render_template('index.html')

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

@app.route('/admin')
def admin_dashboard():
    """
    Simple admin dashboard showing system statistics
    """
    stats = {
        'total_shipments': Shipment.query.count(),
        'total_quotes': Quote.query.count(),
        'recent_quotes': Quote.query.order_by(Quote.created_at.desc()).limit(5).all(),
        'quote_actions': db.session.query(QuoteHistory.action, db.func.count(QuoteHistory.id))
                           .group_by(QuoteHistory.action).all()
    }
    return render_template('admin_dashboard.html', stats=stats)

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    flash("An internal error occurred. Please try again.", 'error')
    return render_template('index.html'), 500
