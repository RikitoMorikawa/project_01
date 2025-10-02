import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { User } from "@/types";

// 認証状態の型定義
interface AuthState {
  // 状態
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // アクション
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  login: (user: User, token: string) => void;
  logout: () => void;
  clearError: () => void;
}

// 認証ストア
export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        // 初期状態
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,

        // ユーザー設定
        setUser: (user) =>
          set(
            {
              user,
              isAuthenticated: !!user,
            },
            false,
            "auth/setUser"
          ),

        // ローディング状態設定
        setLoading: (loading) => set({ isLoading: loading }, false, "auth/setLoading"),

        // エラー設定
        setError: (error) => set({ error }, false, "auth/setError"),

        // ログイン
        login: (user, token) => {
          // トークンをローカルストレージに保存
          if (typeof window !== "undefined") {
            localStorage.setItem("auth_token", token);
          }

          set(
            {
              user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            },
            false,
            "auth/login"
          );
        },

        // ログアウト
        logout: () => {
          // トークンをローカルストレージから削除
          if (typeof window !== "undefined") {
            localStorage.removeItem("auth_token");
          }

          set(
            {
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            },
            false,
            "auth/logout"
          );
        },

        // エラークリア
        clearError: () => set({ error: null }, false, "auth/clearError"),
      }),
      {
        name: "auth-storage",
        // 永続化する項目を指定
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    {
      name: "auth-store",
    }
  )
);
