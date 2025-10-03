"""
FastAPI メインアプリケーション

CSR Lambda API システムのメインエントリーポイント。
AWS Lambda 環境で動作するサーバーレス API を提供する。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import auth, users, health
from app.middleware import (
    request_id_middleware,
    timing_middleware,
    error_handling_middleware,
    security_headers_middleware
)
from app.middleware.security import setup_security_middleware
from app.utils.metrics import metrics, BusinessMetrics
from app.utils.notifications import send_business_notification, send_critical_alert

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションライフサイクル管理
    
    FastAPI アプリケーションの開始・終了時に実行される処理を定義する。
    メトリクス収集、通知送信、リソースクリーンアップを行う。
    """
    # アプリケーション開始処理
    logger.info("CSR Lambda API を開始しています...")
    
    # アプリケーション開始メトリクス
    metrics.increment_counter('application_startup')
    
    # 開始通知（本番環境以外）
    if settings.environment != "prod":
        send_business_notification(
            "application_startup",
            f"CSR Lambda API が {settings.environment} 環境で開始されました",
            {"version": settings.api_version, "environment": settings.environment}
        )
    
    yield
    
    # アプリケーション終了処理
    logger.info("CSR Lambda API を終了しています...")
    
    # アプリケーション終了メトリクス
    metrics.increment_counter('application_shutdown')
    
    # メトリクスバッファをフラッシュ
    try:
        metrics.flush_buffer()
    except Exception as e:
        logger.error(f"メトリクスフラッシュエラー: {str(e)}")

# FastAPI アプリケーションの作成
app = FastAPI(
    title="CSR Lambda API システム",
    version=settings.api_version,
    description="""
    ## CSR Lambda API システム

    AWS Lambda で動作するクライアントサイドレンダリング用サーバーレス API バックエンド

    ### 主な機能
    - **認証**: AWS Cognito を使用したJWT認証
    - **ユーザー管理**: ユーザー情報の作成、取得、更新、削除
    - **ヘルスチェック**: システム稼働状況の監視
    - **メトリクス**: CloudWatch との統合によるパフォーマンス監視

    ### 認証について
    このAPIは AWS Cognito JWT トークンによる認証を使用します。
    認証が必要なエンドポイントには `Authorization: Bearer <token>` ヘッダーを含めてください。

    ### エラーレスポンス
    すべてのエラーレスポンスは以下の形式で返されます：
    ```json
    {
        "error_code": "ERROR_CODE",
        "message": "エラーメッセージ",
        "details": {}
    }
    ```

    ### 環境
    - **開発環境**: 開発・テスト用
    - **ステージング環境**: 本番前検証用
    - **本番環境**: 実運用環境
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "prod" else None,  # 本番環境では無効化
    redoc_url="/redoc" if settings.environment != "prod" else None,  # 本番環境では無効化
    contact={
        "name": "CSR Lambda API サポート",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "認証",
            "description": "ユーザー認証とトークン管理",
        },
        {
            "name": "ユーザー",
            "description": "ユーザー情報の管理",
        },
        {
            "name": "ヘルスチェック",
            "description": "システム稼働状況の監視",
        },
    ],
)

# セキュリティミドルウェア - 信頼できるホスト制限（本番環境のみ）
if settings.environment == "prod":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*.execute-api.ap-northeast-1.amazonaws.com", "*.cloudfront.net"]
    )

# セキュリティミドルウェアの設定
setup_security_middleware(app, settings.environment)

# カスタムミドルウェアの追加（順序重要 - 最初に追加されたものが最外層）
app.middleware("http")(security_headers_middleware)  # セキュリティヘッダー
app.middleware("http")(error_handling_middleware)    # エラーハンドリング
app.middleware("http")(timing_middleware)            # レスポンス時間計測
app.middleware("http")(request_id_middleware)        # リクエストID付与

# CORS ミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# API ルーターの登録
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(users.router, prefix="/api/v1/users", tags=["ユーザー"])
app.include_router(health.router, prefix="/api/v1/health", tags=["ヘルスチェック"])

# データ保護・プライバシー関連ルーター
from app.api.routes import consent
app.include_router(consent.router, prefix="/api/v1", tags=["データ保護・同意管理"])

@app.get("/")
async def root():
    """
    ルートエンドポイント
    
    API の基本情報とヘルスステータスを返す。
    API が正常に動作していることを確認するために使用される。
    
    Returns:
        dict: API の基本情報（メッセージ、バージョン、環境）
    """
    return {
        "message": "CSR Lambda API is running",
        "version": settings.api_version,
        "environment": settings.environment
    }