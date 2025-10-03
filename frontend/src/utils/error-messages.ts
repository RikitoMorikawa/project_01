/**
 * 日本語エラーメッセージ定義
 *
 * フロントエンドアプリケーション全体で使用される日本語エラーメッセージを定義する。
 * 一貫性のあるユーザー体験を提供するため、エラーメッセージを集約管理する。
 */

/**
 * 認証関連エラーメッセージ
 */
export const AUTH_ERROR_MESSAGES = {
  INVALID_CREDENTIALS: "メールアドレスまたはパスワードが正しくありません",
  TOKEN_EXPIRED: "セッションの有効期限が切れました。再度ログインしてください",
  TOKEN_INVALID: "認証情報が無効です。再度ログインしてください",
  UNAUTHORIZED: "この操作を実行する権限がありません",
  FORBIDDEN: "アクセスが拒否されました",
  USER_NOT_FOUND: "ユーザーが見つかりません",
  EMAIL_ALREADY_EXISTS: "このメールアドレスは既に使用されています",
  USERNAME_ALREADY_EXISTS: "このユーザー名は既に使用されています",
  PASSWORD_TOO_WEAK: "パスワードが弱すぎます。8文字以上で英数字を含めてください",
  EMAIL_NOT_VERIFIED: "メールアドレスが確認されていません。確認メールをご確認ください",
  ACCOUNT_DISABLED: "アカウントが無効化されています。管理者にお問い合わせください",
  LOGIN_FAILED: "ログインに失敗しました",
  LOGOUT_FAILED: "ログアウトに失敗しました",
  SIGNUP_FAILED: "アカウント作成に失敗しました",
  PASSWORD_RESET_FAILED: "パスワードリセットに失敗しました",
} as const;

/**
 * バリデーション関連エラーメッセージ
 */
export const VALIDATION_ERROR_MESSAGES = {
  REQUIRED_FIELD: "この項目は必須です",
  INVALID_EMAIL: "有効なメールアドレスを入力してください",
  INVALID_FORMAT: "入力形式が正しくありません",
  VALUE_TOO_SHORT: "入力値が短すぎます",
  VALUE_TOO_LONG: "入力値が長すぎます",
  INVALID_RANGE: "値が許可された範囲外です",
  INVALID_CHARACTERS: "使用できない文字が含まれています",
  PASSWORD_MISMATCH: "パスワードが一致しません",
  WEAK_PASSWORD: "パスワードは8文字以上で、英数字を含む必要があります",
  INVALID_USERNAME: "ユーザー名は3文字以上で入力してください",
  INVALID_PHONE: "有効な電話番号を入力してください",
  INVALID_URL: "有効なURLを入力してください",
} as const;

/**
 * ネットワーク関連エラーメッセージ
 */
export const NETWORK_ERROR_MESSAGES = {
  NETWORK_ERROR: "ネットワークエラーが発生しました。インターネット接続を確認してください",
  TIMEOUT: "リクエストがタイムアウトしました。しばらく時間をおいて再度お試しください",
  SERVER_ERROR: "サーバーエラーが発生しました。しばらく時間をおいて再度お試しください",
  SERVICE_UNAVAILABLE: "サービスが一時的に利用できません",
  RATE_LIMIT_EXCEEDED: "リクエスト制限を超えました。しばらく時間をおいて再度お試しください",
  BAD_REQUEST: "リクエストが正しくありません",
  NOT_FOUND: "要求されたリソースが見つかりません",
  CONFLICT: "データの競合が発生しました",
  MAINTENANCE_MODE: "システムメンテナンス中です",
} as const;

/**
 * ファイル関連エラーメッセージ
 */
export const FILE_ERROR_MESSAGES = {
  FILE_TOO_LARGE: "ファイルサイズが大きすぎます",
  INVALID_FILE_TYPE: "サポートされていないファイル形式です",
  FILE_NOT_FOUND: "ファイルが見つかりません",
  UPLOAD_FAILED: "ファイルのアップロードに失敗しました",
  DOWNLOAD_FAILED: "ファイルのダウンロードに失敗しました",
  FILE_CORRUPTED: "ファイルが破損しています",
  STORAGE_FULL: "ストレージ容量が不足しています",
} as const;

/**
 * UI関連エラーメッセージ
 */
export const UI_ERROR_MESSAGES = {
  LOADING_FAILED: "データの読み込みに失敗しました",
  SAVE_FAILED: "データの保存に失敗しました",
  DELETE_FAILED: "データの削除に失敗しました",
  UPDATE_FAILED: "データの更新に失敗しました",
  OPERATION_CANCELLED: "操作がキャンセルされました",
  UNSUPPORTED_BROWSER: "お使いのブラウザはサポートされていません",
  JAVASCRIPT_DISABLED: "JavaScriptが無効になっています。有効にしてください",
  COOKIES_DISABLED: "Cookieが無効になっています。有効にしてください",
} as const;

/**
 * 全エラーメッセージを統合
 */
export const ALL_ERROR_MESSAGES = {
  ...AUTH_ERROR_MESSAGES,
  ...VALIDATION_ERROR_MESSAGES,
  ...NETWORK_ERROR_MESSAGES,
  ...FILE_ERROR_MESSAGES,
  ...UI_ERROR_MESSAGES,
} as const;

