/**
 * 認証フック
 *
 * AWS Amplify と既存の認証システムを統合した認証機能を提供する。
 * ログイン、ログアウト、ユーザー情報取得、トークン管理などの機能を含む。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { useNotifications } from "@/stores/ui-store";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-client";
import { User, LoginCredentials } from "@/types";
import { useAmplifyAuth } from "@/hooks/use-amplify-auth";

/**
 * 認証 API 関数群
 *
 * バックエンド API との認証関連通信を行う関数を定義する。
 */
const authApi = {
  /**
   * ログイン処理
   *
   * @param credentials ログイン認証情報
   * @returns ユーザー情報とアクセストークン
   */
  login: async (credentials: LoginCredentials) => {
    const response = await apiClient.post<{
      user: User;
      access_token: string;
      token_type: string;
    }>("/api/v1/auth/login", credentials);
    return response;
  },

  /**
   * ログアウト処理
   */
  logout: async () => {
    await apiClient.post("/api/v1/auth/logout");
  },

  /**
   * 現在のユーザー情報を取得
   *
   * @returns 現在ログイン中のユーザー情報
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<{ data: User }>("/api/v1/auth/me");
    return response.data;
  },

  /**
   * アクセストークンをリフレッシュ
   *
   * @returns 新しいアクセストークン
   */
  refreshToken: async () => {
    const response = await apiClient.post<{
      access_token: string;
      token_type: string;
    }>("/api/v1/auth/refresh");
    return response;
  },
};

/**
 * 統合認証フック（Amplify + 既存システム）
 *
 * AWS Amplify の認証機能と既存の認証システムを統合し、
 * 統一されたインターフェースで認証機能を提供する。
 *
 * @returns 認証状態と認証操作関数
 */
export const useAuth = () => {
  const queryClient = useQueryClient();
  const { user, isAuthenticated, login: setLogin, logout: setLogout, setError, setLoading } = useAuthStore();
  const notifications = useNotifications();

  // Amplify 認証フックを使用
  const {
    signIn: amplifySignIn,
    signOut: amplifySignOut,
    signUp,
    confirmSignUp,
    resendConfirmationCode,
    resetPassword,
    confirmResetPassword,
    isLoading: amplifyLoading,
    error: amplifyError,
    getToken,
  } = useAmplifyAuth();

  // 現在のユーザー情報を取得するクエリ
  const { data: currentUser, isLoading: isUserLoading } = useQuery({
    queryKey: queryKeys.auth.user(),
    queryFn: authApi.getCurrentUser,
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000, // 10分間キャッシュ
    retry: false,
  });

  // ログインミューテーション（Amplify を使用）
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      // Amplify でサインイン
      await amplifySignIn(credentials.email, credentials.password);
      return { success: true };
    },
    onMutate: () => {
      setLoading(true);
      setError(null);
    },
    onSuccess: () => {
      // Amplify が自動的にユーザー情報とトークンを管理
      // クエリキャッシュを無効化して最新情報を取得
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.user() });
    },
    onError: (error: any) => {
      const errorMessage = error.message || "ログインに失敗しました";
      setError(errorMessage);
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  // ログアウトミューテーション（Amplify を使用）
  const logoutMutation = useMutation({
    mutationFn: async () => {
      // Amplify でサインアウト
      await amplifySignOut();
      return { success: true };
    },
    onMutate: () => {
      setLoading(true);
    },
    onSuccess: () => {
      // Amplify が自動的にクリーンアップを実行
      // 全てのクエリキャッシュをクリア
      queryClient.clear();
    },
    onError: (error: any) => {
      // エラーが発生してもログアウト処理は続行
      setLogout();
      apiClient.clearAuthToken();
      queryClient.clear();
      notifications.warning("ログアウト", "サーバーエラーが発生しましたが、ローカルからログアウトしました");
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  // トークンリフレッシュミューテーション
  const refreshTokenMutation = useMutation({
    mutationFn: authApi.refreshToken,
    onSuccess: (data) => {
      const { access_token } = data;
      apiClient.setAuthToken(access_token);

      // ローカルストレージのトークンも更新
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", access_token);
      }
    },
    onError: () => {
      // リフレッシュに失敗した場合はログアウト
      logoutMutation.mutate();
    },
  });

  return {
    // 状態
    user: currentUser || user,
    isAuthenticated,
    isLoading: isUserLoading || loginMutation.isPending || logoutMutation.isPending || amplifyLoading,
    error: amplifyError || useAuthStore.getState().error,

    // 基本認証アクション
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    getToken,

    // Amplify認証アクション
    signUp,
    confirmSignUp,
    resendConfirmationCode,
    resetPassword,
    confirmResetPassword,

    // ミューテーション状態
    isLoginPending: loginMutation.isPending,
    isLogoutPending: logoutMutation.isPending,
    isRefreshPending: refreshTokenMutation.isPending,
  };
};
