"""
Common dependencies for FastAPI endpoints
"""
from fastapi import Depends, HTTPException, Request
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    """Get request ID from request state"""
    return getattr(request.state, 'request_id', 'unknown')


def get_current_environment() -> str:
    """Get current environment"""
    return settings.environment


def validate_content_type(request: Request, expected: str = "application/json"):
    """Validate request content type"""
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith(expected):
        raise HTTPException(
            status_code=415,
            detail={
                "error_code": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"Expected content type: {expected}",
                "received": content_type
            }
        )


async def log_request_info(request: Request, request_id: str = Depends(get_request_id)):
    """Log request information for debugging"""
    logger.info(
        f"Request {request_id}: {request.method} {request.url}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else None
        }
    )
    return request_id


# Common response headers
def get_common_headers() -> dict:
    """Get common response headers"""
    return {
        "X-API-Version": settings.api_version,
        "X-Environment": settings.environment
    }