/**
 * 日本語ログメッセージ定義
 *
 * フロントエンドアプリケーション全体で使用される日本語ログメッセージを定義する。
 * 開発者向けの詳細なログ情報を日本語で提供し、デバッグとモニタリングを支援する。
 */

/**
 * ログレベル
 */
export enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARN = "WARN",
  ERROR = "ERROR",
}

/**
 * ログレベルの日本語表記
 */
export const LOG_LEVELS_JP = {
  [LogLevel.DEBUG]: "デバッグ",
  [LogLevel.INFO]: "情報",
  [LogLevel.WARN]: "警告",
  [LogLevel.ERROR]: "エラー",
} as const;

/**
 * 認証関連ログメッセージ
 */
export const AUTH_LOG_MESSAGES = {
  LOGIN_ATTEMPT: "ログイン試行: {email}",
  LOGIN_SUCCESS: "ログイン成功: ユーザー {username}",
  LOGIN_FAILED: "ログイン失敗: {email} - 理由: {reason}",
  LOGOUT_SUCCESS: "ログアウト成功: ユーザー {username}",
  LOGOUT_FAILED: "ログアウト失敗: {reason}",
  TOKEN_REFRESH: "トークンリフレッシュ実行",
  TOKEN_REFRESH_SUCCESS: "トークンリフレッシュ成功",
  TOKEN_REFRESH_FAILED: "トークンリフレッシュ失敗: {reason}",
  SESSION_EXPIRED: "セッション期限切れ検出",
  AUTO_LOGOUT: "自動ログアウト実行: 理由 {reason}",
  PASSWORD_RESET_REQUEST: "パスワードリセット要求: {email}",
  PASSWORD_RESET_SUCCESS: "パスワードリセット成功",
  SIGNUP_ATTEMPT: "アカウント作成試行: {email}",
  SIGNUP_SUCCESS: "アカウント作成成功: {email}",
  SIGNUP_FAILED: "アカウント作成失敗: {email} - 理由: {reason}",
} as const;

/**
 * API関連ログメッセージ
 */
export const API_LOG_MESSAGES = {
  REQUEST_START: "API リクエスト開始: {method} {url}",
  REQUEST_SUCCESS: "API リクエスト成功: {method} {url} - ステータス: {status} - 時間: {duration}ms",
  REQUEST_FAILED: "API リクエスト失敗: {method} {url} - エラー: {error}",
  REQUEST_TIMEOUT: "API リクエストタイムアウト: {method} {url}",
  REQUEST_CANCELLED: "API リクエストキャンセル: {method} {url}",
  RETRY_ATTEMPT: "API リクエスト再試行: {method} {url} - 試行回数: {attempt}",
  CACHE_HIT: "API キャッシュヒット: {key}",
  CACHE_MISS: "API キャッシュミス: {key}",
  CACHE_SET: "API キャッシュ設定: {key}",
  CACHE_CLEAR: "API キャッシュクリア: {pattern}",
} as const;

/**
 * UI関連ログメッセージ
 */
export const UI_LOG_MESSAGES = {
  PAGE_LOAD: "ページ読み込み: {path}",
  PAGE_LOAD_SUCCESS: "ページ読み込み成功: {path} - 時間: {duration}ms",
  PAGE_LOAD_FAILED: "ページ読み込み失敗: {path} - エラー: {error}",
  COMPONENT_MOUNT: "コンポーネントマウント: {component}",
  COMPONENT_UNMOUNT: "コンポーネントアンマウント: {component}",
  COMPONENT_ERROR: "コンポーネントエラー: {component} - エラー: {error}",
  FORM_SUBMIT: "フォーム送信: {form}",
  FORM_VALIDATION_ERROR: "フォームバリデーションエラー: {form} - フィールド: {field}",
  BUTTON_CLICK: "ボタンクリック: {button}",
  NAVIGATION: "ナビゲーション: {from} → {to}",
  MODAL_OPEN: "モーダル表示: {modal}",
  MODAL_CLOSE: "モーダル非表示: {modal}",
  NOTIFICATION_SHOW: "通知表示: {type} - {message}",
} as const;

/**
 * パフォーマンス関連ログメッセージ
 */
