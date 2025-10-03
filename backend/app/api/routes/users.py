from fastapi import APIRouter, Depends, Query
import pymysql
from typing import Dict, Any, List, Optional
import logging

from app.database import get_db
from app.schemas.user import (
    UserResponse, UserCreate, UserUpdate, UserWithProfileResponse,
    UserProfileCreate, UserProfileUpdate, PaginationParams
)
from app.repositories.user import UserRepository, UserProfileRepository
from app.auth.dependencies import get_current_user, get_current_user_from_db, require_admin
from app.auth.decorators import require_resource_permission, Scopes
from app.exceptions import NotFoundError, ConflictError, AuthorizationError
from app.utils.response import success_response, error_response, paginated_response
from app.utils.metrics import track_api_call, BusinessMetrics
from app.dependencies import get_request_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=Dict[str, Any])
@track_api_call("users_list")
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for username or email"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Get list of users with pagination and search
    Requires authentication
    ページネーションと検索機能付きでユーザー一覧を取得
    認証が必要
    """
    logger.info(f"Get users requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        user_repo = UserRepository(db)
        
        if search:
            # Search users by username or email / ユーザー名またはメールで検索
            users = user_repo.search_users(search, limit=page_size)
            total = len(users)  # For search, we'll use the result count / 検索の場合は結果数を使用
        else:
            # Get paginated users / ページネーション付きでユーザーを取得
            skip = (page - 1) * page_size
            users = user_repo.get_multi(skip=skip, limit=page_size, order_by="created_at")
            total = user_repo.count()
        
        # Convert to response format (users are already dictionaries) / レスポンス形式に変換（既に辞書形式）
        user_responses = users
        
        return paginated_response(
            data=user_responses,
            total=total,
            page=page,
            page_size=page_size,
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="GET_USERS_ERROR",
            message="Failed to retrieve users",
            status_code=500
        )


@router.post("/", response_model=Dict[str, Any])
@track_api_call("users_create")
async def create_user(
    user_data: UserCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Create a new user
    Note: In a Cognito-based system, users are typically created through:
    1. Cognito sign-up process
    2. Admin API calls
    3. Automatic sync from Cognito events
    
    This endpoint is for administrative purposes or manual user creation
    
    新しいユーザーを作成
    注意：Cognitoベースのシステムでは、通常以下の方法でユーザーが作成される：
    1. Cognitoサインアッププロセス
    2. 管理者API呼び出し
    3. Cognitoイベントからの自動同期
    
    このエンドポイントは管理目的または手動ユーザー作成用
    """
    logger.info(f"Create user requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        user_repo = UserRepository(db)
        
        # Create user data / ユーザーデータを作成
        create_data = {
            "cognito_user_id": f"temp_{user_data.username}",  # Temporary - should come from Cognito / 一時的 - Cognitoから取得すべき
            "email": user_data.email,
            "username": user_data.username
        }
        
        new_user = user_repo.create_user(create_data)
        
        # Track user registration
        BusinessMetrics.track_user_registration()
        
        logger.info(f"User created successfully: {new_user['id']} - Request ID: {request_id}")
        
        return success_response(
            data=new_user,
            message="User created successfully",
            status_code=201
        )
        
    except ConflictError as e:
        logger.warning(f"User creation conflict: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="USER_CONFLICT",
            message=str(e),
            status_code=409,
            details=e.detail.get("details") if hasattr(e, 'detail') else None
        )
    except Exception as e:
        logger.error(f"Create user error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="CREATE_USER_ERROR",
            message="Failed to create user",
            status_code=500
        )


@router.get("/{user_id}", response_model=Dict[str, Any])
@track_api_call("users_get")
async def get_user(
    user_id: int,
    include_profile: bool = Query(False, description="Include user profile information"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Get user by ID
    Users can access their own information, admins can access any user
    """
    logger.info(f"Get user {user_id} requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        user_repo = UserRepository(db)
        
        if include_profile:
            user = user_repo.get_with_profile(user_id)
        else:
            user = user_repo.get(user_id)
        
        if not user:
            return error_response(
                error_code="USER_NOT_FOUND",
                message=f"User with ID {user_id} not found",
                status_code=404
            )
        
        # Check permissions - users can access their own data or admins can access any user
        if user['cognito_user_id'] != current_user.get('cognito_user_id'):
            # Check if current user has admin privileges
            user_scopes = current_user.get('scope', [])
            if 'admin' not in user_scopes and 'user:read' not in user_scopes:
                return error_response(
                    error_code="INSUFFICIENT_PERMISSIONS",
                    message="You can only access your own user information",
                    status_code=403
                )
        
        return success_response(
            data=user,
            message="User retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="GET_USER_ERROR",
            message="Failed to retrieve user",
            status_code=500
        )


@router.put("/{user_id}", response_model=Dict[str, Any])
@track_api_call("users_update")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Update user information
    Users can update their own information, admins can update any user
    """
    logger.info(f"Update user {user_id} requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        user_repo = UserRepository(db)
        
        # Get the user to check permissions
        existing_user = user_repo.get(user_id)
        if not existing_user:
            return error_response(
                error_code="USER_NOT_FOUND",
                message=f"User with ID {user_id} not found",
                status_code=404
            )
        
        # Check permissions - users can update their own data or admins can update any user
        if existing_user['cognito_user_id'] != current_user.get('cognito_user_id'):
            # Check if current user has admin privileges
            user_scopes = current_user.get('scope', [])
            if 'admin' not in user_scopes and 'user:write' not in user_scopes:
                return error_response(
                    error_code="INSUFFICIENT_PERMISSIONS",
                    message="You can only update your own user information",
                    status_code=403
                )
        
        # Update user
        update_data = user_data.dict(exclude_unset=True)
        updated_user = user_repo.update_user(user_id, update_data)
        
        logger.info(f"User {user_id} updated successfully - Request ID: {request_id}")
        
        return success_response(
            data=updated_user,
            message="User updated successfully"
        )
        
    except ConflictError as e:
        logger.warning(f"User update conflict: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="USER_CONFLICT",
            message=str(e),
            status_code=409
        )
    except Exception as e:
        logger.error(f"Update user error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="UPDATE_USER_ERROR",
            message="Failed to update user",
            status_code=500
        )


@router.delete("/{user_id}", response_model=Dict[str, Any])
@track_api_call("users_delete")
async def delete_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Delete user
    Only admins can delete users, or users can delete their own account
    """
    logger.info(f"Delete user {user_id} requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        user_repo = UserRepository(db)
        
        # Get the user to check permissions
        existing_user = user_repo.get(user_id)
        if not existing_user:
            return error_response(
                error_code="USER_NOT_FOUND",
                message=f"User with ID {user_id} not found",
                status_code=404
            )
        
        # Check permissions - users can delete their own account or admins can delete any user
        if existing_user['cognito_user_id'] != current_user.get('cognito_user_id'):
            # Check if current user has admin privileges
            user_scopes = current_user.get('scope', [])
            if 'admin' not in user_scopes:
                return error_response(
                    error_code="INSUFFICIENT_PERMISSIONS",
                    message="You can only delete your own account",
                    status_code=403
                )
        
        # Delete user
        user_repo.delete(user_id)
        
        logger.info(f"User {user_id} deleted successfully - Request ID: {request_id}")
        
        return success_response(
            data={"deleted_user_id": user_id},
            message="User deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Delete user error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="DELETE_USER_ERROR",
            message="Failed to delete user",
            status_code=500
        )


# User profile endpoints
@router.get("/{user_id}/profile", response_model=Dict[str, Any])
async def get_user_profile(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Get user profile information
    """
    logger.info(f"Get profile for user {user_id} requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        profile_repo = UserProfileRepository(db)
        profile = profile_repo.get_by_user_id(user_id)
        
        if not profile:
            return error_response(
                error_code="PROFILE_NOT_FOUND",
                message=f"Profile for user {user_id} not found",
                status_code=404
            )
        
        return success_response(
            data=profile,
            message="User profile retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get user profile error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="GET_PROFILE_ERROR",
            message="Failed to retrieve user profile",
            status_code=500
        )


@router.put("/{user_id}/profile", response_model=Dict[str, Any])
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: pymysql.Connection = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Update user profile information
    """
    logger.info(f"Update profile for user {user_id} requested by: {current_user.get('username')} - Request ID: {request_id}")
    
    try:
        # Check if user exists and permissions
        user_repo = UserRepository(db)
        user = user_repo.get(user_id)
        
        if not user:
            return error_response(
                error_code="USER_NOT_FOUND",
                message=f"User with ID {user_id} not found",
                status_code=404
            )
        
        # Check permissions - users can update their own profile or admins can update any profile
        if user['cognito_user_id'] != current_user.get('cognito_user_id'):
            # Check if current user has admin privileges
            user_scopes = current_user.get('scope', [])
            if 'admin' not in user_scopes and 'profile:write' not in user_scopes:
                return error_response(
                    error_code="INSUFFICIENT_PERMISSIONS",
                    message="You can only update your own profile",
                    status_code=403
                )
        
        profile_repo = UserProfileRepository(db)
        update_data = profile_data.dict(exclude_unset=True)
        
        updated_profile = profile_repo.update_profile(user_id, update_data)
        
        logger.info(f"Profile for user {user_id} updated successfully - Request ID: {request_id}")
        
        return success_response(
            data=updated_profile,
            message="User profile updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Update user profile error: {str(e)} - Request ID: {request_id}")
        return error_response(
            error_code="UPDATE_PROFILE_ERROR",
            message="Failed to update user profile",
            status_code=500
        )