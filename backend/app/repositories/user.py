"""
User and UserProfile repository implementations using raw SQL
生SQLを使用したユーザーとユーザープロファイルリポジトリの実装
"""
from typing import Optional, List, Dict, Any
import pymysql
import logging

from app.repositories.base import BaseRepository
from app.database import execute_query, execute_update, execute_insert
from app.exceptions import DatabaseError, ConflictError

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for User table with specific user operations
    ユーザー固有の操作を持つユーザーテーブル用リポジトリ
    """
    
    def __init__(self, connection: pymysql.Connection):
        super().__init__(connection, "users")
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address / メールアドレスでユーザーを取得"""
        return self.get_by_field("email", email)
    
    def get_by_cognito_id(self, cognito_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Cognito user ID / Cognito ユーザーIDでユーザーを取得"""
        return self.get_by_field("cognito_user_id", cognito_user_id)
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username / ユーザー名でユーザーを取得"""
        return self.get_by_field("username", username)
    
    def get_with_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user with profile information loaded / プロファイル情報を含むユーザーを取得"""
        try:
            query = """
            SELECT u.*, 
                   p.id as profile_id, p.first_name, p.last_name, 
                   p.avatar_url, p.bio, p.created_at as profile_created_at,
                   p.updated_at as profile_updated_at
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = %s
            """
            results = execute_query(self.connection, query, (user_id,))
            
            if not results:
                return None
            
            user_data = results[0]
            
            # Separate user and profile data / ユーザーとプロファイルデータを分離
            user = {
                'id': user_data['id'],
                'cognito_user_id': user_data['cognito_user_id'],
                'email': user_data['email'],
                'username': user_data['username'],
                'created_at': user_data['created_at'],
                'updated_at': user_data['updated_at']
            }
            
            # Add profile if exists / プロファイルが存在する場合は追加
            if user_data['profile_id']:
                user['profile'] = {
                    'id': user_data['profile_id'],
                    'user_id': user_data['id'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'avatar_url': user_data['avatar_url'],
                    'bio': user_data['bio'],
                    'created_at': user_data['profile_created_at'],
                    'updated_at': user_data['profile_updated_at']
                }
            else:
                user['profile'] = None
            
            return user
            
        except Exception as e:
            logger.error(f"Database error in get_with_profile({user_id}): {str(e)}")
            raise DatabaseError("Failed to retrieve user with profile")
    
    def get_users_with_profiles(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get multiple users with their profiles loaded"""
        try:
            query = """
            SELECT u.*, 
                   p.id as profile_id, p.first_name, p.last_name, 
                   p.avatar_url, p.bio, p.created_at as profile_created_at,
                   p.updated_at as profile_updated_at
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            """
            params = []
            
            # Apply filters
            if filters:
                where_conditions = []
                for field_name, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ','.join(['%s'] * len(value))
                        where_conditions.append(f"u.{field_name} IN ({placeholders})")
                        params.extend(value)
                    else:
                        where_conditions.append(f"u.{field_name} = %s")
                        params.append(value)
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY u.created_at LIMIT %s OFFSET %s"
            params.extend([limit, skip])
            
            results = execute_query(self.connection, query, tuple(params))
            
            # Process results to combine user and profile data
            users = []
            for row in results:
                user = {
                    'id': row['id'],
                    'cognito_user_id': row['cognito_user_id'],
                    'email': row['email'],
                    'username': row['username'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                
                # Add profile if exists
                if row['profile_id']:
                    user['profile'] = {
                        'id': row['profile_id'],
                        'user_id': row['id'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'avatar_url': row['avatar_url'],
                        'bio': row['bio'],
                        'created_at': row['profile_created_at'],
                        'updated_at': row['profile_updated_at']
                    }
                else:
                    user['profile'] = None
                
                users.append(user)
            
            return users
            
        except Exception as e:
            logger.error(f"Database error in get_users_with_profiles: {str(e)}")
            raise DatabaseError("Failed to retrieve users with profiles")
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with validation / バリデーション付きで新しいユーザーを作成"""
        try:
            # Check if email already exists / メールアドレスが既に存在するかチェック
            if self.get_by_email(user_data.get("email")):
                raise ConflictError(
                    "User with this email already exists",
                    {"field": "email", "value": user_data.get("email")}
                )
            
            # Check if username already exists / ユーザー名が既に存在するかチェック
            if self.get_by_username(user_data.get("username")):
                raise ConflictError(
                    "User with this username already exists",
                    {"field": "username", "value": user_data.get("username")}
                )
            
            # Check if cognito_user_id already exists / Cognito ユーザーIDが既に存在するかチェック
            if user_data.get("cognito_user_id") and self.get_by_cognito_id(user_data.get("cognito_user_id")):
                raise ConflictError(
                    "User with this Cognito ID already exists",
                    {"field": "cognito_user_id", "value": user_data.get("cognito_user_id")}
                )
            
            return self.create(user_data)
            
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise DatabaseError("Failed to create user")
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user with validation"""
        try:
            # Check if new email conflicts with existing users
            if "email" in user_data:
                existing_user = self.get_by_email(user_data["email"])
                if existing_user and existing_user['id'] != user_id:
                    raise ConflictError(
                        "Email already in use by another user",
                        {"field": "email", "value": user_data["email"]}
                    )
            
            # Check if new username conflicts with existing users
            if "username" in user_data:
                existing_user = self.get_by_username(user_data["username"])
                if existing_user and existing_user['id'] != user_id:
                    raise ConflictError(
                        "Username already in use by another user",
                        {"field": "username", "value": user_data["username"]}
                    )
            
            return self.update(user_id, user_data)
            
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise DatabaseError("Failed to update user")
    
    def search_users(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search users by username or email"""
        try:
            search_pattern = f"%{search_term}%"
            query = """
            SELECT * FROM users 
            WHERE username LIKE %s OR email LIKE %s 
            ORDER BY username 
            LIMIT %s
            """
            return execute_query(self.connection, query, (search_pattern, search_pattern, limit))
            
        except Exception as e:
            logger.error(f"Database error in search_users: {str(e)}")
            raise DatabaseError("Failed to search users")


class UserProfileRepository(BaseRepository):
    """
    Repository for UserProfile table with specific profile operations
    """
    
    def __init__(self, connection: pymysql.Connection):
        super().__init__(connection, "user_profiles")
    
    def get_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get profile by user ID"""
        return self.get_by_field("user_id", user_id)
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile with validation"""
        try:
            # Check if profile already exists for this user
            if self.get_by_user_id(profile_data.get("user_id")):
                raise ConflictError(
                    "Profile already exists for this user",
                    {"field": "user_id", "value": profile_data.get("user_id")}
                )
            
            return self.create(profile_data)
            
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"Error creating profile: {str(e)}")
            raise DatabaseError("Failed to create user profile")
    
    def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile by user ID"""
        try:
            profile = self.get_by_user_id(user_id)
            if not profile:
                # Create profile if it doesn't exist
                profile_data["user_id"] = user_id
                return self.create_profile(profile_data)
            
            return self.update(profile['id'], profile_data)
            
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {str(e)}")
            raise DatabaseError("Failed to update user profile")
    
    def delete_by_user_id(self, user_id: int) -> bool:
        """Delete profile by user ID"""
        try:
            profile = self.get_by_user_id(user_id)
            if not profile:
                return False
            
            return self.delete(profile['id'])
            
        except Exception as e:
            logger.error(f"Error deleting profile for user {user_id}: {str(e)}")
            raise DatabaseError("Failed to delete user profile")