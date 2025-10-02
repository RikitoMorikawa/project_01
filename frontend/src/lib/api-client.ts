import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";

// API設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// APIクライアントクラス
class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // リクエストインターセプター
    this.client.interceptors.request.use(
      (config) => {
        // 認証トークンを自動で追加
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // リクエストログ
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);

        return config;
      },
      (error) => {
        console.error("Request interceptor error:", error);
        return Promise.reject(error);
      }
    );

    // レスポンスインターセプター
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error("API Error:", error.response?.status, error.response?.data);

        // 401エラーの場合は認証エラーとして処理
        if (error.response?.status === 401) {
          this.handleAuthError();
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  // 認証トークンを取得
  private getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("auth_token");
  }

  // 認証エラーハンドリング
  private handleAuthError(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      // ログインページにリダイレクト
      window.location.href = "/login";
    }
  }

  // エラーフォーマット
  private formatError(error: any): ApiError {
    const response = error.response;

    return new ApiError(
      response?.data?.error_code || "UNKNOWN_ERROR",
      response?.data?.message || error.message || "An unknown error occurred",
      response?.status || 500,
      response?.data?.details
    );
  }

  // GET リクエスト
  async get<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(endpoint, config);
    return response.data;
  }

  // POST リクエスト
  async post<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(endpoint, data, config);
    return response.data;
  }

  // PUT リクエスト
  async put<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(endpoint, data, config);
    return response.data;
  }

  // DELETE リクエスト
  async delete<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(endpoint, config);
    return response.data;
  }

  // PATCH リクエスト
  async patch<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(endpoint, data, config);
    return response.data;
  }

  // 認証トークンを設定
  setAuthToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  // 認証トークンを削除
  clearAuthToken(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }
}

// カスタムエラークラス
export class ApiError extends Error {
  constructor(public errorCode: string, public message: string, public statusCode: number, public details?: any) {
    super(message);
    this.name = "ApiError";
  }
}

// APIクライアントのシングルトンインスタンス
export const apiClient = new ApiClient();

// 型定義
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: "success" | "error";
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RequestConfig {
  headers?: Record<string, string>;
  timeout?: number;
}

export default apiClient;
