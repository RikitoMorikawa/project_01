"""
同意管理 API ルーター

ユーザーの同意状況管理とプライバシー設定を提供する
GDPR および個人情報保護法に準拠した同意管理機能
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ...auth.dependencies import get_current_user
from ...services.data_protection import DataProtectionService
from ...database import get_db_connection
from ...utils.audit_logging import log_user_data_read, log_user_data_update

logger = logging.getLogger(__name__)

router = APIRouter()


class ConsentRequest(BaseModel):
    """同意リクエストモデル"""
    consent_type: str
    consent_version: str
    consented: bool


class ConsentWithdrawalRequest(BaseModel):
    """同意撤回リクエストモデル"""
    consent_type: str


class ConsentResponse(BaseModel):
    """同意レスポンスモデル"""
    consent_type: str
    consent_version: str
    consented: bool
    consent_date: Optional[str]
    withdrawn_at: Optional[str]


class ConsentStatusResponse(BaseModel):
    """同意状況レスポンスモデル"""
    user_id: int
    consents: Dict[str, Dict[str, Any]]
    last_updated: str


@router.post("/consent", response_model=Dict[str, str])
async def create_consent_record(
    consent_request: ConsentRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    ユーザー同意記録の作成
    
    Args:
        consent_request: 同意リクエストデータ
        request: HTTPリクエスト
        current_user: 現在のユーザー情報
        db: データベース接続
        
    Returns:
        Dict[str, str]: 作成結果
    """
    try:
        user_id = current_user["id"]
        
        # クライアント情報の取得
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # データ保護サービスの初期化
        data_protection_service = DataProtectionService(db)
        
        # 同意記録の作成
        success = await data_protection_service.create_user_consent_record(
            user_id=user_id,
            consent_type=consent_request.consent_type,
            consent_version=consent_request.consent_version,
            consented=consent_request.consented,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="同意記録の作成に失敗しました"
            )
        
        logger.info(f"同意記録を作成しました (user_id: {user_id}, type: {consent_request.consent_type})")
        
        return {
            "message": "同意記録を作成しました",
            "consent_type": consent_request.consent_type,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"同意記録作成エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同意記録の作成に失敗しました: {str(e)}"
        )