/**
 * エラーコードタイプ
 */
export type ErrorCode = keyof typeof ALL_ERROR_MESSAGES;

/**
 * エラーコードに対応する日本語エラーメッセージを取得する
 *
 * @param errorCode エラーコード
 * @param defaultMessage デフォルトメッセージ
 * @returns 日本語エラーメッセージ
 */
export function getErrorMessage(errorCode: string, defaultMessage?: string): string {
  return ALL_ERROR_MESSAGES[errorCode as ErrorCode] || defaultMessage || "予期しないエラーが発生しました";
}

/**
 * HTTPステータスコードに基づいてエラーメッセージを取得する
 *
 * @param statusCode HTTPステータスコード
 * @returns 日本語エラーメッセージ
 */
export function getErrorMessageByStatus(statusCode: number): string {
  switch (statusCode) {
    case 400:
      return NETWORK_ERROR_MESSAGES.BAD_REQUEST;
    case 401:
      return AUTH_ERROR_MESSAGES.UNAUTHORIZED;
    case 403:
      return AUTH_ERROR_MESSAGES.FORBIDDEN;
    case 404:
      return NETWORK_ERROR_MESSAGES.NOT_FOUND;
    case 409:
      return NETWORK_ERROR_MESSAGES.CONFLICT;
    case 429:
      return NETWORK_ERROR_MESSAGES.RATE_LIMIT_EXCEEDED;
    case 500:
      return NETWORK_ERROR_MESSAGES.SERVER_ERROR;
    case 502:
    case 503:
      return NETWORK_ERROR_MESSAGES.SERVICE_UNAVAILABLE;
    case 504:
      return NETWORK_ERROR_MESSAGES.TIMEOUT;
    default:
      return "予期しないエラーが発生しました";
  }
}

/**
 * バリデーションエラーメッセージをフォーマットする
 *
 * @param fieldName フィールド名
 * @param errorType エラータイプ
 * @param options 追加オプション
 * @returns フォーマットされたエラーメッセージ
 */
export function formatValidationError(
  fieldName: string,
  errorType: keyof typeof VALIDATION_ERROR_MESSAGES,
  options?: { minLength?: number; maxLength?: number; pattern?: string }
): string {
  const baseMessage = VALIDATION_ERROR_MESSAGES[errorType];

  // フィールド名を日本語に変換
  const fieldNamesJp: Record<string, string> = {
    email: "メールアドレス",
    username: "ユーザー名",
    password: "パスワード",
    confirmPassword: "パスワード確認",
    firstName: "名前",
    lastName: "姓",
    bio: "自己紹介",
    avatarUrl: "アバター画像URL",
    phone: "電話番号",
    website: "ウェブサイト",
  };

  const fieldNameJp = fieldNamesJp[fieldName] || fieldName;

  // 特定のエラータイプに対する詳細メッセージ
  switch (errorType) {
    case "VALUE_TOO_SHORT":
      if (options?.minLength) {
        return `${fieldNameJp}は${options.minLength}文字以上で入力してください`;
      }
      break;
    case "VALUE_TOO_LONG":
      if (options?.maxLength) {
        return `${fieldNameJp}は${options.maxLength}文字以下で入力してください`;
      }
      break;
    case "REQUIRED_FIELD":
      return `${fieldNameJp}は必須項目です`;
    case "INVALID_EMAIL":
      return `有効な${fieldNameJp}を入力してください`;
  }

  return `${fieldNameJp}: ${baseMessage}`;
}

/**
 * エラー詳細情報の型定義
 */
export interface ErrorDetails {
  field?: string;
  code?: string;
  message?: string;
  [key: string]: any;
}

/**
 * 統一されたエラーレスポンス形式
 */
export interface ErrorResponse {
  errorCode: string;
  message: string;
  details?: ErrorDetails;
  timestamp?: string;
}

/**
 * 統一されたエラーレスポンスを作成する
 *
 * @param errorCode エラーコード
 * @param message カスタムメッセージ
 * @param details エラー詳細情報
 * @returns エラーレスポンス
 */
export function createErrorResponse(errorCode: string, message?: string, details?: ErrorDetails): ErrorResponse {
  return {
    errorCode,
    message: message || getErrorMessage(errorCode),
    details,
    timestamp: new Date().toISOString(),
  };
}

/**
 * フィールド別バリデーションエラーメッセージ
 */
export const FIELD_VALIDATION_MESSAGES = {
  email: {
    required: "メールアドレスを入力してください",
    invalid: "有効なメールアドレスを入力してください",
    exists: "このメールアドレスは既に使用されています",
  },
  username: {
    required: "ユーザー名を入力してください",
    tooShort: "ユーザー名は3文字以上で入力してください",
    tooLong: "ユーザー名は50文字以下で入力してください",
    invalid: "ユーザー名に使用できない文字が含まれています",
    exists: "このユーザー名は既に使用されています",
  },
  password: {
    required: "パスワードを入力してください",
    tooShort: "パスワードは8文字以上で入力してください",
    weak: "パスワードは英数字を含む8文字以上で入力してください",
    mismatch: "パスワードが一致しません",
  },
  confirmPassword: {
    required: "パスワード確認を入力してください",
    mismatch: "パスワードが一致しません",
  },
} as const;
