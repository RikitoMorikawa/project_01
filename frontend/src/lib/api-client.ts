/**
 * API クライアント
 *
 * バックエンド API との通信を管理するクライアントクラス。
 * 認証トークンの自動付与、エラーハンドリング、リクエスト/レスポンスの
 * インターセプト機能を提供する。
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";

// API 設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/**
 * API クライアントクラス
 *
 * HTTP リクエストの送信、認証トークンの管理、エラーハンドリングを行う。
 * シングルトンパターンで実装され、アプリケーション全体で共有される。
 */
class ApiClient {
  private client: AxiosInstance;

  /**
   * ApiClient を初期化する
   *
   * Axios インスタンスを作成し、リクエスト/レスポンスインターセプターを設定する。
   */
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000, // 10秒でタイムアウト
      headers: {
        "Content-Type": "application/json",
      },
    });

    // リクエストインターセプター - 送信前の処理
    this.client.interceptors.request.use(
      (config) => {
        // 認証トークンを自動で追加
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // リクエストログ出力
        console.log(`API リクエスト: ${config.method?.toUpperCase()} ${config.url}`);

        return config;
      },
      (error) => {
        console.error("リクエストインターセプターエラー:", error);
        return Promise.reject(error);
      }
    );

    // レスポンスインターセプター - 受信後の処理
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`API レスポンス: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error("API エラー:", error.response?.status, error.response?.data);

        // 401エラーの場合は認証エラーとして処理
        if (error.response?.status === 401) {
          this.handleAuthError();
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  /**
   * 認証トークンを取得する
   *
   * ローカルストレージから認証トークンを取得する。
   * サーバーサイドレンダリング時は null を返す。
   *
   * @returns 認証トークンまたは null
   */
  private getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("auth_token");
  }

  /**
   * 認証エラーを処理する
   *
   * 401 エラー発生時にローカルストレージからトークンを削除し、
   * ログインページにリダイレクトする。
   */
  private handleAuthError(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      // ログインページにリダイレクト
      window.location.href = "/login";
    }
  }

  /**
   * エラーを統一フォーマットに変換する
   *
   * Axios エラーを ApiError クラスのインスタンスに変換し、
   * エラーコード、メッセージ、ステータスコードを統一する。
   *
   * @param error Axios エラーオブジェクト
   * @returns フォーマットされた ApiError
   */
  private formatError(error: any): ApiError {
    const response = error.response;

    // ネットワークエラーの場合
    if (!response) {
      return new ApiError("NETWORK_ERROR", "ネットワークエラーが発生しました。インターネット接続を確認してください", 0);
    }

    // サーバーからのエラーレスポンスがある場合
    const errorCode = response.data?.error_code || `HTTP_${response.status}`;
    let errorMessage = response.data?.message;

    // エラーメッセージが英語の場合は日本語に変換
    if (!errorMessage || !this.isJapanese(errorMessage)) {
      errorMessage = this.getJapaneseErrorMessage(response.status, errorCode);
    }

    return new ApiError(errorCode, errorMessage, response.status, response.data?.details);
  }

  /**
   * 文字列が日本語を含むかチェックする
   *
   * @param text チェックする文字列
   * @returns 日本語を含む場合は true
   */
  private isJapanese(text: string): boolean {
    return /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(text);
  }

  /**
   * ステータスコードとエラーコードに基づいて日本語エラーメッセージを取得する
   *
   * @param statusCode HTTPステータスコード
   * @param errorCode エラーコード
   * @returns 日本語エラーメッセージ
   */
  private getJapaneseErrorMessage(statusCode: number, errorCode: string): string {
    // 認証関連エラー
    if (statusCode === 401) {
      return "認証が必要です。ログインしてください";
    }
    if (statusCode === 403) {
      return "この操作を実行する権限がありません";
    }

    // クライアントエラー
    if (statusCode === 400) {
      return "リクエストが正しくありません";
    }
    if (statusCode === 404) {
      return "要求されたリソースが見つかりません";
    }
    if (statusCode === 409) {
      return "データの競合が発生しました";
    }
    if (statusCode === 422) {
      return "入力データに不正な値が含まれています";
    }
    if (statusCode === 429) {
      return "リクエスト制限を超えました。しばらく時間をおいて再度お試しください";
    }

    // サーバーエラー
    if (statusCode >= 500) {
      return "サーバーエラーが発生しました。しばらく時間をおいて再度お試しください";
    }

    return "予期しないエラーが発生しました";
  }

  /**
   * GET リクエストを送信する
   *
   * @param endpoint API エンドポイント
   * @param config リクエスト設定
   * @returns レスポンスデータ
   */
  async get<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(endpoint, config);
    return response.data;
  }

  /**
   * POST リクエストを送信する
   *
   * @param endpoint API エンドポイント
   * @param data リクエストボディ
   * @param config リクエスト設定
   * @returns レスポンスデータ
   */
  async post<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(endpoint, data, config);
    return response.data;
  }

  /**
   * PUT リクエストを送信する
   *
   * @param endpoint API エンドポイント
   * @param data リクエストボディ
   * @param config リクエスト設定
   * @returns レスポンスデータ
   */
  async put<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(endpoint, data, config);
    return response.data;
  }

  /**
   * DELETE リクエストを送信する
   *
   * @param endpoint API エンドポイント
   * @param config リクエスト設定
   * @returns レスポンスデータ
   */
  async delete<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(endpoint, config);
    return response.data;
  }

  /**
   * PATCH リクエストを送信する
   *
   * @param endpoint API エンドポイント
   * @param data リクエストボディ
   * @param config リクエスト設定
   * @returns レスポンスデータ
   */
  async patch<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(endpoint, data, config);
    return response.data;
  }

  /**
   * 認証トークンを設定する
   *
   * ローカルストレージに認証トークンを保存する。
   *
   * @param token 認証トークン
   */
  setAuthToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  /**
   * 認証トークンを削除する
   *
   * ローカルストレージから認証トークンを削除する。
   */
  clearAuthToken(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }
}

/**
 * API エラークラス
 *
 * API リクエストで発生したエラーを表現するカスタムエラークラス。
 * エラーコード、メッセージ、ステータスコード、詳細情報を含む。
 */
export class ApiError extends Error {
  constructor(public errorCode: string, public message: string, public statusCode: number, public details?: any) {
    super(message);
    this.name = "ApiError";
  }
}

// API クライアントのシングルトンインスタンス
export const apiClient = new ApiClient();

/**
 * API レスポンスの型定義
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: "success" | "error";
}

/**
 * ページネーション付きレスポンスの型定義
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * リクエスト設定の型定義
 */
export interface RequestConfig {
  headers?: Record<string, string>;
  timeout?: number;
}

export default apiClient;
