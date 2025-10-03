"""
データアクセス制御ミドルウェア

個人データへのアクセスを制御し、監査ログを記録する
GDPR および個人情報保護法に準拠したアクセス制御機能
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Callable, Dict, Any, Optional, List
import logging
import json
from datetime import datetime

from ..utils.audit_logging import AuditLogger, AuditAction, DataCategory
from ..database import get_db_connection

logger = logging.getLogger(__name__)


class DataAccessControlMiddleware:
    """データアクセス制御ミドルウェアクラス
    
    個人データへのアクセスを監視・制御し、監査ログを記録する
    """
    
    def __init__(self):
        """ミドルウェアの初期化"""
        # 個人データを含むエンドポイントの定義
        self.personal_data_endpoints = {
            "/api/v1/users": {
                "GET": {"category": DataCategory.PERSONAL_INFO, "fields": ["email", "username", "profile"]},
                "PUT": {"category": DataCategory.PERSONAL_INFO, "fields": ["email", "username", "profile"]},
                "DELETE": {"category": DataCategory.PERSONAL_INFO, "fields": ["all_user_data"]}
            },
            "/api/v1/users/{user_id}": {
                "GET": {"category": DataCategory.PERSONAL_INFO, "fields": ["email", "username", "profile"]},
                "PUT": {"category": DataCategory.PERSONAL_INFO, "fields": ["email", "username", "profile"]},
                "DELETE": {"category": DataCategory.PERSONAL_INFO, "fields": ["all_user_data"]}
            },
            "/api/v1/consent": {
                "GET": {"category": DataCategory.PERSONAL_INFO, "fields": ["consent_status"]},
                "POST": {"category": DataCategory.PERSONAL_INFO, "fields": ["consent_data"]}
            },
            "/api/v1/data/export": {
                "POST": {"category": DataCategory.PERSONAL_INFO, "fields": ["all_personal_data"]}
            }
        }
        
        # 管理者権限が必要なエンドポイント
        self.admin_only_endpoints = {
            "/api/v1/admin/users",
            "/api/v1/admin/audit-logs",
            "/api/v1/admin/data-retention"
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """ミドルウェアの実行
        
        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラー
            
        Returns:
            Response: HTTPレスポンス
        """
        # リクエスト情報の取得
        path = request.url.path
        method = request.method
        
        # 個人データアクセスの確認
        is_personal_data_access = self._is_personal_data_endpoint(path, method)
        
        # 管理者権限の確認
        is_admin_endpoint = self._is_admin_endpoint(path)
        
        # アクセス制御の実行
        if is_personal_data_access or is_admin_endpoint:
            access_check_result = await self._check_access_permissions(
                request, path, method, is_admin_endpoint
            )
            
            if not access_check_result["allowed"]:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error_code": "ACCESS_DENIED",
                        "message": access_check_result["reason"],
                        "details": {"path": path, "method": method}
                    }
                )
        
        # リクエスト処理の実行
        start_time = datetime.utcnow()
        
        try:
            response = await call_next(request)
            
            # 成功時の監査ログ記録
            if is_personal_data_access:
                await self._log_data_access(
                    request, path, method, response.status_code, start_time
                )
            
            return response
            
        except Exception as e:
            # エラー時の監査ログ記録
            if is_personal_data_access:
                await self._log_data_access(
                    request, path, method, 500, start_time, error=str(e)
                )
            
            raise e
    
    def _is_personal_data_endpoint(self, path: str, method: str) -> bool:
        """個人データエンドポイントの判定
        
        Args:
            path: リクエストパス
            method: HTTPメソッド
            
        Returns:
            bool: 個人データエンドポイントの場合 True
        """
        # 完全一致チェック
        if path in self.personal_data_endpoints:
            return method in self.personal_data_endpoints[path]
        
        # パターンマッチング（パスパラメータ対応）
        for endpoint_pattern in self.personal_data_endpoints:
            if self._match_path_pattern(path, endpoint_pattern):
                return method in self.personal_data_endpoints[endpoint_pattern]
        
        return False
    
    def _is_admin_endpoint(self, path: str) -> bool:
        """管理者エンドポイントの判定
        
        Args:
            path: リクエストパス
            
        Returns:
            bool: 管理者エンドポイントの場合 True
        """
        return any(path.startswith(admin_path) for admin_path in self.admin_only_endpoints)
    
    def _match_path_pattern(self, path: str, pattern: str) -> bool:
        """パスパターンマッチング
        
        Args:
            path: 実際のパス
            pattern: パターン（{param}形式のパラメータを含む）
            
        Returns:
            bool: マッチする場合 True
        """
        path_parts = path.strip('/').split('/')
        pattern_parts = pattern.strip('/').split('/')
        
        if len(path_parts) != len(pattern_parts):
            return False
        
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                # パスパラメータの場合はスキップ
                continue
            elif path_part != pattern_part:
                return False
        
        return True
    
    async def _check_access_permissions(
        self, 
        request: Request, 
        path: str, 
        method: str, 
        is_admin_endpoint: bool
    ) -> Dict[str, Any]:
        """アクセス権限の確認
        
        Args:
            request: HTTPリクエスト
            path: リクエストパス
            method: HTTPメソッド
            is_admin_endpoint: 管理者エンドポイントフラグ
            
        Returns:
            Dict[str, Any]: アクセス許可結果
        """
        try:
            # 認証情報の取得
            authorization = request.headers.get("authorization")
            if not authorization:
                return {
                    "allowed": False,
                    "reason": "認証が必要です"
                }
            
            # ユーザー情報の取得（実際の実装では JWT トークンから取得）
            # ここでは簡略化
            user_info = await self._get_user_from_token(authorization)
            if not user_info:
                return {
                    "allowed": False,
                    "reason": "無効な認証トークンです"
                }
            
            # 管理者権限の確認
            if is_admin_endpoint:
                if not user_info.get("is_admin", False):
                    return {
                        "allowed": False,
                        "reason": "管理者権限が必要です"
                    }
            
            # 自分のデータへのアクセス確認
            if "/users/" in path and method in ["GET", "PUT", "DELETE"]:
                path_user_id = self._extract_user_id_from_path(path)
                if path_user_id and path_user_id != user_info["id"]:
                    if not user_info.get("is_admin", False):
                        return {
                            "allowed": False,
                            "reason": "他のユーザーのデータにはアクセスできません"
                        }
            
            return {
                "allowed": True,
                "user_info": user_info
            }
            
        except Exception as e:
            logger.error(f"アクセス権限確認エラー: {e}")
            return {
                "allowed": False,
                "reason": "アクセス権限の確認に失敗しました"
            }
    
    async def _get_user_from_token(self, authorization: str) -> Optional[Dict[str, Any]]:
        """認証トークンからユーザー情報を取得
        
        Args:
            authorization: Authorization ヘッダー
            
        Returns:
            Optional[Dict[str, Any]]: ユーザー情報
        """
        # 実際の実装では JWT トークンの検証を行う
        # ここでは簡略化したダミー実装
        try:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
                # JWT デコード処理（省略）
                return {
                    "id": 1,  # ダミーユーザーID
                    "email": "user@example.com",
                    "is_admin": False
                }
        except Exception as e:
            logger.error(f"トークン解析エラー: {e}")
        
        return None
    
    def _extract_user_id_from_path(self, path: str) -> Optional[int]:
        """パスからユーザーIDを抽出
        
        Args:
            path: リクエストパス
            
        Returns:
            Optional[int]: ユーザーID
        """
        try:
            # /api/v1/users/{user_id} からユーザーIDを抽出
            parts = path.strip('/').split('/')
            if len(parts) >= 4 and parts[2] == "users":
                return int(parts[3])
        except (ValueError, IndexError):
            pass
        
        return None
    
    async def _log_data_access(
        self,
        request: Request,
        path: str,
        method: str,
        status_code: int,
        start_time: datetime,
        error: Optional[str] = None
    ):
        """データアクセスログの記録
        
        Args:
            request: HTTPリクエスト
            path: リクエストパス
            method: HTTPメソッド
            status_code: レスポンスステータスコード
            start_time: リクエスト開始時刻
            error: エラー情報
        """
        try:
            # データベース接続の取得
            db = await get_db_connection()
            audit_logger = AuditLogger(db)
            
            # リクエスト情報の取得
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            # ユーザー情報の取得
            authorization = request.headers.get("authorization")
            user_info = await self._get_user_from_token(authorization) if authorization else None
            user_id = user_info["id"] if user_info else None
            
            # アクセスされたフィールドの特定
            accessed_fields = self._get_accessed_fields(path, method)
            
            # アクションの決定
            action = self._determine_action(method, status_code)
            
            # 監査ログの記録
            await audit_logger.log_data_access(
                user_id=user_id,
                action=action,
                data_category=DataCategory.PERSONAL_INFO,
                target_user_id=self._extract_user_id_from_path(path) or user_id,
                details={
                    "path": path,
                    "method": method,
                    "status_code": status_code,
                    "accessed_fields": accessed_fields,
                    "processing_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    "error": error
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except Exception as e:
            logger.error(f"データアクセスログ記録エラー: {e}")
    
    def _get_accessed_fields(self, path: str, method: str) -> List[str]:
        """アクセスされたフィールドの取得
        
        Args:
            path: リクエストパス
            method: HTTPメソッド
            
        Returns:
            List[str]: アクセスされたフィールドリスト
        """
        # エンドポイント設定からフィールドを取得
        for endpoint_pattern, methods in self.personal_data_endpoints.items():
            if self._match_path_pattern(path, endpoint_pattern) and method in methods:
                return methods[method]["fields"]
        
        return ["unknown"]
    
    def _determine_action(self, method: str, status_code: int) -> AuditAction:
        """HTTPメソッドとステータスコードからアクションを決定
        
        Args:
            method: HTTPメソッド
            status_code: レスポンスステータスコード
            
        Returns:
            AuditAction: 監査アクション
        """
        if status_code >= 400:
            return AuditAction.ACCESS_DENIED
        
        method_action_map = {
            "GET": AuditAction.READ,
            "POST": AuditAction.CREATE,
            "PUT": AuditAction.UPDATE,
            "PATCH": AuditAction.UPDATE,
            "DELETE": AuditAction.DELETE
        }
        
        return method_action_map.get(method, AuditAction.READ)


# ミドルウェア関数
async def data_access_control_middleware(request: Request, call_next: Callable) -> Response:
    """データアクセス制御ミドルウェア関数
    
    Args:
        request: HTTPリクエスト
        call_next: 次のミドルウェア/ハンドラー
        
    Returns:
        Response: HTTPレスポンス
    """
    middleware = DataAccessControlMiddleware()
    return await middleware(request, call_next)