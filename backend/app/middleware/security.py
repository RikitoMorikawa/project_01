"""
セキュリティミドルウェア

セキュリティヘッダーの設定とセキュリティ強化機能を提供する
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    セキュリティヘッダーを追加するミドルウェア
    
    OWASP推奨のセキュリティヘッダーを自動的に追加する
    """
    
    def __init__(self, app, environment: str = "production"):
        super().__init__(app)
        self.environment = environment
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエスト処理とセキュリティヘッダーの追加"""
        
        # リクエスト処理
        response = await call_next(request)
        
        # セキュリティヘッダーの追加
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """セキュリティヘッダーを追加する"""
        
        # X-Content-Type-Options: MIME タイプスニッフィング攻撃を防ぐ
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: クリックジャッキング攻撃を防ぐ
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: XSS攻撃を防ぐ（レガシーブラウザ用）
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: リファラー情報の制御
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: ブラウザ機能の制御
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Content-Security-Policy: XSS攻撃を防ぐ
        if self.environment == "production":
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # 開発環境では緩い設定
            csp = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:"
            )
        
        response.headers["Content-Security-Policy"] = csp
        
        # Strict-Transport-Security: HTTPS強制（本番環境のみ）
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Cache-Control: 機密情報のキャッシュを防ぐ
        if "/api/v1/auth/" in str(response.headers.get("location", "")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    レート制限ミドルウェア
    
    IP アドレスベースでリクエスト数を制限する
    """
    
    def __init__(
        self, 
        app, 
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # リクエスト履歴を保存（本番環境では Redis を使用することを推奨）
        self.request_history = defaultdict(list)
        self.burst_history = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエスト処理とレート制限チェック"""
        
        client_ip = self._get_client_ip(request)
        current_time = datetime.now()
        
        # レート制限チェック
        if self._is_rate_limited(client_ip, current_time):
            logger.warning(f"レート制限に達しました: IP={client_ip}")
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                headers={"Content-Type": "application/json"}
            )
        
        # リクエスト履歴を記録
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """クライアント IP アドレスを取得する"""
        
        # CloudFront/ALB からの X-Forwarded-For ヘッダーをチェック
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP ヘッダーをチェック
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 直接接続の場合
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str, current_time: datetime) -> bool:
        """レート制限チェック"""
        
        # 古い履歴を削除
        self._cleanup_old_requests(client_ip, current_time)
        
        # バースト制限チェック（直近10秒間）
        burst_window = current_time - timedelta(seconds=10)
        recent_burst_requests = [
            req_time for req_time in self.burst_history[client_ip]
            if req_time > burst_window
        ]
        
        if len(recent_burst_requests) >= self.burst_limit:
            return True
        
        # 分間制限チェック
        minute_window = current_time - timedelta(minutes=1)
        recent_minute_requests = [
            req_time for req_time in self.request_history[client_ip]
            if req_time > minute_window
        ]
        
        if len(recent_minute_requests) >= self.requests_per_minute:
            return True
        
        # 時間制限チェック
        hour_window = current_time - timedelta(hours=1)
        recent_hour_requests = [
            req_time for req_time in self.request_history[client_ip]
            if req_time > hour_window
        ]
        
        if len(recent_hour_requests) >= self.requests_per_hour:
            return True
        
        return False
    
    def _record_request(self, client_ip: str, current_time: datetime) -> None:
        """リクエスト履歴を記録する"""
        
        self.request_history[client_ip].append(current_time)
        self.burst_history[client_ip].append(current_time)
        
        # メモリ使用量を制限するため、古い履歴を削除
        self._cleanup_old_requests(client_ip, current_time)
    
    def _cleanup_old_requests(self, client_ip: str, current_time: datetime) -> None:
        """古いリクエスト履歴を削除する"""
        
        # 1時間より古い履歴を削除
        hour_window = current_time - timedelta(hours=1)
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip]
            if req_time > hour_window
        ]
        
        # 10秒より古いバースト履歴を削除
        burst_window = current_time - timedelta(seconds=10)
        self.burst_history[client_ip] = [
            req_time for req_time in self.burst_history[client_ip]
            if req_time > burst_window
        ]


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    セキュリティログミドルウェア
    
    セキュリティ関連のイベントをログに記録する
    """
    
    def __init__(self, app):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエスト処理とセキュリティログ記録"""
        
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # 疑わしいリクエストパターンをチェック
        self._check_suspicious_patterns(request, client_ip, user_agent)
        
        # リクエスト処理
        response = await call_next(request)
        
        # レスポンス時間を計算
        process_time = time.time() - start_time
        
        # セキュリティログを記録
        self._log_security_event(request, response, client_ip, user_agent, process_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """クライアント IP アドレスを取得する"""
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _check_suspicious_patterns(self, request: Request, client_ip: str, user_agent: str) -> None:
        """疑わしいリクエストパターンをチェックする"""
        
        url_path = str(request.url.path).lower()
        query_params = str(request.url.query).lower()
        
        # SQL インジェクション攻撃パターン
        sql_injection_patterns = [
            "union select", "drop table", "insert into", "delete from",
            "update set", "exec(", "execute(", "sp_", "xp_"
        ]
        
        # XSS 攻撃パターン
        xss_patterns = [
            "<script", "javascript:", "onerror=", "onload=", "eval("
        ]
        
        # パストラバーサル攻撃パターン
        path_traversal_patterns = [
            "../", "..\\", "%2e%2e", "%252e%252e"
        ]
        
        # 疑わしいパターンをチェック
        suspicious_content = url_path + " " + query_params
        
        for pattern in sql_injection_patterns:
            if pattern in suspicious_content:
                logger.warning(
                    f"SQL インジェクション攻撃の可能性: IP={client_ip}, "
                    f"Pattern={pattern}, URL={request.url}"
                )
                break
        
        for pattern in xss_patterns:
            if pattern in suspicious_content:
                logger.warning(
                    f"XSS 攻撃の可能性: IP={client_ip}, "
                    f"Pattern={pattern}, URL={request.url}"
                )
                break
        
        for pattern in path_traversal_patterns:
            if pattern in suspicious_content:
                logger.warning(
                    f"パストラバーサル攻撃の可能性: IP={client_ip}, "
                    f"Pattern={pattern}, URL={request.url}"
                )
                break
        
        # 疑わしいユーザーエージェント
        suspicious_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp"
        ]
        
        for suspicious_ua in suspicious_user_agents:
            if suspicious_ua in user_agent.lower():
                logger.warning(
                    f"疑わしいユーザーエージェント: IP={client_ip}, "
                    f"UserAgent={user_agent}"
                )
                break
    
    def _log_security_event(
        self, 
        request: Request, 
        response: Response, 
        client_ip: str, 
        user_agent: str, 
        process_time: float
    ) -> None:
        """セキュリティイベントをログに記録する"""
        
        # 認証関連のエンドポイントは詳細ログを記録
        if "/api/v1/auth/" in str(request.url.path):
            logger.info(
                f"認証エンドポイントアクセス: "
                f"IP={client_ip}, "
                f"Method={request.method}, "
                f"Path={request.url.path}, "
                f"Status={response.status_code}, "
                f"ProcessTime={process_time:.3f}s, "
                f"UserAgent={user_agent}"
            )
        
        # エラーレスポンスをログに記録
        if response.status_code >= 400:
            logger.warning(
                f"エラーレスポンス: "
                f"IP={client_ip}, "
                f"Method={request.method}, "
                f"Path={request.url.path}, "
                f"Status={response.status_code}, "
                f"ProcessTime={process_time:.3f}s"
            )
        
        # 異常に遅いレスポンスをログに記録
        if process_time > 5.0:  # 5秒以上
            logger.warning(
                f"遅いレスポンス: "
                f"IP={client_ip}, "
                f"Method={request.method}, "
                f"Path={request.url.path}, "
                f"ProcessTime={process_time:.3f}s"
            )


def setup_security_middleware(app, environment: str = "production"):
    """
    セキュリティミドルウェアをセットアップする
    
    Args:
        app: FastAPI アプリケーション
        environment: 環境名（production, staging, development）
    """
    
    # セキュリティログミドルウェア
    app.add_middleware(SecurityLoggingMiddleware)
    
    # レート制限ミドルウェア（本番環境のみ）
    if environment == "production":
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_limit=10
        )
    elif environment == "staging":
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=120,
            requests_per_hour=2000,
            burst_limit=20
        )
    
    # セキュリティヘッダーミドルウェア
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)
    
    logger.info(f"セキュリティミドルウェアを設定しました: environment={environment}")