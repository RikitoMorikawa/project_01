"""
Authentication dependencies for FastAPI endpoints
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.auth.cognito import cognito_verifier, extract_token_from_header, get_user_from_token
from app.exceptions import AuthenticationError, AuthorizationError
from app.repositories.user import UserRepository
from app.database import get_db
import pymysql

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token (optional - returns None if no token)
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_info = get_user_from_token(token)
        return user_info
    except AuthenticationError:
        # Return None for optional authentication
        return None
    except Exception as e:
        logger.error(f"Optional authentication failed: {str(e)}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from JWT token (required)
    """
    if not credentials:
        raise AuthenticationError("Authentication required")
    
    try:
        token = credentials.credentials
        user_info = get_user_from_token(token)
        return user_info
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise AuthenticationError("Authentication failed")


async def get_current_user_from_db(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current user from database using JWT token information
    """
    try:
        user_repo = UserRepository(db)
        
        # Try to find user by Cognito user ID
        cognito_user_id = current_user.get('cognito_user_id')
        if not cognito_user_id:
            raise AuthenticationError("Invalid token: missing user ID")
        
        user = user_repo.get_by_cognito_id(cognito_user_id)
        if not user:
            # User exists in Cognito but not in our database
            # This could happen if user was created in Cognito but not synced to our DB
            raise AuthenticationError("User not found in system")
        
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Failed to get user from database: {str(e)}")
        raise AuthenticationError("Failed to retrieve user information")


async def get_current_user_from_db_optional(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: pymysql.Connection = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from database (optional - returns None if no token)
    """
    if not current_user:
        return None
    
    try:
        user_repo = UserRepository(db)
        
        cognito_user_id = current_user.get('cognito_user_id')
        if not cognito_user_id:
            return None
        
        user = user_repo.get_by_cognito_id(cognito_user_id)
        return user
        
    except Exception as e:
        logger.error(f"Failed to get optional user from database: {str(e)}")
        return None


def require_scope(required_scope: str):
    """
    Dependency factory to require specific OAuth scope
    """
    async def check_scope(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_scopes = current_user.get('scope', [])
        if required_scope not in user_scopes:
            raise AuthorizationError(f"Required scope '{required_scope}' not found")
        return current_user
    
    return check_scope


def require_admin():
    """
    Dependency to require admin privileges
    """
    async def check_admin(current_user: Dict[str, Any] = Depends(get_current_user_from_db)) -> Dict[str, Any]:
        # TODO: Implement admin role checking logic
        # For now, we'll use a simple check based on email or user attributes
        # In a real implementation, you'd have a roles/permissions system
        
        # Example: Check if user has admin scope or is in admin group
        # This would be configured in Cognito groups or custom attributes
        
        # Placeholder implementation - replace with actual admin logic
        admin_emails = ["admin@example.com"]  # Configure this properly
        if current_user['email'] not in admin_emails:
            raise AuthorizationError("Admin privileges required")
        
        return current_user
    
    return check_admin


async def verify_token_manually(request: Request) -> Optional[Dict[str, Any]]:
    """
    Manual token verification from request headers
    Useful for middleware or custom authentication flows
    """
    try:
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        token = extract_token_from_header(authorization)
        user_info = get_user_from_token(token)
        return user_info
        
    except Exception as e:
        logger.debug(f"Manual token verification failed: {str(e)}")
        return None


class AuthenticationMiddleware:
    """
    Custom authentication middleware for request-level authentication
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add authentication info to request scope if available
            request = Request(scope, receive)
            
            try:
                user_info = await verify_token_manually(request)
                if user_info:
                    scope["user"] = user_info
            except Exception as e:
                logger.debug(f"Middleware authentication failed: {str(e)}")
        
        await self.app(scope, receive, send)


# Utility functions for token validation
def validate_token_format(token: str) -> bool:
    """
    Validate JWT token format without full verification
    """
    try:
        parts = token.split('.')
        return len(parts) == 3
    except:
        return False


def is_token_expired(token_info: Dict[str, Any]) -> bool:
    """
    Check if token is expired based on exp claim
    """
    try:
        import time
        exp = token_info.get('exp')
        if not exp:
            return True
        return time.time() > exp
    except:
        return True