export const PERFORMANCE_LOG_MESSAGES = {
  SLOW_RENDER: "遅いレンダリング検出: コンポーネント {component} - 時間: {duration}ms",
  SLOW_API_CALL: "遅い API 呼び出し検出: {method} {url} - 時間: {duration}ms",
  MEMORY_WARNING: "メモリ使用量警告: {usage}MB",
  BUNDLE_SIZE_WARNING: "バンドルサイズ警告: {size}KB",
  LARGE_LIST_RENDER: "大きなリスト描画: 要素数 {count}",
  IMAGE_LOAD_SLOW: "画像読み込み遅延: {url} - 時間: {duration}ms",
  SCRIPT_LOAD_FAILED: "スクリプト読み込み失敗: {script}",
} as const;

/**
 * エラー関連ログメッセージ
 */
export const ERROR_LOG_MESSAGES = {
  JAVASCRIPT_ERROR: "JavaScript エラー: {message} - ファイル: {filename}:{line}",
  UNHANDLED_PROMISE_REJECTION: "未処理の Promise 拒否: {reason}",
  NETWORK_ERROR: "ネットワークエラー: {message}",
  CORS_ERROR: "CORS エラー: {origin}",
  VALIDATION_ERROR: "バリデーションエラー: {field} - {message}",
  STORAGE_ERROR: "ストレージエラー: {operation} - {error}",
  PERMISSION_ERROR: "権限エラー: {permission}",
  BROWSER_COMPATIBILITY_ERROR: "ブラウザ互換性エラー: {feature}",
} as const;

/**
 * 全ログメッセージを統合
 */
export const ALL_LOG_MESSAGES = {
  ...AUTH_LOG_MESSAGES,
  ...API_LOG_MESSAGES,
  ...UI_LOG_MESSAGES,
  ...PERFORMANCE_LOG_MESSAGES,
  ...ERROR_LOG_MESSAGES,
} as const;

/**
 * ログメッセージキーの型
 */
export type LogMessageKey = keyof typeof ALL_LOG_MESSAGES;

/**
 * ログコンテキスト情報
 */
export interface LogContext {
  userId?: string;
  sessionId?: string;
  userAgent?: string;
  url?: string;
  timestamp?: string;
  [key: string]: any;
}

/**
 * 日本語ロガークラス
 */
export class JapaneseLogger {
  private context: LogContext = {};

  constructor(private name: string) {
    // 基本コンテキスト情報を設定
    this.context = {
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
  }

  /**
   * コンテキスト情報を設定する
   *
   * @param context コンテキスト情報
   */
  setContext(context: Partial<LogContext>): void {
    this.context = { ...this.context, ...context };
  }

  /**
   * メッセージテンプレートをフォーマットする
   *
   * @param messageKey メッセージキー
   * @param params フォーマット用パラメータ
   * @returns フォーマットされたメッセージ
   */
  private formatMessage(messageKey: LogMessageKey, params: Record<string, any> = {}): string {
    const template = ALL_LOG_MESSAGES[messageKey] || messageKey;

    try {
      return template.replace(/\{(\w+)\}/g, (match, key) => {
        return params[key]?.toString() || match;
      });
    } catch (error) {
      return `${template} (フォーマットエラー: ${error})`;
    }
  }

  /**
   * ログを出力する
   *
   * @param level ログレベル
   * @param messageKey メッセージキー
   * @param params パラメータ
   * @param additionalContext 追加コンテキスト
   */
  private log(level: LogLevel, messageKey: LogMessageKey, params: Record<string, any> = {}, additionalContext: Record<string, any> = {}): void {
    const message = this.formatMessage(messageKey, params);
    const timestamp = new Date().toISOString();

    const logData = {
      level,
      levelJp: LOG_LEVELS_JP[level],
      logger: this.name,
      message,
      messageKey,
      timestamp,
      context: { ...this.context, ...additionalContext },
      params,
    };

    // 開発環境では詳細ログを出力
    if (process.env.NODE_ENV === "development") {
      const consoleMethod = level === LogLevel.ERROR ? "error" : level === LogLevel.WARN ? "warn" : level === LogLevel.DEBUG ? "debug" : "log";

      console[consoleMethod](`[${LOG_LEVELS_JP[level]}] ${this.name}: ${message}`, logData);
    }

    // 本番環境では構造化ログとして送信（実装は環境に応じて）
    if (process.env.NODE_ENV === "production") {
      this.sendToLogService(logData);
    }
  }

  /**
   * ログサービスに送信する（本番環境用）
   *
   * @param logData ログデータ
   */
  private sendToLogService(logData: any): void {
    // 実際の実装では CloudWatch Logs や外部ログサービスに送信
    // 現在はローカルストレージに保存（デモ用）
    try {
      const logs = JSON.parse(localStorage.getItem("app_logs") || "[]");
      logs.push(logData);

      // 最新の100件のみ保持
      if (logs.length > 100) {
        logs.splice(0, logs.length - 100);
      }

      localStorage.setItem("app_logs", JSON.stringify(logs));
    } catch (error) {
      console.error("ログ保存エラー:", error);
    }
  }

  /**
   * デバッグログを出力
   */
  debug(messageKey: LogMessageKey, params?: Record<string, any>, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, messageKey, params, context);
  }

