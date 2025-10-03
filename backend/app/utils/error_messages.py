"""
日本語エラーメッセージ定義

アプリケーション全体で使用される日本語エラーメッセージを定義する。
一貫性のあるユーザー体験を提供するため、エラーメッセージを集約管理する。
"""
from typing import Dict, Any

# 認証関連エラーメッセージ
AUTH_ERROR_MESSAGES = {
    "INVALID_CREDENTIALS": "メールアドレスまたはパスワードが正しくありません",
    "TOKEN_EXPIRED": "認証トークンの有効期限が切れています。再度ログインしてください",
    "TOKEN_INVALID": "認証トークンが無効です",
    "TOKEN_MISSING": "認証トークンが提供されていません",
    "UNAUTHORIZED": "この操作を実行する権限がありません",
    "FORBIDDEN": "アクセスが拒否されました",
    "USER_NOT_FOUND": "指定されたユーザーが見つかりません",
    "USER_ALREADY_EXISTS": "このメールアドレスは既に使用されています",
    "USERNAME_ALREADY_EXISTS": "このユーザー名は既に使用されています",
    "COGNITO_USER_NOT_FOUND": "Cognito ユーザーが見つかりません",
    "COGNITO_CONNECTION_ERROR": "認証サービスへの接続に失敗しました",
    "PASSWORD_TOO_WEAK": "パスワードが弱すぎます。8文字以上で英数字を含めてください",
    "EMAIL_NOT_VERIFIED": "メールアドレスが確認されていません",
    "ACCOUNT_DISABLED": "アカウントが無効化されています",
}

# データベース関連エラーメッセージ
DATABASE_ERROR_MESSAGES = {
    "CONNECTION_FAILED": "データベースへの接続に失敗しました",
    "QUERY_FAILED": "データベースクエリの実行に失敗しました",
    "TRANSACTION_FAILED": "データベーストランザクションに失敗しました",
    "CONSTRAINT_VIOLATION": "データの整合性制約に違反しています",
    "DUPLICATE_KEY": "重複するデータが存在します",
    "FOREIGN_KEY_VIOLATION": "関連するデータが見つかりません",
    "DATA_TOO_LONG": "入力データが長すぎます",
    "INVALID_DATA_TYPE": "データ型が正しくありません",
    "RECORD_NOT_FOUND": "指定されたレコードが見つかりません",
    "RECORD_LOCKED": "レコードが他の処理でロックされています",
}

# バリデーション関連エラーメッセージ
VALIDATION_ERROR_MESSAGES = {
    "REQUIRED_FIELD": "必須項目です",
    "INVALID_EMAIL": "有効なメールアドレスを入力してください",
    "INVALID_FORMAT": "入力形式が正しくありません",
    "VALUE_TOO_SHORT": "値が短すぎます",
    "VALUE_TOO_LONG": "値が長すぎます",
    "INVALID_RANGE": "値が許可された範囲外です",
    "INVALID_CHARACTERS": "使用できない文字が含まれています",
    "INVALID_JSON": "JSON 形式が正しくありません",
    "MISSING_PARAMETER": "必要なパラメータが不足しています",
    "INVALID_PARAMETER": "パラメータの値が無効です",
}

# システム関連エラーメッセージ
SYSTEM_ERROR_MESSAGES = {
    "INTERNAL_ERROR": "内部エラーが発生しました。しばらく時間をおいて再度お試しください",
    "SERVICE_UNAVAILABLE": "サービスが一時的に利用できません",
    "TIMEOUT": "処理がタイムアウトしました",
    "RATE_LIMIT_EXCEEDED": "リクエスト制限を超えました。しばらく時間をおいて再度お試しください",
    "MAINTENANCE_MODE": "システムメンテナンス中です",
    "FEATURE_DISABLED": "この機能は現在無効化されています",
    "EXTERNAL_SERVICE_ERROR": "外部サービスでエラーが発生しました",
    "CONFIGURATION_ERROR": "システム設定エラーが発生しました",
    "RESOURCE_EXHAUSTED": "システムリソースが不足しています",
    "NETWORK_ERROR": "ネットワークエラーが発生しました",
}

# ファイル・アップロード関連エラーメッセージ
FILE_ERROR_MESSAGES = {
    "FILE_TOO_LARGE": "ファイルサイズが大きすぎます",
    "INVALID_FILE_TYPE": "サポートされていないファイル形式です",
    "FILE_NOT_FOUND": "ファイルが見つかりません",
    "UPLOAD_FAILED": "ファイルのアップロードに失敗しました",
    "STORAGE_FULL": "ストレージ容量が不足しています",
    "FILE_CORRUPTED": "ファイルが破損しています",
}

# 全エラーメッセージを統合
ALL_ERROR_MESSAGES = {
    **AUTH_ERROR_MESSAGES,
    **DATABASE_ERROR_MESSAGES,
    **VALIDATION_ERROR_MESSAGES,
    **SYSTEM_ERROR_MESSAGES,
    **FILE_ERROR_MESSAGES,
}


def get_error_message(error_code: str, default_message: str = None) -> str:
    """
    エラーコードに対応する日本語エラーメッセージを取得する
    
    Args:
        error_code (str): エラーコード
        default_message (str, optional): デフォルトメッセージ
        
    Returns:
        str: 日本語エラーメッセージ
    """
    return ALL_ERROR_MESSAGES.get(
        error_code, 
        default_message or "予期しないエラーが発生しました"
    )


def format_validation_error(field_name: str, error_type: str, **kwargs) -> str:
    """
    バリデーションエラーメッセージをフォーマットする
    
    Args:
        field_name (str): フィールド名
        error_type (str): エラータイプ
        **kwargs: 追加パラメータ
        
    Returns:
        str: フォーマットされたエラーメッセージ
    """
    base_message = VALIDATION_ERROR_MESSAGES.get(error_type, "入力エラーが発生しました")
    
    # フィールド名を日本語に変換
    field_names_jp = {
        "email": "メールアドレス",
        "username": "ユーザー名",
        "password": "パスワード",
        "first_name": "名前",
        "last_name": "姓",
        "bio": "自己紹介",
        "avatar_url": "アバター画像URL",
    }
    
    field_name_jp = field_names_jp.get(field_name, field_name)
    
    # 特定のエラータイプに対する詳細メッセージ
    if error_type == "VALUE_TOO_SHORT" and "min_length" in kwargs:
        return f"{field_name_jp}は{kwargs['min_length']}文字以上で入力してください"
    elif error_type == "VALUE_TOO_LONG" and "max_length" in kwargs:
        return f"{field_name_jp}は{kwargs['max_length']}文字以下で入力してください"
    elif error_type == "REQUIRED_FIELD":
        return f"{field_name_jp}は必須項目です"
    
    return f"{field_name_jp}: {base_message}"


def create_error_response(error_code: str, message: str = None, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    統一されたエラーレスポンス形式を作成する
    
    Args:
        error_code (str): エラーコード
        message (str, optional): カスタムメッセージ
        details (Dict[str, Any], optional): エラー詳細情報
        
    Returns:
        Dict[str, Any]: エラーレスポンス
    """
    return {
        "error_code": error_code,
        "message": message or get_error_message(error_code),
        "details": details or {}
    }