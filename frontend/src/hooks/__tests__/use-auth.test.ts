/**
 * useAuthフックの単体テスト
 * Unit tests for useAuth hook
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuth } from "../use-auth";
import { mockUser, mockAuthState, createWrapper } from "@/__tests__/utils/test-utils";
import React from "react";

// useAmplifyAuth フックのモック / Mock useAmplifyAuth hook
const mockAmplifyAuth = {
  signIn: jest.fn(),
  signOut: jest.fn(),
  signUp: jest.fn(),
  confirmSignUp: jest.fn(),
  resendConfirmationCode: jest.fn(),
  resetPassword: jest.fn(),
  confirmResetPassword: jest.fn(),
  isLoading: false,
  error: null as any,
  getToken: jest.fn(),
};

jest.mock("../use-amplify-auth", () => ({
  useAmplifyAuth: () => mockAmplifyAuth,
}));

// auth store のモック / Mock auth store
const mockAuthStore = {
  user: null as any,
  isAuthenticated: false,
  login: jest.fn(),
  logout: jest.fn(),
  setError: jest.fn(),
  setLoading: jest.fn(),
  error: null as any,
};

jest.mock("@/stores/auth-store", () => ({
  useAuthStore: () => mockAuthStore,
}));

// notifications store のモック / Mock notifications store
const mockNotifications = {
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
  info: jest.fn(),
};

jest.mock("@/stores/ui-store", () => ({
  useNotifications: () => mockNotifications,
}));

// API client のモック / Mock API client
const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  setAuthToken: jest.fn(),
  clearAuthToken: jest.fn(),
};

jest.mock("@/lib/api-client", () => ({
  apiClient: mockApiClient,
}));

describe("useAuth", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // デフォルトのモック状態をリセット / Reset default mock state
    Object.assign(mockAuthStore, {
      user: null,
      isAuthenticated: false,
      error: null,
    });

    Object.assign(mockAmplifyAuth, {
      isLoading: false,
      error: null,
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => React.createElement(QueryClientProvider, { client: queryClient }, children);

  describe("初期状態 / Initial State", () => {
    it("初期状態が正しく設定される / Initial state is set correctly", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("認証済み状態が正しく反映される / Authenticated state is reflected correctly", () => {
      mockAuthStore.isAuthenticated = true;
      mockAuthStore.user = mockUser;

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe("ログイン機能 / Login Functionality", () => {
    it("ログインが成功する / Login succeeds", async () => {
      mockAmplifyAuth.signIn.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper });

      const credentials = { email: "test@example.com", password: "password123" };

      await waitFor(() => {
        result.current.login(credentials);
      });

      expect(mockAmplifyAuth.signIn).toHaveBeenCalledWith(credentials.email, credentials.password);
      expect(mockAuthStore.setLoading).toHaveBeenCalledWith(true);
    });

    it("ログインエラーが適切に処理される / Login error is handled properly", async () => {
      const errorMessage = "Invalid credentials";
      mockAmplifyAuth.signIn.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAuth(), { wrapper });

      const credentials = { email: "test@example.com", password: "wrong" };

      await waitFor(() => {
        result.current.login(credentials);
      });

      expect(mockAuthStore.setError).toHaveBeenCalledWith(errorMessage);
      expect(mockAuthStore.setLoading).toHaveBeenCalledWith(false);
    });

    it("ログイン中のローディング状態が管理される / Loading state during login is managed", async () => {
      mockAmplifyAuth.signIn.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

      const { result } = renderHook(() => useAuth(), { wrapper });

      const credentials = { email: "test@example.com", password: "password123" };

      result.current.login(credentials);

      expect(mockAuthStore.setLoading).toHaveBeenCalledWith(true);

      await waitFor(() => {
        expect(mockAuthStore.setLoading).toHaveBeenCalledWith(false);
      });
    });
  });

  describe("ログアウト機能 / Logout Functionality", () => {
    it("ログアウトが成功する / Logout succeeds", async () => {
      mockAmplifyAuth.signOut.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        result.current.logout();
      });

      expect(mockAmplifyAuth.signOut).toHaveBeenCalled();
      expect(mockAuthStore.setLoading).toHaveBeenCalledWith(true);
    });

    it("ログアウトエラーが適切に処理される / Logout error is handled properly", async () => {
      mockAmplifyAuth.signOut.mockRejectedValue(new Error("Logout failed"));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        result.current.logout();
      });

      expect(mockAuthStore.logout).toHaveBeenCalled();
      expect(mockApiClient.clearAuthToken).toHaveBeenCalled();
      expect(mockNotifications.warning).toHaveBeenCalledWith("ログアウト", "サーバーエラーが発生しましたが、ローカルからログアウトしました");
    });

    it("ログアウト時にクエリキャッシュがクリアされる / Query cache is cleared on logout", async () => {
      mockAmplifyAuth.signOut.mockResolvedValue(undefined);
      const clearSpy = jest.spyOn(queryClient, "clear");

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        result.current.logout();
      });

      expect(clearSpy).toHaveBeenCalled();
    });
  });

  describe("ユーザー情報取得 / User Info Retrieval", () => {
    it("認証済みユーザーの情報が取得される / Authenticated user info is retrieved", async () => {
      mockAuthStore.isAuthenticated = true;
      mockApiClient.get.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser);
      });

      expect(mockApiClient.get).toHaveBeenCalledWith("/api/v1/auth/me");
    });

    it("未認証時はユーザー情報が取得されない / User info is not retrieved when not authenticated", () => {
      mockAuthStore.isAuthenticated = false;

      renderHook(() => useAuth(), { wrapper });

      expect(mockApiClient.get).not.toHaveBeenCalled();
    });
  });

  describe("Amplify認証機能 / Amplify Auth Features", () => {
    it("サインアップ機能が利用できる / Sign up functionality is available", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.signUp).toBe("function");
      expect(result.current.signUp).toBe(mockAmplifyAuth.signUp);
    });

    it("メール確認機能が利用できる / Email confirmation functionality is available", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.confirmSignUp).toBe("function");
      expect(result.current.confirmSignUp).toBe(mockAmplifyAuth.confirmSignUp);
    });

    it("確認コード再送信機能が利用できる / Resend confirmation code functionality is available", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.resendConfirmationCode).toBe("function");
      expect(result.current.resendConfirmationCode).toBe(mockAmplifyAuth.resendConfirmationCode);
    });

    it("パスワードリセット機能が利用できる / Password reset functionality is available", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.resetPassword).toBe("function");
      expect(result.current.resetPassword).toBe(mockAmplifyAuth.resetPassword);
    });

    it("パスワードリセット確認機能が利用できる / Password reset confirmation functionality is available", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.confirmResetPassword).toBe("function");
      expect(result.current.confirmResetPassword).toBe(mockAmplifyAuth.confirmResetPassword);
    });

    it("トークン取得機能が利用できる / Token retrieval functionality is available", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.getToken).toBe("function");
      expect(result.current.getToken).toBe(mockAmplifyAuth.getToken);
    });
  });

  describe("ローディング状態 / Loading States", () => {
    it("Amplifyローディング状態が反映される / Amplify loading state is reflected", () => {
      mockAmplifyAuth.isLoading = true;

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(true);
    });

    it("ログインペンディング状態が管理される / Login pending state is managed", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.isLoginPending).toBe("boolean");
    });

    it("ログアウトペンディング状態が管理される / Logout pending state is managed", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.isLogoutPending).toBe("boolean");
    });

    it("リフレッシュペンディング状態が管理される / Refresh pending state is managed", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.isRefreshPending).toBe("boolean");
    });
  });

  describe("エラー状態 / Error States", () => {
    it("Amplifyエラーが反映される / Amplify error is reflected", () => {
      const amplifyError = "Amplify authentication error";
      mockAmplifyAuth.error = amplifyError;

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.error).toBe(amplifyError);
    });

    it("ストアエラーが反映される / Store error is reflected", () => {
      const storeError = "Store authentication error";
      mockAuthStore.error = storeError;

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.error).toBe(storeError);
    });

    it("Amplifyエラーがストアエラーより優先される / Amplify error takes precedence over store error", () => {
      const amplifyError = "Amplify error";
      const storeError = "Store error";

      mockAmplifyAuth.error = amplifyError;
      mockAuthStore.error = storeError;

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.error).toBe(amplifyError);
    });
  });

  describe("クエリ無効化 / Query Invalidation", () => {
    it("ログイン成功時にユーザークエリが無効化される / User query is invalidated on successful login", async () => {
      mockAmplifyAuth.signIn.mockResolvedValue(undefined);
      const invalidateQueriesSpy = jest.spyOn(queryClient, "invalidateQueries");

      const { result } = renderHook(() => useAuth(), { wrapper });

      const credentials = { email: "test@example.com", password: "password123" };

      await waitFor(() => {
        result.current.login(credentials);
      });

      expect(invalidateQueriesSpy).toHaveBeenCalled();
    });
  });

  describe("統合テスト / Integration Tests", () => {
    it("完全な認証フローが正しく動作する / Complete auth flow works correctly", async () => {
      // 1. 初期状態（未認証）/ Initial state (unauthenticated)
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();

      // 2. ログイン実行 / Execute login
      mockAmplifyAuth.signIn.mockResolvedValue(undefined);
      mockAuthStore.isAuthenticated = true;
      mockAuthStore.user = mockUser;

      const credentials = { email: "test@example.com", password: "password123" };

      await waitFor(() => {
        result.current.login(credentials);
      });

      // 3. ログイン後の状態確認 / Check state after login
      expect(mockAmplifyAuth.signIn).toHaveBeenCalledWith(credentials.email, credentials.password);

      // 4. ログアウト実行 / Execute logout
      mockAmplifyAuth.signOut.mockResolvedValue(undefined);
      mockAuthStore.isAuthenticated = false;
      mockAuthStore.user = null;

      await waitFor(() => {
        result.current.logout();
      });

      // 5. ログアウト後の状態確認 / Check state after logout
      expect(mockAmplifyAuth.signOut).toHaveBeenCalled();
    });
  });
});