  /**
   * 情報ログを出力
   */
  info(messageKey: LogMessageKey, params?: Record<string, any>, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, messageKey, params, context);
  }

  /**
   * 警告ログを出力
   */
  warn(messageKey: LogMessageKey, params?: Record<string, any>, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, messageKey, params, context);
  }

  /**
   * エラーログを出力
   */
  error(messageKey: LogMessageKey, params?: Record<string, any>, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, messageKey, params, context);
  }
}

/**
 * ロガーインスタンスのキャッシュ
 */
const loggerCache = new Map<string, JapaneseLogger>();

/**
 * 日本語ロガーのインスタンスを取得する
 *
 * @param name ロガー名
 * @returns 日本語ロガーインスタンス
 */
export function getLogger(name: string): JapaneseLogger {
  if (!loggerCache.has(name)) {
    loggerCache.set(name, new JapaneseLogger(name));
  }
  return loggerCache.get(name)!;
}

/**
 * よく使用されるログ関数のショートカット
 */

/**
 * 認証成功ログ
 */
export function logAuthSuccess(username: string, method: string = "password"): void {
  const logger = getLogger("auth");
  logger.info("LOGIN_SUCCESS", { username, method });
}

/**
 * 認証失敗ログ
 */
export function logAuthFailure(email: string, reason: string): void {
  const logger = getLogger("auth");
  logger.warn("LOGIN_FAILED", { email, reason });
}

/**
 * API リクエストログ
 */
export function logApiRequest(method: string, url: string, duration?: number, status?: number): void {
  const logger = getLogger("api");
  if (duration !== undefined && status !== undefined) {
    logger.info("REQUEST_SUCCESS", { method, url, duration, status });
  } else {
    logger.info("REQUEST_START", { method, url });
  }
}

/**
 * API エラーログ
 */
export function logApiError(method: string, url: string, error: string): void {
  const logger = getLogger("api");
  logger.error("REQUEST_FAILED", { method, url, error });
}

/**
 * ページ読み込みログ
 */
export function logPageLoad(path: string, duration?: number): void {
  const logger = getLogger("ui");
  if (duration !== undefined) {
    logger.info("PAGE_LOAD_SUCCESS", { path, duration });
  } else {
    logger.info("PAGE_LOAD", { path });
  }
}

/**
 * エラーログ
 */
export function logError(messageKey: LogMessageKey, params?: Record<string, any>): void {
  const logger = getLogger("error");
  logger.error(messageKey, params);
}

/**
 * パフォーマンス警告ログ
 */
export function logPerformanceWarning(messageKey: LogMessageKey, params?: Record<string, any>): void {
  const logger = getLogger("performance");
  logger.warn(messageKey, params);
}

/**
 * グローバルエラーハンドラーを設定
 */
export function setupGlobalErrorHandling(): void {
  // JavaScript エラーをキャッチ
  window.addEventListener("error", (event) => {
    logError("JAVASCRIPT_ERROR", {
      message: event.message,
      filename: event.filename,
      line: event.lineno,
      column: event.colno,
    });
  });

  // 未処理の Promise 拒否をキャッチ
  window.addEventListener("unhandledrejection", (event) => {
    logError("UNHANDLED_PROMISE_REJECTION", {
      reason: event.reason?.toString() || "Unknown reason",
    });
  });
}
