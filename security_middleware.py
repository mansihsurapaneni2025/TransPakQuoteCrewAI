from functools import wraps
from flask import request, jsonify, session
import time
import hashlib
from collections import defaultdict

class SecurityMiddleware:
    """Security enhancements for the TransPak system"""
    
    def __init__(self):
        self.rate_limits = defaultdict(list)
        self.blocked_ips = set()
        
    def rate_limit(self, max_requests=10, window_minutes=1):
        """Rate limiting decorator for API endpoints"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                now = time.time()
                window = window_minutes * 60
                
                # Clean old requests
                self.rate_limits[client_ip] = [
                    req_time for req_time in self.rate_limits[client_ip] 
                    if now - req_time < window
                ]
                
                # Check rate limit
                if len(self.rate_limits[client_ip]) >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window_minutes * 60
                    }), 429
                
                self.rate_limits[client_ip].append(now)
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_shipment_input(self, data):
        """Validate and sanitize shipment input data"""
        required_fields = ['item_description', 'dimensions', 'weight', 'origin', 'destination']
        
        # Check for required fields
        for field in required_fields:
            if not data.get(field) or not data[field].strip():
                return False, f"Missing required field: {field}"
        
        # Validate dimensions format
        dimensions = data.get('dimensions', '').strip()
        if not any(char in dimensions.lower() for char in ['x', '×', 'by']):
            return False, "Dimensions must include length x width x height"
        
        # Validate weight format
        weight = data.get('weight', '').strip()
        if not any(unit in weight.lower() for unit in ['lb', 'kg', 'ton', 'pound', 'kilogram']):
            return False, "Weight must include units (lbs, kg, etc.)"
        
        # Sanitize text fields
        text_fields = ['item_description', 'special_requirements']
        for field in text_fields:
            if data.get(field):
                # Remove potentially dangerous characters
                data[field] = ''.join(char for char in data[field] if char.isprintable())
                # Limit length
                data[field] = data[field][:1000]
        
        return True, "Valid"
    
    def log_security_event(self, event_type, client_ip, details):
        """Log security events for monitoring"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[SECURITY] {timestamp} - {event_type} from {client_ip}: {details}")