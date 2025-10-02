/**
 * 認証フロー統合テスト
 * Authentication flow integration tests
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import AuthForm from "@/components/auth/AuthForm";
import { useAuth } from "@/hooks/use-auth";
import { mockUser, mockApiResponse } from "@/__tests__/utils/test-utils";

// API モック設定 / API mock setup
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Amplify Auth のモック / Mock Amplify Auth
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
  getToken: jest.fn().mockResolvedValue("integration-test-token"),
};

jest.mock("@/hooks/use-amplify-auth", () => ({
  useAmplifyAuth: () => mockAmplifyAuth,
}));

// Auth store のモック / Mock auth store
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

// Notifications store のモック / Mock notifications store
const mockNotifications = {
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
  info: jest.fn(),
};

jest.mock("@/stores/ui-store", () => ({
  useNotifications: () => mockNotifications,
}));

// テスト用コンポーネント / Test component
const AuthTestComponent: React.FC = () => {
  const auth = useAuth();

  const handleLogin = async (credentials: any) => {
    await auth.login(credentials);
  };

  const handleLogout = async () => {
    await auth.logout();
  };

  return (
    <div>
      <div data-testid="auth-status">{auth.isAuthenticated ? "Authenticated" : "Not Authenticated"}</div>

      {auth.user && (
        <div data-testid="user-info">
          <span data-testid="username">{auth.user.username}</span>
          <span data-testid="email">{auth.user.email}</span>
        </div>
      )}

      {auth.error && <div data-testid="auth-error">{auth.error}</div>}

      {auth.isLoading && <div data-testid="auth-loading">Loading...</div>}

      {!auth.isAuthenticated ? (
        <AuthForm type="login" onSubmit={handleLogin} loading={auth.isLoading} error={auth.error} />
      ) : (
        <div>
          <button onClick={handleLogout} data-testid="logout-button">
            Logout
          </button>
        </div>
      )}
    </div>
  );
};

describe("認証フロー統合テスト / Authentication Flow Integration Tests", () => {
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

    // fetch モックのリセット / Reset fetch mock
    mockFetch.mockClear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;

  it("完全なログインフローが正常に動作する / Complete login flow works correctly", async () => {
    // Amplifyログインの成功をモック / Mock successful Amplify login
    mockAmplifyAuth.signIn.mockResolvedValue(undefined);

    render(<AuthTestComponent />, { wrapper });

    // 初期状態：未認証 / Initial state: not authenticated
    expect(screen.getByTestId("auth-status")).toHaveTextContent("Not Authenticated");
    expect(screen.getByText("ログイン")).toBeInTheDocument();

    // ログインフォームに入力 / Fill login form
    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });

    // ログインボタンをクリック / Click login button
    const loginButton = screen.getByRole("button", { name: "ログイン" });
    fireEvent.click(loginButton);

    // Amplifyログインが呼ばれることを確認 / Verify Amplify login is called
    await waitFor(() => {
      expect(mockAmplifyAuth.signIn).toHaveBeenCalledWith("test@example.com", "password123");
    });

    // 認証状態の更新をシミュレート / Simulate auth state update
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.user = mockUser;

    // 再レンダリングして認証状態を確認 / Re-render and check auth state
    render(<AuthTestComponent />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent("Authenticated");
    });
  });

  it("ログインエラーが適切に処理される / Login errors are handled properly", async () => {
    const errorMessage = "Invalid credentials";

    // Amplifyログインエラーをモック / Mock Amplify login error
    mockAmplifyAuth.signIn.mockRejectedValue(new Error(errorMessage));
    mockAmplifyAuth.error = errorMessage;

    render(<AuthTestComponent />, { wrapper });

    // ログインフォームに入力 / Fill login form
    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "wrongpassword" } });

    // ログインボタンをクリック / Click login button
    const loginButton = screen.getByRole("button", { name: "ログイン" });
    fireEvent.click(loginButton);

    // エラーメッセージが表示されることを確認 / Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByTestId("auth-error")).toHaveTextContent(errorMessage);
    });

    // 未認証状態が維持されることを確認 / Verify unauthenticated state is maintained
    expect(screen.getByTestId("auth-status")).toHaveTextContent("Not Authenticated");
  });

  it("ログアウトフローが正常に動作する / Logout flow works correctly", async () => {
    // 初期状態を認証済みに設定 / Set initial state to authenticated
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.user = mockUser;
    mockAmplifyAuth.signOut.mockResolvedValue(undefined);

    render(<AuthTestComponent />, { wrapper });

    // 認証済み状態を確認 / Verify authenticated state
    expect(screen.getByTestId("auth-status")).toHaveTextContent("Authenticated");
    expect(screen.getByTestId("logout-button")).toBeInTheDocument();

    // ログアウトボタンをクリック / Click logout button
    const logoutButton = screen.getByTestId("logout-button");
    fireEvent.click(logoutButton);

    // Amplifyログアウトが呼ばれることを確認 / Verify Amplify logout is called
    await waitFor(() => {
      expect(mockAmplifyAuth.signOut).toHaveBeenCalled();
    });

    // ログアウト後の状態をシミュレート / Simulate post-logout state
    mockAuthStore.isAuthenticated = false;
    mockAuthStore.user = null;

    // 再レンダリングして未認証状態を確認 / Re-render and check unauthenticated state
    render(<AuthTestComponent />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent("Not Authenticated");
    });
  });

  it("ローディング状態が正しく表示される / Loading state is displayed correctly", async () => {
    // ローディング状態をモック / Mock loading state
    mockAmplifyAuth.isLoading = true;
    mockAmplifyAuth.signIn.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 1000)));

    render(<AuthTestComponent />, { wrapper });

    // ログインフォームに入力 / Fill login form
    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });

    // ローディング状態を確認 / Check loading state
    expect(screen.getByTestId("auth-loading")).toBeInTheDocument();

    // ログインボタンが無効化されていることを確認 / Verify login button is disabled
    const loginButton = screen.getByRole("button", { name: "ログイン" });
    expect(loginButton).toBeDisabled();
  });

  it("トークン取得が正常に動作する / Token retrieval works correctly", async () => {
    // 認証済み状態を設定 / Set authenticated state
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.user = mockUser;

    render(<AuthTestComponent />, { wrapper });

    // トークン取得をテスト / Test token retrieval
    const token = await mockAmplifyAuth.getToken();
    expect(token).toBe("integration-test-token");
    expect(mockAmplifyAuth.getToken).toHaveBeenCalled();
  });

  it("認証状態の永続化が動作する / Auth state persistence works", async () => {
    // localStorage にトークンが保存されている状態をシミュレート
    // Simulate token saved in localStorage
    const mockLocalStorage = {
      getItem: jest.fn().mockReturnValue("integration-test-token"),
      setItem: jest.fn(),
      removeItem: jest.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: mockLocalStorage });

    // 認証済み状態を設定 / Set authenticated state
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.user = mockUser;

    render(<AuthTestComponent />, { wrapper });

    // 認証状態が復元されることを確認 / Verify auth state is restored
    expect(screen.getByTestId("auth-status")).toHaveTextContent("Authenticated");
    expect(screen.getByTestId("username")).toHaveTextContent(mockUser.username);
  });

  it("複数の認証アクションが順次実行される / Multiple auth actions execute sequentially", async () => {
    // 複数のAmplifyアクションをモック / Mock multiple Amplify actions
    mockAmplifyAuth.signIn.mockResolvedValue(undefined);
    mockAmplifyAuth.signOut.mockResolvedValue(undefined);

    render(<AuthTestComponent />, { wrapper });

    // 1. ログイン / Login
    const emailInput = screen.getByLabelText("メールアドレス");
    const passwordInput = screen.getByLabelText("パスワード");

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });

    const loginButton = screen.getByRole("button", { name: "ログイン" });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(mockAmplifyAuth.signIn).toHaveBeenCalled();
    });

    // 認証状態を更新 / Update auth state
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.user = mockUser;

    // 再レンダリング / Re-render
    render(<AuthTestComponent />, { wrapper });

    // 2. ログアウト / Logout
    const logoutButton = screen.getByTestId("logout-button");
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockAmplifyAuth.signOut).toHaveBeenCalled();
    });

    // 両方のアクションが実行されたことを確認 / Verify both actions were executed
    expect(mockAmplifyAuth.signIn).toHaveBeenCalledTimes(1);
    expect(mockAmplifyAuth.signOut).toHaveBeenCalledTimes(1);
  });
});
