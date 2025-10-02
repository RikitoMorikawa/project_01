from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import logging
from typing import Dict, Any
from datetime import datetime

from app.schemas.user import LoginRequest, LoginResponse, TokenRefreshRequest, TokenRefreshResponse
from app.auth.cognito import cognito_verifier
from app.auth.dependencies import get_current_user, security
from app.exceptions import AuthenticationError, ExternalServiceError
from app.utils.response import success_response, error_response
from app.dependencies import get_request_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=Dict[str, Any])
async def login(
    login_data: LoginRequest,
    request_id: str = Depends(get_request_id)
):
    """
    Server-side login endpoint using AWS Cognito
    
    This endpoint provides server-side authentication using Cognito's InitiateAuth API.
    For production use, consider using:
    1. AWS Amplify Auth on the frontend for better UX
    2. Cognito Hosted UI for OAuth flows
    3. This endpoint for server-to-server authentication
    """
    logger.info(f"Login attempt for email: {login_data.email} - Request ID: {request_id}")
    
    try:
        # Use Cognito's InitiateAuth API for server-side authentication
        response = cognito_verifier.cognito_client.initiate_auth(
            ClientId=cognito_verifier.client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': login_data.email,
                'PASSWORD': login_data.password
            }
        )
        
        # Check if authentication was successful
        if 'AuthenticationResult' in response:
            auth_result = response['AuthenticationResult']
            
            # Verify the access token to get user info
            access_token = auth_result.get('AccessToken')
            user_claims = cognito_verifier.verify_token(access_token)
            
            return success_response(
                data={
                    "access_token": access_token,
                    "id_token": auth_result.get('IdToken'),
                    "refresh_token": auth_result.get('RefreshToken'),
                    "token_type": auth_result.get('TokenType', 'Bearer'),
                    "expires_in": auth_result.get('ExpiresIn'),
                    "user": {
                        "cognito_user_id": user_claims.get('sub'),
                        "username": user_claims.get('username'),
                        "email": user_claims.get('email'),
                        "scopes": user_claims.get('scope', '').split()
                    }
                },
                message="Login successful"
            )
        
        # Handle challenge responses (MFA, password reset, etc.)
        elif 'ChallengeName' in response:
            challenge_name = response['ChallengeName']
            session = response.get('Session')
            
            return success_response(
                data={
                    "challenge": challenge_name,
                    "session": session,
                    "challenge_parameters": response.get('ChallengeParameters', {}),
                    "message": f"Authentication challenge required: {challenge_name}"
                },
                message="Authentication challenge required",
                status_code=202
            )
        
        else:
            return error_response(
                error_code="UNEXPECTED_RESPONSE",
                message="Unexpected response from authentication service",
                status_code=500
            )
        
    except cognito_verifier.cognito_client.exceptions.NotAuthorizedException:
        logger.warning(f"Login failed - invalid credentials for: {login_data.email} - Request ID: {request_id}")
        return error_response(
            error_code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401
        )
    except cognito_verifier.cognito_client.exceptions.UserNotConfirmedException:
        logger.warning(f"Login failed - user not confirmed: {login_data.email} - Request ID: {request_id}")
        return error_response(
            error_code="USER_NOT_CONFIRMED",
            message="User account is not confirmed. Please check your email for confirmation instructions.",
            status_code=401
        )
    except cognito_verifier.cognito_client.exceptions.UserNotFoundException:
        logger.warning(f"Login failed - user not found: {login_data.email} - Request ID: {request_id}")
        return error_response(
            error_code="USER_NOT_FOUND",
            message="User not found",
            status_code=401
        )
    except cognito_verifier.cognito_client.exceptions.TooManyRequestsException:
        logger.warning(f"Login failed - too many requests for: {login_data.email} - Request ID: {request_id}")
        return error_response(
            error_code="TOO_MANY_REQUESTS",
            message="Too many login attempts. Please try again later.",
            status_code=429
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="LOGIN_ERROR",
            message="Login failed due to server error",
            status_code=500
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    request_id: str = Depends(get_request_id)
):
    """
    Refresh access token using refresh token
    """
    logger.info(f"Token refresh requested - Request ID: {request_id}")
    
    try:
        # Use Cognito to refresh the token
        token_data = cognito_verifier.refresh_token(refresh_data.refresh_token)
        
        return success_response(
            data=token_data,
            message="Token refreshed successfully"
        )
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed - authentication error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="INVALID_REFRESH_TOKEN",
            message=str(e),
            status_code=401
        )
    except ExternalServiceError as e:
        logger.error(f"Token refresh failed - external service error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="SERVICE_ERROR",
            message="Token refresh service temporarily unavailable",
            status_code=502
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="REFRESH_ERROR",
            message="Token refresh failed",
            status_code=500
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """
    Logout endpoint - Invalidate current session using Cognito GlobalSignOut
    
    This endpoint will:
    1. Call Cognito's GlobalSignOut API to invalidate all tokens
    2. Log the logout event
    3. Return success response
    """
    logger.info(f"Logout requested for user: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        # Use the access token to perform global sign out
        access_token = credentials.credentials
        
        # Call Cognito GlobalSignOut to invalidate all user sessions
        cognito_verifier.cognito_client.global_sign_out(
            AccessToken=access_token
        )
        
        logger.info(f"User {current_user.get('username')} logged out successfully - Request ID: {request_id}")
        
        return success_response(
            data={
                "message": "Logout successful",
                "user": current_user.get('username'),
                "logout_time": datetime.now().isoformat(),
                "instructions": [
                    "All sessions have been invalidated",
                    "Clear tokens from client storage",
                    "Redirect to login page"
                ]
            },
            message="User logged out successfully"
        )
        
    except cognito_verifier.cognito_client.exceptions.NotAuthorizedException:
        # Token might already be invalid, but we'll still consider logout successful
        logger.warning(f"Logout with invalid token for user: {current_user.get('username')} - Request ID: {request_id}")
        return success_response(
            data={
                "message": "Logout successful (token was already invalid)",
                "user": current_user.get('username')
            },
            message="User logged out successfully"
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="LOGOUT_ERROR",
            message="Logout failed due to server error",
            status_code=500
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """
    Get current user information from JWT token
    """
    logger.info(f"User info requested for: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        return success_response(
            data={
                "user": current_user,
                "token_info": {
                    "cognito_user_id": current_user.get('cognito_user_id'),
                    "username": current_user.get('username'),
                    "email": current_user.get('email'),
                    "scopes": current_user.get('scope', []),
                    "client_id": current_user.get('client_id'),
                    "expires_at": current_user.get('exp')
                }
            },
            message="User information retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get user info error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="USER_INFO_ERROR",
            message="Failed to retrieve user information",
            status_code=500
        )


@router.post("/verify", response_model=Dict[str, Any])
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request_id: str = Depends(get_request_id)
):
    """
    Verify JWT token validity
    """
    logger.info(f"Token verification requested - Request ID: {request_id}")
    
    try:
        if not credentials:
            return error_response(
                error_code="MISSING_TOKEN",
                message="Authorization token is required",
                status_code=401
            )
        
        # Verify the token
        token_claims = cognito_verifier.verify_token(credentials.credentials)
        
        return success_response(
            data={
                "valid": True,
                "claims": {
                    "cognito_user_id": token_claims.get('sub'),
                    "username": token_claims.get('username'),
                    "email": token_claims.get('email'),
                    "scopes": token_claims.get('scope', '').split(),
                    "expires_at": token_claims.get('exp'),
                    "issued_at": token_claims.get('iat')
                }
            },
            message="Token is valid"
        )
        
    except AuthenticationError as e:
        logger.warning(f"Token verification failed: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="INVALID_TOKEN",
            message=str(e),
            status_code=401
        )
    except Exception as e:
        logger.error(f"Token verification error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="VERIFICATION_ERROR",
            message="Token verification failed",
            status_code=500
        )