"""
Custom middleware for the CSR Lambda API
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Add request ID to all requests for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


async def timing_middleware(request: Request, call_next: Callable) -> Response:
    """Add timing information to responses"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


async def error_handling_middleware(request: Request, call_next: Callable) -> Response:
    """Enhanced error handling middleware"""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            f"Request {request_id} failed: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(exc)
            },
            exc_info=True
        )
        
        # Return structured error response
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "request_id": request_id
            }
        )


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response