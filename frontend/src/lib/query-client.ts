import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./api-client";

// QueryClientの設定
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // デフォルトのstaleTime（データが古いと判断される時間）
      staleTime: 5 * 60 * 1000, // 5分
      // デフォルトのcacheTime（キャッシュ保持時間）
      gcTime: 10 * 60 * 1000, // 10分
      // エラー時のリトライ設定
      retry: (failureCount, error) => {
        // ApiErrorの場合、4xx系エラーはリトライしない
        if (error instanceof ApiError && error.statusCode >= 400 && error.statusCode < 500) {
          return false;
        }
        // 最大3回までリトライ
        return failureCount < 3;
      },
      // リトライ間隔
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      // ミューテーション失敗時のリトライ設定
      retry: (failureCount, error) => {
        // ApiErrorの場合、4xx系エラーはリトライしない
        if (error instanceof ApiError && error.statusCode >= 400 && error.statusCode < 500) {
          return false;
        }
        // 最大1回までリトライ
        return failureCount < 1;
      },
    },
  },
});

// クエリキーファクトリー
export const queryKeys = {
  // 認証関連
  auth: {
    user: () => ["auth", "user"] as const,
    profile: () => ["auth", "profile"] as const,
  },

  // ユーザー関連
  users: {
    all: () => ["users"] as const,
    lists: () => [...queryKeys.users.all(), "list"] as const,
    list: (filters: Record<string, any>) => [...queryKeys.users.lists(), filters] as const,
    details: () => [...queryKeys.users.all(), "detail"] as const,
    detail: (id: number) => [...queryKeys.users.details(), id] as const,
  },

  // ヘルスチェック関連
  health: {
    all: () => ["health"] as const,
    basic: () => [...queryKeys.health.all(), "basic"] as const,
    detailed: () => [...queryKeys.health.all(), "detailed"] as const,
    database: () => [...queryKeys.health.all(), "database"] as const,
  },
} as const;

// エラーハンドリング用のヘルパー
export const handleQueryError = (error: unknown): string => {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unknown error occurred";
};
