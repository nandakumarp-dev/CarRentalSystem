import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to log slow requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > 2.0:  # Log requests slower than 2 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s by user {request.user}"
                )
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers"""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response