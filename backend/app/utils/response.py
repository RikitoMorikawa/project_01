"""
Response utilities for consistent API responses
"""
from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse
from datetime import datetime


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a standardized success response
    """
    response_data = {
        "status": "success",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response_data["message"] = message
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers or {}
    )


def error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a standardized error response
    """
    response_data = {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response_data["details"] = details
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers or {}
    )


def paginated_response(
    data: list,
    total: int,
    page: int = 1,
    page_size: int = 10,
    message: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized paginated response
    """
    total_pages = (total + page_size - 1) // page_size
    
    response_data = {
        "status": "success",
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response_data["message"] = message
    
    return JSONResponse(content=response_data, status_code=200)