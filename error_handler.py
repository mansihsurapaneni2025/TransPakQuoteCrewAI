"""
Comprehensive Error Handling System for TransPak AI Quoter
Provides centralized error management, logging, and user-friendly error responses
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from flask import jsonify, render_template, request, flash
from werkzeug.exceptions import HTTPException
import functools

logger = logging.getLogger(__name__)

class TransPakError(Exception):
    """Base exception class for TransPak-specific errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "TRANSPAK_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)

class AgentCommunicationError(TransPakError):
    """Error in AI agent communication or processing"""
    pass

class A2AProtocolError(TransPakError):
    """Error in Agent2Agent protocol communication"""
    pass

class ValidationError(TransPakError):
    """Error in data validation"""
    pass

class DatabaseError(TransPakError):
    """Error in database operations"""
    pass

class ExternalServiceError(TransPakError):
    """Error communicating with external services"""
    pass

class ErrorHandler:
    """Centralized error handling and logging system"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handling for Flask app"""
        app.errorhandler(400)(self.handle_bad_request)
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        app.errorhandler(405)(self.handle_method_not_allowed)
        app.errorhandler(429)(self.handle_too_many_requests)
        app.errorhandler(500)(self.handle_internal_error)
        app.errorhandler(502)(self.handle_bad_gateway)
        app.errorhandler(503)(self.handle_service_unavailable)
        
        # Custom TransPak errors
        app.errorhandler(TransPakError)(self.handle_transpak_error)
        app.errorhandler(AgentCommunicationError)(self.handle_agent_error)
        app.errorhandler(A2AProtocolError)(self.handle_a2a_error)
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(DatabaseError)(self.handle_database_error)
        app.errorhandler(ExternalServiceError)(self.handle_external_service_error)
        
        # General exception handler
        app.errorhandler(Exception)(self.handle_general_exception)
    
    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors"""
        return self._create_error_response(
            error_code="BAD_REQUEST",
            message="Invalid request data provided",
            status_code=400,
            details={"error": str(error)}
        )
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return self._create_error_response(
            error_code="UNAUTHORIZED",
            message="Authentication required",
            status_code=401,
            details={"redirect": "/auth/login"}
        )
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return self._create_error_response(
            error_code="FORBIDDEN",
            message="Access denied to this resource",
            status_code=403
        )
    
    def handle_not_found(self, error):
        """Handle 404 Not Found errors"""
        if request.path.startswith('/api/'):
            return self._create_error_response(
                error_code="NOT_FOUND",
                message="API endpoint not found",
                status_code=404,
                details={"endpoint": request.path}
            )
        else:
            return render_template('errors/404.html'), 404
    
    def handle_method_not_allowed(self, error):
        """Handle 405 Method Not Allowed errors"""
        return self._create_error_response(
            error_code="METHOD_NOT_ALLOWED",
            message=f"Method {request.method} not allowed for this endpoint",
            status_code=405,
            details={"allowed_methods": error.valid_methods if hasattr(error, 'valid_methods') else []}
        )
    
    def handle_too_many_requests(self, error):
        """Handle 429 Too Many Requests errors"""
        return self._create_error_response(
            error_code="RATE_LIMITED",
            message="Too many requests. Please try again later.",
            status_code=429,
            details={"retry_after": "60 seconds"}
        )
    
    def handle_internal_error(self, error):
        """Handle 500 Internal Server Error"""
        error_id = self._log_error(error, "INTERNAL_SERVER_ERROR")
        
        if request.path.startswith('/api/'):
            return self._create_error_response(
                error_code="INTERNAL_ERROR",
                message="An internal server error occurred",
                status_code=500,
                details={"error_id": error_id}
            )
        else:
            return render_template('errors/500.html', error_id=error_id), 500
    
    def handle_bad_gateway(self, error):
        """Handle 502 Bad Gateway errors"""
        return self._create_error_response(
            error_code="BAD_GATEWAY",
            message="External service unavailable",
            status_code=502
        )
    
    def handle_service_unavailable(self, error):
        """Handle 503 Service Unavailable errors"""
        return self._create_error_response(
            error_code="SERVICE_UNAVAILABLE",
            message="Service temporarily unavailable",
            status_code=503,
            details={"retry_after": "300 seconds"}
        )
    
    def handle_transpak_error(self, error: TransPakError):
        """Handle custom TransPak errors"""
        error_id = self._log_error(error, error.error_code)
        
        return self._create_error_response(
            error_code=error.error_code,
            message=error.message,
            status_code=400,
            details={**error.details, "error_id": error_id}
        )
    
    def handle_agent_error(self, error: AgentCommunicationError):
        """Handle AI agent communication errors"""
        error_id = self._log_error(error, "AGENT_COMMUNICATION_ERROR")
        
        return self._create_error_response(
            error_code="AGENT_ERROR",
            message="AI agent processing failed",
            status_code=503,
            details={
                "agent_error": error.message,
                "error_id": error_id,
                "retry_recommended": True
            }
        )
    
    def handle_a2a_error(self, error: A2AProtocolError):
        """Handle A2A protocol errors"""
        error_id = self._log_error(error, "A2A_PROTOCOL_ERROR")
        
        return self._create_error_response(
            error_code="A2A_ERROR",
            message="Agent communication protocol error",
            status_code=502,
            details={
                "protocol_error": error.message,
                "error_id": error_id
            }
        )
    
    def handle_validation_error(self, error: ValidationError):
        """Handle data validation errors"""
        return self._create_error_response(
            error_code="VALIDATION_ERROR",
            message=error.message,
            status_code=400,
            details=error.details
        )
    
    def handle_database_error(self, error: DatabaseError):
        """Handle database operation errors"""
        error_id = self._log_error(error, "DATABASE_ERROR")
        
        return self._create_error_response(
            error_code="DATABASE_ERROR",
            message="Database operation failed",
            status_code=500,
            details={"error_id": error_id}
        )
    
    def handle_external_service_error(self, error: ExternalServiceError):
        """Handle external service errors"""
        error_id = self._log_error(error, "EXTERNAL_SERVICE_ERROR")
        
        return self._create_error_response(
            error_code="EXTERNAL_SERVICE_ERROR",
            message="External service unavailable",
            status_code=502,
            details={
                "service_error": error.message,
                "error_id": error_id,
                "retry_recommended": True
            }
        )
    
    def handle_general_exception(self, error: Exception):
        """Handle any unhandled exceptions"""
        error_id = self._log_error(error, "UNHANDLED_EXCEPTION")
        
        if request.path.startswith('/api/'):
            return self._create_error_response(
                error_code="UNEXPECTED_ERROR",
                message="An unexpected error occurred",
                status_code=500,
                details={"error_id": error_id}
            )
        else:
            flash("An unexpected error occurred. Please try again.", "error")
            return render_template('errors/500.html', error_id=error_id), 500
    
    def _create_error_response(self, error_code: str, message: str, 
                             status_code: int, details: Dict[str, Any] = None) -> Tuple[Any, int]:
        """Create standardized error response"""
        error_response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
        }
        
        if request.path.startswith('/api/'):
            return jsonify(error_response), status_code
        else:
            # For web requests, flash the error and redirect
            flash(message, "error")
            return render_template('errors/generic.html', error=error_response["error"]), status_code
    
    def _log_error(self, error: Exception, error_type: str) -> str:
        """Log error with unique ID for tracking"""
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(str(error)) % 10000:04d}"
        
        logger.error(
            f"Error ID: {error_id} | Type: {error_type} | "
            f"Path: {request.path} | Method: {request.method} | "
            f"Error: {str(error)} | Traceback: {traceback.format_exc()}"
        )
        
        return error_id

def safe_execute(error_type: type = TransPakError, default_message: str = "Operation failed"):
    """Decorator for safe function execution with error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise error_type(default_message, details={"function": func.__name__, "error": str(e)})
        return wrapper
    return decorator

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present in data"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            error_code="MISSING_REQUIRED_FIELDS",
            details={"missing_fields": missing_fields, "provided_fields": list(data.keys())}
        )

def validate_shipment_data(shipment_data: Dict[str, Any]) -> None:
    """Validate shipment data structure and content"""
    required_fields = ['item_description', 'dimensions', 'weight', 'origin', 'destination']
    validate_required_fields(shipment_data, required_fields)
    
    # Additional validation
    if len(shipment_data.get('item_description', '')) < 10:
        raise ValidationError(
            "Item description must be at least 10 characters long",
            error_code="INVALID_ITEM_DESCRIPTION"
        )
    
    weight_str = shipment_data.get('weight', '')
    if not any(unit in weight_str.lower() for unit in ['lb', 'kg', 'pound', 'kilogram']):
        raise ValidationError(
            "Weight must include units (lbs or kg)",
            error_code="INVALID_WEIGHT_FORMAT"
        )
    
    dimensions_str = shipment_data.get('dimensions', '')
    if 'x' not in dimensions_str.lower() and '×' not in dimensions_str:
        raise ValidationError(
            "Dimensions must be in format 'Length x Width x Height'",
            error_code="INVALID_DIMENSIONS_FORMAT"
        )

# Global error handler instance
error_handler = ErrorHandler()