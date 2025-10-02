"""
Custom exceptions for the CSR Lambda API
"""
from fastapi import HTTPException
from typing import Optional, Dict, Any


class APIException(HTTPException):
    """Base API exception class"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "details": details
            }
        )


class ValidationError(APIException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details
        )


class AuthenticationError(APIException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            message=message
        )


class AuthorizationError(APIException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            message=message
        )


class NotFoundError(APIException):
    """Resource not found exception"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' not found"
        )


class ConflictError(APIException):
    """Resource conflict exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=409,
            error_code="RESOURCE_CONFLICT",
            message=message,
            details=details
        )


class DatabaseError(APIException):
    """Database operation error exception"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            status_code=500,
            error_code="DATABASE_ERROR",
            message=message
        )


class ExternalServiceError(APIException):
    """External service error exception"""
    
    def __init__(self, service: str, message: str = "External service error"):
        super().__init__(
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}"
        )