from flask import Blueprint, render_template, jsonify
from models import Shipment, Quote, QuoteHistory
from app import db
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/api/metrics')
def get_system_metrics():
    """API endpoint for real-time system metrics"""
    try:
        # Calculate metrics for the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Quote generation trends
        daily_quotes = db.session.query(
            db.func.date(Quote.created_at).label('date'),
            db.func.count(Quote.id).label('count')
        ).filter(Quote.created_at >= thirty_days_ago).group_by(
            db.func.date(Quote.created_at)
        ).all()
        
        # Popular shipping routes
        popular_routes = db.session.query(
            Shipment.origin,
            Shipment.destination,
            db.func.count(Shipment.id).label('count')
        ).join(Quote).group_by(
            Shipment.origin, Shipment.destination
        ).order_by(db.func.count(Shipment.id).desc()).limit(10).all()
        
        # Average processing metrics
        processing_stats = db.session.query(
            db.func.avg(
                db.func.extract('epoch', Quote.created_at - Shipment.created_at)
            ).label('avg_processing_time'),
            db.func.count(Quote.id).label('total_quotes')
        ).join(Shipment).first()
        
        # Agent activity breakdown
        agent_activity = db.session.query(
            QuoteHistory.action,
            db.func.count(QuoteHistory.id).label('count')
        ).group_by(QuoteHistory.action).all()
        
        return jsonify({
            'success': True,
            'data': {
                'daily_quotes': [{'date': str(item.date), 'count': item.count} for item in daily_quotes],
                'popular_routes': [
                    {'origin': item.origin, 'destination': item.destination, 'count': item.count}
                    for item in popular_routes
                ],
                'processing_stats': {
                    'avg_time_seconds': float(processing_stats.avg_processing_time or 0),
                    'total_quotes': processing_stats.total_quotes
                },
                'agent_activity': [
                    {'action': item.action, 'count': item.count}
                    for item in agent_activity
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/performance')
def performance_dashboard():
    """Performance monitoring dashboard"""
    return render_template('analytics/performance.html')

@analytics_bp.route('/api/cost-analysis')
def cost_analysis():
    """Analyze quote costs and pricing trends"""
    try:
        # This would analyze actual quote costs if we tracked them
        # For now, provide structure for future implementation
        
        cost_data = {
            'avg_quote_value': 2500.00,  # Placeholder - would come from parsed quotes
            'cost_breakdown': {
                'materials': 35,
                'labor': 25,
                'shipping': 30,
                'margin': 10
            },
            'monthly_trends': [
                {'month': '2024-11', 'avg_cost': 2200},
                {'month': '2024-12', 'avg_cost': 2350},
                {'month': '2025-01', 'avg_cost': 2500}
            ]
        }
        
        return jsonify({'success': True, 'data': cost_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500