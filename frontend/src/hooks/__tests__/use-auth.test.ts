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
import { mockUser } from "@/__tests__/utils/test-utils";

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
  });
});
