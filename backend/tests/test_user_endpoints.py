"""
ユーザーエンドポイントの単体テスト
Unit tests for user endpoints
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.exceptions import NotFoundError, ConflictError, AuthorizationError


class TestUserEndpoints:
    """ユーザーエンドポイントのテストクラス / User endpoints test class"""
    
    def test_get_users_success(self, client: TestClient, mock_current_user, mock_database_operations, 
                              sample_user_data, mock_request_id):
        """ユーザー一覧取得成功のテスト / Test successful get users"""
        # モックデータベースレスポンス / Mock database response
        mock_database_operations['execute_query'].return_value = [sample_user_data]
        
        with patch('app.repositories.user.UserRepository.get_multi') as mock_get_multi, \
             patch('app.repositories.user.UserRepository.count') as mock_count:
            
            mock_get_multi.return_value = [sample_user_data]
            mock_count.return_value = 1
            
            response = client.get("/api/v1/users/", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 1
            assert data["total"] == 1
            assert data["page"] == 1
    
    def test_get_users_with_pagination(self, client: TestClient, mock_current_user, 
                                     mock_database_operations, sample_user_data, mock_request_id):
        """ページネーション付きユーザー一覧取得のテスト / Test get users with pagination"""
        users_data = [sample_user_data.copy() for _ in range(5)]
        for i, user in enumerate(users_data):
            user['id'] = i + 1
            user['email'] = f'user{i+1}@example.com'
        
        with patch('app.repositories.user.UserRepository.get_multi') as mock_get_multi, \
             patch('app.repositories.user.UserRepository.count') as mock_count:
            
            mock_get_multi.return_value = users_data[:2]  # ページサイズ2 / Page size 2
            mock_count.return_value = 5
            
            response = client.get("/api/v1/users/?page=1&page_size=2", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 2
            assert data["total"] == 5
            assert data["page"] == 1
            assert data["page_size"] == 2
    
    def test_get_users_with_search(self, client: TestClient, mock_current_user, 
                                 mock_database_operations, sample_user_data, mock_request_id):
        """検索付きユーザー一覧取得のテスト / Test get users with search"""
        with patch('app.repositories.user.UserRepository.search_users') as mock_search:
            mock_search.return_value = [sample_user_data]
            
            response = client.get("/api/v1/users/?search=test", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 1
            mock_search.assert_called_once_with("test", limit=10)
    
    def test_create_user_success(self, client: TestClient, mock_current_user, 
                               mock_database_operations, sample_user_data, mock_request_id):
        """ユーザー作成成功のテスト / Test successful user creation"""
        with patch('app.repositories.user.UserRepository.create_user') as mock_create:
            mock_create.return_value = sample_user_data
            
            user_create_data = {
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
            
            response = client.post("/api/v1/users/", 
                                 json=user_create_data,
                                 headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["email"] == sample_user_data["email"]
    
    def test_create_user_email_conflict(self, client: TestClient, mock_current_user, 
                                      mock_database_operations, mock_request_id):
        """メールアドレス重複でのユーザー作成テスト / Test user creation with email conflict"""
        with patch('app.repositories.user.UserRepository.create_user') as mock_create:
            mock_create.side_effect = ConflictError(
                "User with this email already exists",
                {"field": "email", "value": "existing@example.com"}
            )
            
            user_create_data = {
                "email": "existing@example.com",
                "username": "newuser",
                "password": "password123"
            }
            
            response = client.post("/api/v1/users/", 
                                 json=user_create_data,
                                 headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 409
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_CONFLICT"
    
    def test_create_user_invalid_data(self, client: TestClient, mock_current_user, mock_request_id):
        """無効なデータでのユーザー作成テスト / Test user creation with invalid data"""
        invalid_user_data = {
            "email": "invalid-email",  # 無効なメール形式 / Invalid email format
            "username": "a",  # 短すぎるユーザー名 / Username too short
            "password": "123"  # 短すぎるパスワード / Password too short
        }
        
        response = client.post("/api/v1/users/", 
                             json=invalid_user_data,
                             headers={"Authorization": "Bearer valid-token"})
        
        assert response.status_code == 422  # Validation error
    
    def test_get_user_success(self, client: TestClient, mock_current_user, 
                            mock_database_operations, sample_user_data, mock_request_id):
        """ユーザー取得成功のテスト / Test successful get user"""
        with patch('app.repositories.user.UserRepository.get') as mock_get:
            mock_get.return_value = sample_user_data
            
            response = client.get("/api/v1/users/1", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == sample_user_data["id"]
    
    def test_get_user_with_profile(self, client: TestClient, mock_current_user, 
                                 mock_database_operations, sample_user_data, 
                                 sample_user_profile_data, mock_request_id):
        """プロファイル付きユーザー取得のテスト / Test get user with profile"""
        user_with_profile = sample_user_data.copy()
        user_with_profile['profile'] = sample_user_profile_data
        
        with patch('app.repositories.user.UserRepository.get_with_profile') as mock_get_with_profile:
            mock_get_with_profile.return_value = user_with_profile
            
            response = client.get("/api/v1/users/1?include_profile=true", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "profile" in data["data"]
            assert data["data"]["profile"]["first_name"] == "テスト"
    
    def test_get_user_not_found(self, client: TestClient, mock_current_user, 
                              mock_database_operations, mock_request_id):
        """存在しないユーザー取得のテスト / Test get non-existent user"""
        with patch('app.repositories.user.UserRepository.get') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/v1/users/999", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 404
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_get_user_insufficient_permissions(self, client: TestClient, mock_database_operations, 
                                             sample_user_data, mock_request_id):
        """権限不足でのユーザー取得テスト / Test get user with insufficient permissions"""
        # 異なるユーザーとして認証 / Authenticate as different user
        with patch('app.auth.dependencies.get_current_user') as mock_get_current_user, \
             patch('app.repositories.user.UserRepository.get') as mock_get:
            
            mock_get_current_user.return_value = {
                'cognito_user_id': 'different-user-id',
                'username': 'differentuser',
                'scope': []  # 管理者権限なし / No admin privileges
            }
            mock_get.return_value = sample_user_data
            
            response = client.get("/api/v1/users/1", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 403
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "INSUFFICIENT_PERMISSIONS"
    
    def test_update_user_success(self, client: TestClient, mock_current_user, 
                               mock_database_operations, sample_user_data, mock_request_id):
        """ユーザー更新成功のテスト / Test successful user update"""
        updated_user = sample_user_data.copy()
        updated_user['username'] = 'updateduser'
        
        with patch('app.repositories.user.UserRepository.get') as mock_get, \
             patch('app.repositories.user.UserRepository.update_user') as mock_update:
            
            mock_get.return_value = sample_user_data
            mock_update.return_value = updated_user
            
            update_data = {"username": "updateduser"}
            
            response = client.put("/api/v1/users/1", 
                                json=update_data,
                                headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["username"] == "updateduser"
    
    def test_update_user_not_found(self, client: TestClient, mock_current_user, 
                                 mock_database_operations, mock_request_id):
        """存在しないユーザー更新のテスト / Test update non-existent user"""
        with patch('app.repositories.user.UserRepository.get') as mock_get:
            mock_get.return_value = None
            
            update_data = {"username": "updateduser"}
            
            response = client.put("/api/v1/users/999", 
                                json=update_data,
                                headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 404
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_update_user_username_conflict(self, client: TestClient, mock_current_user, 
                                         mock_database_operations, sample_user_data, mock_request_id):
        """ユーザー名重複での更新テスト / Test update user with username conflict"""
        with patch('app.repositories.user.UserRepository.get') as mock_get, \
             patch('app.repositories.user.UserRepository.update_user') as mock_update:
            
            mock_get.return_value = sample_user_data
            mock_update.side_effect = ConflictError(
                "Username already in use by another user",
                {"field": "username", "value": "existinguser"}
            )
            
            update_data = {"username": "existinguser"}
            
            response = client.put("/api/v1/users/1", 
                                json=update_data,
                                headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 409
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_CONFLICT"
    
    def test_delete_user_success(self, client: TestClient, mock_current_user, 
                               mock_database_operations, sample_user_data, mock_request_id):
        """ユーザー削除成功のテスト / Test successful user deletion"""
        with patch('app.repositories.user.UserRepository.get') as mock_get, \
             patch('app.repositories.user.UserRepository.delete') as mock_delete:
            
            mock_get.return_value = sample_user_data
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/users/1", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["deleted_user_id"] == 1
    
    def test_delete_user_insufficient_permissions(self, client: TestClient, mock_database_operations, 
                                                sample_user_data, mock_request_id):
        """権限不足でのユーザー削除テスト / Test delete user with insufficient permissions"""
        with patch('app.auth.dependencies.get_current_user') as mock_get_current_user, \
             patch('app.repositories.user.UserRepository.get') as mock_get:
            
            mock_get_current_user.return_value = {
                'cognito_user_id': 'different-user-id',
                'username': 'differentuser',
                'scope': []  # 管理者権限なし / No admin privileges
            }
            mock_get.return_value = sample_user_data
            
            response = client.delete("/api/v1/users/1", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 403
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "INSUFFICIENT_PERMISSIONS"
    
    def test_get_user_profile_success(self, client: TestClient, mock_current_user, 
                                    mock_database_operations, sample_user_profile_data, mock_request_id):
        """ユーザープロファイル取得成功のテスト / Test successful get user profile"""
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_profile:
            mock_get_profile.return_value = sample_user_profile_data
            
            response = client.get("/api/v1/users/1/profile", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["first_name"] == "テスト"
    
    def test_get_user_profile_not_found(self, client: TestClient, mock_current_user, 
                                      mock_database_operations, mock_request_id):
        """存在しないプロファイル取得のテスト / Test get non-existent profile"""
        with patch('app.repositories.user.UserProfileRepository.get_by_user_id') as mock_get_profile:
            mock_get_profile.return_value = None
            
            response = client.get("/api/v1/users/1/profile", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 404
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "PROFILE_NOT_FOUND"
    
    def test_update_user_profile_success(self, client: TestClient, mock_current_user, 
                                       mock_database_operations, sample_user_data, 
                                       sample_user_profile_data, mock_request_id):
        """ユーザープロファイル更新成功のテスト / Test successful user profile update"""
        updated_profile = sample_user_profile_data.copy()
        updated_profile['bio'] = '更新された自己紹介'
        
        with patch('app.repositories.user.UserRepository.get') as mock_get_user, \
             patch('app.repositories.user.UserProfileRepository.update_profile') as mock_update_profile:
            
            mock_get_user.return_value = sample_user_data
            mock_update_profile.return_value = updated_profile
            
            update_data = {"bio": "更新された自己紹介"}
            
            response = client.put("/api/v1/users/1/profile", 
                                json=update_data,
                                headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["bio"] == "更新された自己紹介"
    
    def test_update_user_profile_user_not_found(self, client: TestClient, mock_current_user, 
                                              mock_database_operations, mock_request_id):
        """存在しないユーザーのプロファイル更新テスト / Test update profile for non-existent user"""
        with patch('app.repositories.user.UserRepository.get') as mock_get_user:
            mock_get_user.return_value = None
            
            update_data = {"bio": "新しい自己紹介"}
            
            response = client.put("/api/v1/users/999/profile", 
                                json=update_data,
                                headers={"Authorization": "Bearer valid-token"})
            
            assert response.status_code == 404
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_admin_can_access_any_user(self, client: TestClient, mock_admin_user, 
                                     mock_database_operations, sample_user_data, mock_request_id):
        """管理者が任意のユーザーにアクセスできることのテスト / Test admin can access any user"""
        with patch('app.repositories.user.UserRepository.get') as mock_get:
            mock_get.return_value = sample_user_data
            
            response = client.get("/api/v1/users/1", headers={
                "Authorization": "Bearer admin-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == sample_user_data["id"]