@router.get("/consent/status", response_model=ConsentStatusResponse)
async def get_consent_status(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    ユーザーの同意状況取得
    
    Args:
        request: HTTPリクエスト
        current_user: 現在のユーザー情報
        db: データベース接続
        
    Returns:
        ConsentStatusResponse: 同意状況
    """
    try:
        user_id = current_user["id"]
        
        # クライアント情報の取得
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # データ保護サービスの初期化
        data_protection_service = DataProtectionService(db)
        
        # 同意状況の取得
        consent_status = await data_protection_service.get_user_consent_status(user_id)
        
        # 監査ログの記録
        await log_user_data_read(
            db_connection=db,
            user_id=user_id,
            target_user_id=user_id,
            accessed_fields=["consent_status"],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ConsentStatusResponse(
            user_id=user_id,
            consents=consent_status,
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"同意状況取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同意状況の取得に失敗しました: {str(e)}"
        )


@router.post("/consent/withdraw", response_model=Dict[str, str])
async def withdraw_consent(
    withdrawal_request: ConsentWithdrawalRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    ユーザー同意の撤回
    
    Args:
        withdrawal_request: 同意撤回リクエスト
        request: HTTPリクエスト
        current_user: 現在のユーザー情報
        db: データベース接続
        
    Returns:
        Dict[str, str]: 撤回結果
    """
    try:
        user_id = current_user["id"]
        
        # クライアント情報の取得
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # データ保護サービスの初期化
        data_protection_service = DataProtectionService(db)
        
        # 同意の撤回
        success = await data_protection_service.withdraw_user_consent(
            user_id=user_id,
            consent_type=withdrawal_request.consent_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="同意撤回の処理に失敗しました"
            )
        
        logger.info(f"同意を撤回しました (user_id: {user_id}, type: {withdrawal_request.consent_type})")
        
        return {
            "message": "同意を撤回しました",
            "consent_type": withdrawal_request.consent_type,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"同意撤回エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同意撤回の処理に失敗しました: {str(e)}"
        )


@router.get("/consent/history", response_model=List[ConsentResponse])
async def get_consent_history(
    request: Request,
    consent_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    ユーザーの同意履歴取得
    
    Args:
        request: HTTPリクエスト
        consent_type: 同意種別（指定時はその種別のみ）
        current_user: 現在のユーザー情報
        db: データベース接続
        
    Returns:
        List[ConsentResponse]: 同意履歴
    """
    try:
        user_id = current_user["id"]
        
        # クライアント情報の取得
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 同意履歴の取得
        query = """
        SELECT 
            consent_type,
            consent_version,
            consented,
            consent_date,
            withdrawn_at
        FROM user_consents 
        WHERE user_id = %s
        """
        params = [user_id]
        
        if consent_type:
            query += " AND consent_type = %s"
            params.append(consent_type)
        
        query += " ORDER BY consent_date DESC"
        
        cursor = await db.execute(query, params)
        consent_records = await cursor.fetchall()
        
        # 監査ログの記録
        await log_user_data_read(
            db_connection=db,
            user_id=user_id,
            target_user_id=user_id,
            accessed_fields=["consent_history"],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # レスポンスの構築
        consent_history = []
        for record in consent_records:
            consent_history.append(ConsentResponse(
                consent_type=record["consent_type"],
                consent_version=record["consent_version"],
                consented=record["consented"],
                consent_date=record["consent_date"].isoformat() if record["consent_date"] else None,
                withdrawn_at=record["withdrawn_at"].isoformat() if record["withdrawn_at"] else None
            ))
        
        return consent_history
        
    except Exception as e:
        logger.error(f"同意履歴取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同意履歴の取得に失敗しました: {str(e)}"
        )


@router.post("/data/export", response_model=Dict[str, Any])
async def export_user_data(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    ユーザーデータのエクスポート（データポータビリティ対応）
    
    Args:
        request: HTTPリクエスト
        current_user: 現在のユーザー情報
        db: データベース接続
        
    Returns:
        Dict[str, Any]: エクスポートされたユーザーデータ
    """
    try:
        user_id = current_user["id"]
        
        # クライアント情報の取得
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # データ保護サービスの初期化
        data_protection_service = DataProtectionService(db)
        
        # ユーザーデータのエクスポート
        export_data = await data_protection_service.export_user_data(
            user_id=user_id,
            requesting_user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"ユーザーデータをエクスポートしました (user_id: {user_id})")
        
        return export_data
        
    except Exception as e:
        logger.error(f"データエクスポートエラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"データエクスポートに失敗しました: {str(e)}"
        )


@router.post("/data/deletion-request", response_model=Dict[str, str])
async def request_data_deletion(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db_connection)
):
    """
    データ削除リクエストの作成（忘れられる権利対応）
    
    Args:
        request: HTTPリクエスト
        current_user: 現在のユーザー情報
        db: データベース接続
        
    Returns:
        Dict[str, str]: 削除リクエスト結果
    """
    try:
        user_id = current_user["id"]
        
        # データ保護サービスの初期化
        data_protection_service = DataProtectionService(db)
        
        # データ削除リクエストの作成
        success = await data_protection_service.request_data_deletion(
            user_id=user_id,
            reason="ユーザーからの削除要求（忘れられる権利の行使）"
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="データ削除リクエストの作成に失敗しました"
            )
        
        logger.info(f"データ削除リクエストを作成しました (user_id: {user_id})")
        
        return {
            "message": "データ削除リクエストを受け付けました。処理完了まで最大30日かかる場合があります。",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"データ削除リクエストエラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"データ削除リクエストの作成に失敗しました: {str(e)}"
        )