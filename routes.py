import os
import logging
from flask import render_template, request, flash, redirect, url_for, jsonify
from app import app
from crew_manager import TransPakCrewManager

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
        
        # Generate quote using AI agents
        result = crew_manager.generate_quote(shipment_info)
        
        if result['success']:
            return render_template('quote_result.html', 
                                 quote=result['quote'], 
                                 shipment_info=shipment_info)
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

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    flash("An internal error occurred. Please try again.", 'error')
    return render_template('index.html'), 500
