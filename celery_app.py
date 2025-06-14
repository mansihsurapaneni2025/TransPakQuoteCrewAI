from celery import Celery
import os
from app import app

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379'),
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379')
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def generate_quote_async(shipment_info):
    """Background task for quote generation"""
    from crew_manager import TransPakCrewManager
    from models import Shipment, Quote, db
    from cache_manager import CacheManager
    import time
    
    start_time = time.time()
    cache_manager = CacheManager()
    
    try:
        # Check cache first
        shipment_hash = cache_manager.generate_shipment_hash(shipment_info)
        cached_quote = cache_manager.get_cached_quote(shipment_hash)
        
        if cached_quote:
            print(f"Using cached quote for shipment {shipment_hash}")
            return {"success": True, "quote": cached_quote, "cached": True}
        
        # Generate new quote
        crew_manager = TransPakCrewManager()
        quote_result = crew_manager.generate_quote(shipment_info)
        
        # Cache the result
        cache_manager.cache_quote(shipment_hash, quote_result)
        
        # Update performance metrics
        processing_time = time.time() - start_time
        cache_manager.update_agent_metrics("quote_generation", processing_time, True)
        
        return {"success": True, "quote": quote_result, "cached": False}
        
    except Exception as e:
        processing_time = time.time() - start_time
        cache_manager.update_agent_metrics("quote_generation", processing_time, False)
        return {"success": False, "error": str(e)}

@celery.task
def send_quote_notification(quote_id, recipient_email):
    """Send email notification when quote is ready"""
    from models import Quote
    
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return {"success": False, "error": "Quote not found"}
        
        # Email sending logic would go here
        # For now, just log the action
        print(f"Quote {quote_id} notification sent to {recipient_email}")
        
        return {"success": True, "message": "Notification sent"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@celery.task
def analyze_quote_performance():
    """Background task to analyze quote performance and accuracy"""
    from models import Quote, QuoteHistory, db
    from datetime import datetime, timedelta
    
    try:
        # Analyze quotes from the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_quotes = Quote.query.filter(Quote.created_at >= week_ago).all()
        
        # Calculate performance metrics
        total_quotes = len(recent_quotes)
        accepted_quotes = len([q for q in recent_quotes if q.status == 'accepted'])
        accuracy_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0
        
        # Store analysis results
        analysis_result = {
            'period': '7_days',
            'total_quotes': total_quotes,
            'accepted_quotes': accepted_quotes,
            'accuracy_rate': accuracy_rate,
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        print(f"Quote performance analysis: {analysis_result}")
        return analysis_result
        
    except Exception as e:
        return {"success": False, "error": str(e)}