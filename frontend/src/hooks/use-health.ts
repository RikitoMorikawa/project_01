import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-client";

// ヘルスチェックAPI関数
const healthApi = {
  // 基本ヘルスチェック
  getBasicHealth: async () => {
    const response = await apiClient.get<{
      status: string;
      message: string;
      version: string;
      environment: string;
      timestamp: string;
    }>("/api/v1/health");
    return response;
  },

  // 詳細ヘルスチェック
  getDetailedHealth: async () => {
    const response = await apiClient.get<{
      status: string;
      message: string;
      version: string;
      environment: string;
      timestamp: string;
      checks: {
        api: { status: string; message: string };
        database: { status: string; message: string };
        cognito: { status: string; message: string };
      };
      metrics: any;
    }>("/api/v1/health/detailed");
    return response;
  },

  // データベースヘルスチェック
  getDatabaseHealth: async () => {
    const response = await apiClient.get<{
      timestamp: string;
      database: {
        status: string;
        message: string;
        metrics?: any;
      };
    }>("/api/v1/health/database");
    return response;
  },

  // システムメトリクス取得
  getSystemMetrics: async () => {
    const response = await apiClient.get<{
      status: string;
      timestamp: string;
      metrics: {
        process: any;
        system: any;
        environment: any;
      };
    }>("/api/v1/health/metrics");
    return response;
  },
};

// 基本ヘルスチェックフック
export const useBasicHealth = (options?: { enabled?: boolean; refetchInterval?: number }) => {
  return useQuery({
    queryKey: queryKeys.health.basic(),
    queryFn: healthApi.getBasicHealth,
    staleTime: 30 * 1000, // 30秒
    refetchInterval: options?.refetchInterval || 60 * 1000, // 1分間隔で自動更新
    enabled: options?.enabled ?? true,
  });
};

// 詳細ヘルスチェックフック
export const useDetailedHealth = (options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: queryKeys.health.detailed(),
    queryFn: healthApi.getDetailedHealth,
    staleTime: 30 * 1000, // 30秒
    enabled: options?.enabled ?? false, // デフォルトでは無効（手動で有効化）
  });
};

// データベースヘルスチェックフック
export const useDatabaseHealth = (options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: queryKeys.health.database(),
    queryFn: healthApi.getDatabaseHealth,
    staleTime: 30 * 1000, // 30秒
    enabled: options?.enabled ?? false,
  });
};

// システムメトリクスフック
export const useSystemMetrics = (options?: { enabled?: boolean; refetchInterval?: number }) => {
  return useQuery({
    queryKey: [...queryKeys.health.all(), "metrics"],
    queryFn: healthApi.getSystemMetrics,
    staleTime: 30 * 1000, // 30秒
    refetchInterval: options?.refetchInterval || 5 * 60 * 1000, // 5分間隔
    enabled: options?.enabled ?? false,
  });
};
