import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { useNotifications } from "@/stores/ui-store";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-client";
import { User, LoginCredentials } from "@/types";
import { useAmplifyAuth } from "@/hooks/use-amplify-auth";

// 認証API関数
const authApi = {
  // ログイン
  login: async (credentials: LoginCredentials) => {
    const response = await apiClient.post<{
      user: User;
      access_token: string;
      token_type: string;
    }>("/api/v1/auth/login", credentials);
    return response;
  },

  // ログアウト
  logout: async () => {
    await apiClient.post("/api/v1/auth/logout");
  },

  // 現在のユーザー情報取得
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<{ data: User }>("/api/v1/auth/me");
    return response.data;
  },

  // トークンリフレッシュ
  refreshToken: async () => {
    const response = await apiClient.post<{
      access_token: string;
      token_type: string;
    }>("/api/v1/auth/refresh");
    return response;
  },
};

// 統合認証フック（Amplify + 既存システム）
export const useAuth = () => {
  const queryClient = useQueryClient();
  const { user, isAuthenticated, login: setLogin, logout: setLogout, setError, setLoading } = useAuthStore();
  const notifications = useNotifications();

  // Amplify認証フックを使用
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

  // 現在のユーザー情報を取得
  const { data: currentUser, isLoading: isUserLoading } = useQuery({
    queryKey: queryKeys.auth.user(),
    queryFn: authApi.getCurrentUser,
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000, // 10分
    retry: false,
  });

  // ログインミューテーション（Amplifyを使用）
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      // Amplifyでサインイン
      await amplifySignIn(credentials.email, credentials.password);
      return { success: true };
    },
    onMutate: () => {
      setLoading(true);
      setError(null);
    },
    onSuccess: () => {
      // Amplifyが自動的にユーザー情報とトークンを管理
      // クエリキャッシュを無効化
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

  // ログアウトミューテーション（Amplifyを使用）
  const logoutMutation = useMutation({
    mutationFn: async () => {
      // Amplifyでサインアウト
      await amplifySignOut();
      return { success: true };
    },
    onMutate: () => {
      setLoading(true);
    },
    onSuccess: () => {
      // Amplifyが自動的にクリーンアップを実行
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
