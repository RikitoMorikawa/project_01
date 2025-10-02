"""
Authentication decorators and utilities
"""
from functools import wraps
from typing import Callable, Any, Optional, List
import logging

from app.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


def require_authentication(func: Callable) -> Callable:
    """
    Decorator to require authentication for a function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator is mainly for documentation purposes
        # Actual authentication is handled by FastAPI dependencies
        return await func(*args, **kwargs)
    
    return wrapper


def require_authorization(required_scopes: Optional[List[str]] = None):
    """
    Decorator factory to require specific authorization scopes
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This decorator is mainly for documentation purposes
            # Actual authorization is handled by FastAPI dependencies
            return await func(*args, **kwargs)
        
        # Add metadata about required scopes
        wrapper._required_scopes = required_scopes or []
        return wrapper
    
    return decorator


def admin_required(func: Callable) -> Callable:
    """
    Decorator to require admin privileges
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator is mainly for documentation purposes
        # Actual admin checking is handled by FastAPI dependencies
        return await func(*args, **kwargs)
    
    wrapper._requires_admin = True
    return wrapper


class AuthenticationContext:
    """
    Context manager for authentication operations
    """
    
    def __init__(self, user_info: dict):
        self.user_info = user_info
        self.cognito_user_id = user_info.get('cognito_user_id')
        self.username = user_info.get('username')
        self.email = user_info.get('email')
        self.scopes = user_info.get('scope', [])
    
    def has_scope(self, scope: str) -> bool:
        """Check if user has specific scope"""
        return scope in self.scopes
    
    def has_any_scope(self, scopes: List[str]) -> bool:
        """Check if user has any of the specified scopes"""
        return any(scope in self.scopes for scope in scopes)
    
    def has_all_scopes(self, scopes: List[str]) -> bool:
        """Check if user has all of the specified scopes"""
        return all(scope in self.scopes for scope in scopes)
    
    def require_scope(self, scope: str) -> None:
        """Require specific scope or raise exception"""
        if not self.has_scope(scope):
            raise AuthorizationError(f"Required scope '{scope}' not found")
    
    def require_any_scope(self, scopes: List[str]) -> None:
        """Require any of the specified scopes or raise exception"""
        if not self.has_any_scope(scopes):
            raise AuthorizationError(f"One of the following scopes required: {', '.join(scopes)}")
    
    def require_all_scopes(self, scopes: List[str]) -> None:
        """Require all of the specified scopes or raise exception"""
        if not self.has_all_scopes(scopes):
            missing_scopes = [scope for scope in scopes if scope not in self.scopes]
            raise AuthorizationError(f"Missing required scopes: {', '.join(missing_scopes)}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'cognito_user_id': self.cognito_user_id,
            'username': self.username,
            'email': self.email,
            'scopes': self.scopes
        }


def create_auth_context(user_info: dict) -> AuthenticationContext:
    """
    Create authentication context from user info
    """
    return AuthenticationContext(user_info)


# Common scope constants
class Scopes:
    """Common OAuth scopes used in the application"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    PROFILE_READ = "profile:read"
    PROFILE_WRITE = "profile:write"


# Permission checking utilities
def check_resource_permission(
    user_info: dict,
    resource_owner_id: str,
    required_scope: str,
    allow_self: bool = True
) -> bool:
    """
    Check if user has permission to access a resource
    
    Args:
        user_info: Current user information from JWT
        resource_owner_id: ID of the resource owner
        required_scope: Required scope for the operation
        allow_self: Whether to allow access if user owns the resource
    
    Returns:
        True if user has permission, False otherwise
    """
    try:
        auth_context = create_auth_context(user_info)
        
        # Check if user has the required scope
        if auth_context.has_scope(required_scope):
            return True
        
        # Check if user owns the resource (if allowed)
        if allow_self and auth_context.cognito_user_id == resource_owner_id:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Permission check failed: {str(e)}")
        return False


def require_resource_permission(
    user_info: dict,
    resource_owner_id: str,
    required_scope: str,
    allow_self: bool = True
) -> None:
    """
    Require permission to access a resource or raise exception
    """
    if not check_resource_permission(user_info, resource_owner_id, required_scope, allow_self):
        if allow_self:
            raise AuthorizationError(
                f"Access denied. Required scope '{required_scope}' or resource ownership."
            )
        else:
            raise AuthorizationError(f"Access denied. Required scope '{required_scope}'.")


# Rate limiting decorator (placeholder for future implementation)
def rate_limit(requests_per_minute: int = 60):
    """
    Decorator for rate limiting (placeholder for future implementation)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement rate limiting logic
            # This could use Redis or in-memory storage
            return await func(*args, **kwargs)
        
        wrapper._rate_limit = requests_per_minute
        return wrapper
    
    return decorator