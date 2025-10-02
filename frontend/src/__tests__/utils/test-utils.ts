/**
 * テストユーティリティ
 * Test utilities
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// テスト用のQueryClientを作成 / Create QueryClient for testing
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });

// テスト用のプロバイダーラッパー / Test provider wrapper
interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  const queryClient = createTestQueryClient();
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
};

// カスタムレンダー関数 / Custom render function
const customRender = (ui: React.ReactElement, options?: Omit<RenderOptions, "wrapper">) => render(ui, { wrapper: AllTheProviders, ...options });

// テスト用のモックユーザーデータ / Mock user data for testing
export const mockUser = {
  id: 1,
  cognitoUserId: "test-cognito-id-123",
  email: "test@example.com",
  username: "testuser",
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
};

// テスト用のモック認証状態 / Mock auth state for testing
export const mockAuthState = {
  user: mockUser,
  isAuthenticated: true,
  isLoading: false,
  error: null,
};

// APIレスポンスのモック / Mock API responses
export const mockApiResponse = {
  success: function <T>(data: T) {
    return {
      status: "success" as const,
      data,
      message: "Success",
    };
  },
  error: (errorCode: string, message: string) => ({
    status: "error" as const,
    error_code: errorCode,
    message,
  }),
};

// ローディング状態のモック / Mock loading state
export const mockLoadingState = {
  isLoading: true,
  isError: false,
  error: null,
  data: undefined,
};

// エラー状態のモック / Mock error state
export const mockErrorState = {
  isLoading: false,
  isError: true,
  error: new Error("Test error"),
  data: undefined,
};

// フォームイベントのモック / Mock form events
export const mockFormEvent = (formData: Record<string, string> = {}) => ({
  preventDefault: jest.fn(),
  target: {
    elements: Object.entries(formData).reduce((acc, [name, value]) => {
      acc[name] = { name, value };
      return acc;
    }, {} as any),
  },
});

// 入力変更イベントのモック / Mock input change events
export const mockInputChangeEvent = (name: string, value: string) => ({
  target: { name, value },
  preventDefault: jest.fn(),
  stopPropagation: jest.fn(),
});

// ファイル選択イベントのモック / Mock file selection events
export const mockFileChangeEvent = (files: File[]) => ({
  target: { files },
  preventDefault: jest.fn(),
  stopPropagation: jest.fn(),
});

// テスト用のファイルオブジェクト作成 / Create test file object
export const createMockFile = (name: string = "test.jpg", size: number = 1024, type: string = "image/jpeg"): File => {
  const file = new File(["test content"], name, { type });
  Object.defineProperty(file, "size", { value: size });
  return file;
};

// 非同期処理の待機ユーティリティ / Async wait utility
export const waitForTimeout = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// テスト用のローカルストレージモック / Mock localStorage for testing
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// テスト用のfetchモック / Mock fetch for testing
export const mockFetch = (response: any, ok: boolean = true) => {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    status: ok ? 200 : 400,
    json: jest.fn().mockResolvedValue(response),
    text: jest.fn().mockResolvedValue(JSON.stringify(response)),
  });
};

// APIエラーのモック / Mock API errors
export const mockApiError = (statusCode: number, errorCode: string, message: string) => {
  const error = new Error(message) as any;
  error.response = {
    status: statusCode,
    data: {
      error_code: errorCode,
      message,
    },
  };
  return error;
};

// React Query のテストヘルパー / React Query test helpers
export const createWrapper = () => {
  const queryClient = createTestQueryClient();
  return ({ children }: { children: React.ReactNode }) => React.createElement(QueryClientProvider, { client: queryClient }, children);
};

// すべてのエクスポートを再エクスポート / Re-export everything
export * from "@testing-library/react";
export { customRender as render };
