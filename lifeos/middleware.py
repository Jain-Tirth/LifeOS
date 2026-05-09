import logging
from uuid import uuid4
from django.utils.deprecation import MiddlewareBase
import contextvars

# Context variable to hold the correlation ID
correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

class CorrelationIdMiddleware(MiddlewareBase):
    def process_request(self, request):
        request.correlation_id = str(uuid4())
        correlation_id_var.set(request.correlation_id)
        return None
    
    def process_response(self, request, response):
        # Clear context variable to prevent memory leaks and context bleeding
        correlation_id_var.set(None)
        return response
    
    def process_exception(self, request, exception):
        # Clear context variable on exceptions
        correlation_id_var.set(None)
        return None
