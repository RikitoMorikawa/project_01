"""
リポジトリクラスの単体テスト
Unit tests for repository classes
"""
import pytest
from unittest.mock import Mock, patch
import pymysql

from app.repositories.user import UserRepository, UserProfileRepository
from app.exceptions import DatabaseError, ConflictError


class TestUserRepository:
    """ユーザーリポジトリのテストクラス / User repository test class"""
    
    def test_get_by_email_success(self, mock_db_connection, sample_user_data):
        """メールアドレスでのユーザー取得成功テスト / Test successful get user by email"""
        mock_connection, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = sample_user_data
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [sample_user_data]
            
            repo = UserRepository(mock_connection)
            result = repo.get_by_email("test@example.com")
            
            assert result is not None
            assert result["email"] == "test@example.com"
            mock_execute_query.assert_called_once()
    
    def test_get_by_email_not_found(self, mock_db_connection):
        """メールアドレスでのユーザー取得失敗テスト / Test get user by email not found"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = []
            
            repo = UserRepository(mock_connection)
            result = repo.get_by_email("nonexistent@example.com")
            
            assert result is None
    
    def test_get_by_cognito_id_success(self, mock_db_connection, sample_user_data):
        """Cognito IDでのユーザー取得成功テスト / Test successful get user by Cognito ID"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [sample_user_data]
            
            repo = UserRepository(mock_connection)
            result = repo.get_by_cognito_id("test-cognito-id-123")
            
            assert result is not None
            assert result["cognito_user_id"] == "test-cognito-id-123"
    
    def test_get_by_username_success(self, mock_db_connection, sample_user_data):
        """ユーザー名でのユーザー取得成功テスト / Test successful get user by username"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [sample_user_data]
            
            repo = UserRepository(mock_connection)
            result = repo.get_by_username("testuser")
            
            assert result is not None
            assert result["username"] == "testuser"
    
    def test_get_with_profile_success(self, mock_db_connection, sample_user_data, sample_user_profile_data):
        """プロファイル付きユーザー取得成功テスト / Test successful get user with profile"""
        mock_connection, mock_cursor = mock_db_connection
        
        # プロファイル付きのユーザーデータを作成 / Create user data with profile
        user_with_profile_data = {
            **sample_user_data,
            'profile_id': sample_user_profile_data['id'],
            'first_name': sample_user_profile_data['first_name'],
            'last_name': sample_user_profile_data['last_name'],
            'avatar_url': sample_user_profile_data['avatar_url'],
            'bio': sample_user_profile_data['bio'],
            'profile_created_at': sample_user_profile_data['created_at'],
            'profile_updated_at': sample_user_profile_data['updated_at']
        }
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [user_with_profile_data]
            
            repo = UserRepository(mock_connection)
            result = repo.get_with_profile(1)
            
            assert result is not None
            assert result["id"] == 1
            assert result["profile"] is not None
            assert result["profile"]["first_name"] == "テスト"
    
    def test_get_with_profile_no_profile(self, mock_db_connection, sample_user_data):
        """プロファイルなしユーザー取得テスト / Test get user with no profile"""
        mock_connection, mock_cursor = mock_db_connection
        
        # プロファイルなしのユーザーデータ / User data without profile
        user_without_profile_data = {
            **sample_user_data,
            'profile_id': None,
            'first_name': None,
            'last_name': None,
            'avatar_url': None,
            'bio': None,
            'profile_created_at': None,
            'profile_updated_at': None
        }
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [user_without_profile_data]
            
            repo = UserRepository(mock_connection)
            result = repo.get_with_profile(1)
            
            assert result is not None
            assert result["id"] == 1
            assert result["profile"] is None
    
    def test_create_user_success(self, mock_db_connection, sample_user_data):
        """ユーザー作成成功テスト / Test successful user creation"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.database.execute_query') as mock_execute_query, \
             patch('app.repositories.base.BaseRepository.create') as mock_create:
            
            # メール、ユーザー名、Cognito IDの重複チェックで空の結果を返す
            # Return empty results for duplicate checks
            mock_execute_query.return_value = []
            mock_create.return_value = sample_user_data
            
            repo = UserRepository(mock_connection)
            user_data = {
                "cognito_user_id": "new-cognito-id",
                "email": "newuser@example.com",
                "username": "newuser"
            }
            
            result = repo.create_user(user_data)
            
            assert result is not None
            assert result["email"] == sample_user_data["email"]
            mock_create.assert_called_once_with(user_data)
    
    def test_create_user_email_conflict(self, mock_db_connection, sample_user_data):
        """メールアドレス重複でのユーザー作成テスト / Test user creation with email conflict"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserRepository.get_by_email') as mock_get_by_email:
            mock_get_by_email.return_value = sample_user_data  # 既存ユーザーが存在
            
            repo = UserRepository(mock_connection)
            user_data = {
                "cognito_user_id": "new-cognito-id",
                "email": "test@example.com",  # 既存のメールアドレス
                "username": "newuser"
            }
            
            with pytest.raises(ConflictError) as exc_info:
                repo.create_user(user_data)
            
            assert "email already exists" in str(exc_info.value)
    
    def test_create_user_username_conflict(self, mock_db_connection, sample_user_data):
        """ユーザー名重複でのユーザー作成テスト / Test user creation with username conflict"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserRepository.get_by_email') as mock_get_by_email, \
             patch('app.repositories.user.UserRepository.get_by_username') as mock_get_by_username:
            
            mock_get_by_email.return_value = None  # メールは重複なし
            mock_get_by_username.return_value = sample_user_data  # ユーザー名が重複
            
            repo = UserRepository(mock_connection)
            user_data = {
                "cognito_user_id": "new-cognito-id",
                "email": "newuser@example.com",
                "username": "testuser"  # 既存のユーザー名
            }
            
            with pytest.raises(ConflictError) as exc_info:
                repo.create_user(user_data)
            
            assert "username already exists" in str(exc_info.value)
    
    def test_create_user_cognito_id_conflict(self, mock_db_connection, sample_user_data):
        """Cognito ID重複でのユーザー作成テスト / Test user creation with Cognito ID conflict"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserRepository.get_by_email') as mock_get_by_email, \
             patch('app.repositories.user.UserRepository.get_by_username') as mock_get_by_username, \
             patch('app.repositories.user.UserRepository.get_by_cognito_id') as mock_get_by_cognito_id:
            
            mock_get_by_email.return_value = None
            mock_get_by_username.return_value = None
            mock_get_by_cognito_id.return_value = sample_user_data  # Cognito IDが重複
            
            repo = UserRepository(mock_connection)
            user_data = {
                "cognito_user_id": "test-cognito-id-123",  # 既存のCognito ID
                "email": "newuser@example.com",
                "username": "newuser"
            }
            
            with pytest.raises(ConflictError) as exc_info:
                repo.create_user(user_data)
            
            assert "Cognito ID already exists" in str(exc_info.value)
    
    def test_update_user_success(self, mock_db_connection, sample_user_data):
        """ユーザー更新成功テスト / Test successful user update"""
        mock_connection, mock_cursor = mock_db_connection
        
        updated_user = sample_user_data.copy()
        updated_user['username'] = 'updateduser'
        
        with patch('app.repositories.user.UserRepository.get_by_email') as mock_get_by_email, \
             patch('app.repositories.user.UserRepository.get_by_username') as mock_get_by_username, \
             patch('app.repositories.base.BaseRepository.update') as mock_update:
            
            mock_get_by_email.return_value = None  # 新しいメールは重複なし
            mock_get_by_username.return_value = None  # 新しいユーザー名は重複なし
            mock_update.return_value = updated_user
            
            repo = UserRepository(mock_connection)
            update_data = {"username": "updateduser"}
            
            result = repo.update_user(1, update_data)
            
            assert result is not None
            assert result["username"] == "updateduser"
    
    def test_update_user_email_conflict(self, mock_db_connection, sample_user_data):
        """メールアドレス重複でのユーザー更新テスト / Test user update with email conflict"""
        mock_connection, mock_cursor = mock_db_connection
        
        # 異なるユーザーが同じメールアドレスを使用 / Different user using same email
        conflicting_user = sample_user_data.copy()
        conflicting_user['id'] = 2
        
        with patch('app.repositories.user.UserRepository.get_by_email') as mock_get_by_email:
            mock_get_by_email.return_value = conflicting_user
            
            repo = UserRepository(mock_connection)
            update_data = {"email": "test@example.com"}
            
            with pytest.raises(ConflictError) as exc_info:
                repo.update_user(1, update_data)  # ユーザーID 1を更新しようとする
            
            assert "Email already in use" in str(exc_info.value)
    
    def test_search_users_success(self, mock_db_connection, sample_user_data):
        """ユーザー検索成功テスト / Test successful user search"""
        mock_connection, mock_cursor = mock_db_connection
        
        search_results = [sample_user_data]
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = search_results
            
            repo = UserRepository(mock_connection)
            result = repo.search_users("test", limit=10)
            
            assert len(result) == 1
            assert result[0]["username"] == "testuser"
            
            # 検索クエリの確認 / Verify search query
            call_args = mock_execute_query.call_args
            assert "LIKE" in call_args[0][1]  # SQLクエリにLIKEが含まれる
    
    def test_get_users_with_profiles_success(self, mock_db_connection, sample_user_data, sample_user_profile_data):
        """プロファイル付きユーザー一覧取得成功テスト / Test successful get users with profiles"""
        mock_connection, mock_cursor = mock_db_connection
        
        user_with_profile_data = {
            **sample_user_data,
            'profile_id': sample_user_profile_data['id'],
            'first_name': sample_user_profile_data['first_name'],
            'last_name': sample_user_profile_data['last_name'],
            'avatar_url': sample_user_profile_data['avatar_url'],
            'bio': sample_user_profile_data['bio'],
            'profile_created_at': sample_user_profile_data['created_at'],
            'profile_updated_at': sample_user_profile_data['updated_at']
        }
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [user_with_profile_data]
            
            repo = UserRepository(mock_connection)
            result = repo.get_users_with_profiles(skip=0, limit=10)
            
            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["profile"] is not None
            assert result[0]["profile"]["first_name"] == "テスト"


class TestUserProfileRepository:
    """ユーザープロファイルリポジトリのテストクラス / User profile repository test class"""
    
    def test_get_by_user_id_success(self, mock_db_connection, sample_user_profile_data):
        """ユーザーIDでのプロファイル取得成功テスト / Test successful get profile by user ID"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = [sample_user_profile_data]
            
            repo = UserProfileRepository(mock_connection)
            result = repo.get_by_user_id(1)
            
            assert result is not None
            assert result["user_id"] == 1
            assert result["first_name"] == "テスト"
    
    def test_get_by_user_id_not_found(self, mock_db_connection):
        """存在しないユーザーIDでのプロファイル取得テスト / Test get profile by non-existent user ID"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.database.execute_query') as mock_execute_query:
            mock_execute_query.return_value = []
            
            repo = UserProfileRepository(mock_connection)
            result = repo.get_by_user_id(999)
            
            assert result is None
    
    def test_create_profile_success(self, mock_db_connection, sample_user_profile_data):
        """プロファイル作成成功テスト / Test successful profile creation"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_by_user_id, \
             patch('app.repositories.base.BaseRepository.create') as mock_create:
            
            mock_get_by_user_id.return_value = None  # プロファイルが存在しない
            mock_create.return_value = sample_user_profile_data
            
            repo = UserProfileRepository(mock_connection)
            profile_data = {
                "user_id": 1,
                "first_name": "テスト",
                "last_name": "ユーザー"
            }
            
            result = repo.create_profile(profile_data)
            
            assert result is not None
            assert result["user_id"] == 1
            assert result["first_name"] == "テスト"
    
    def test_create_profile_already_exists(self, mock_db_connection, sample_user_profile_data):
        """既存プロファイル作成テスト / Test create profile when already exists"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_by_user_id:
            mock_get_by_user_id.return_value = sample_user_profile_data  # プロファイルが既に存在
            
            repo = UserProfileRepository(mock_connection)
            profile_data = {
                "user_id": 1,
                "first_name": "テスト",
                "last_name": "ユーザー"
            }
            
            with pytest.raises(ConflictError) as exc_info:
                repo.create_profile(profile_data)
            
            assert "Profile already exists" in str(exc_info.value)
    
    def test_update_profile_success(self, mock_db_connection, sample_user_profile_data):
        """プロファイル更新成功テスト / Test successful profile update"""
        mock_connection, mock_cursor = mock_db_connection
        
        updated_profile = sample_user_profile_data.copy()
        updated_profile['bio'] = '更新された自己紹介'
        
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_by_user_id, \
             patch('app.repositories.base.BaseRepository.update') as mock_update:
            
            mock_get_by_user_id.return_value = sample_user_profile_data
            mock_update.return_value = updated_profile
            
            repo = UserProfileRepository(mock_connection)
            update_data = {"bio": "更新された自己紹介"}
            
            result = repo.update_profile(1, update_data)
            
            assert result is not None
            assert result["bio"] == "更新された自己紹介"
    
    def test_update_profile_create_if_not_exists(self, mock_db_connection, sample_user_profile_data):
        """存在しないプロファイル更新時の作成テスト / Test create profile when updating non-existent profile"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_by_user_id, \
             patch('app.repositories.user.UserProfileRepository.create_profile') as mock_create_profile:
            
            mock_get_by_user_id.return_value = None  # プロファイルが存在しない
            mock_create_profile.return_value = sample_user_profile_data
            
            repo = UserProfileRepository(mock_connection)
            update_data = {"first_name": "テスト"}
            
            result = repo.update_profile(1, update_data)
            
            assert result is not None
            # create_profileが呼ばれることを確認 / Verify create_profile is called
            mock_create_profile.assert_called_once()
    
    def test_delete_by_user_id_success(self, mock_db_connection, sample_user_profile_data):
        """ユーザーIDでのプロファイル削除成功テスト / Test successful delete profile by user ID"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_by_user_id, \
             patch('app.repositories.base.BaseRepository.delete') as mock_delete:
            
            mock_get_by_user_id.return_value = sample_user_profile_data
            mock_delete.return_value = True
            
            repo = UserProfileRepository(mock_connection)
            result = repo.delete_by_user_id(1)
            
            assert result is True
            mock_delete.assert_called_once_with(sample_user_profile_data['id'])
    
    def test_delete_by_user_id_not_found(self, mock_db_connection):
        """存在しないプロファイル削除テスト / Test delete non-existent profile"""
        mock_connection, mock_cursor = mock_db_connection
        
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_by_user_id:
            mock_get_by_user_id.return_value = None  # プロファイルが存在しない
            
            repo = UserProfileRepository(mock_connection)
            result = repo.delete_by_user_id(999)
            
            assert result is False