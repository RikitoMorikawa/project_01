import React, { createContext, useContext, useEffect, useState } from "react";
import { configureAmplify } from "@/lib/amplify-config";
import { useAmplifyAuth } from "@/hooks/use-amplify-auth";
import { useAuthStore } from "@/stores/auth-store";
import { apiClient } from "@/lib/api-client";

// 認証コンテキストの型定義
interface AuthContextType {
  // Amplify認証メソッド
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  signUp: (params: { username: string; password: string; email: string }) => Promise<any>;
  confirmSignUp: (params: { username: string; confirmationCode: string }) => Promise<boolean>;
  resendConfirmationCode: (username: string) => Promise<void>;
  resetPassword: (params: { username: string }) => Promise<boolean>;
  confirmResetPassword: (params: { username: string; confirmationCode: string; newPassword: string }) => Promise<boolean>;

  // 状態
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  // ユーティリティ
  getToken: () => Promise<string | null>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * 認証プロバイダー
 *
 * AWS Amplify認証と既存の認証システムを統合する
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const { isAuthenticated } = useAuthStore();

  const {
    signIn,
    signOut,
    signUp,
    confirmSignUp,
    resendConfirmationCode,
    resetPassword,
    confirmResetPassword,
    isLoading,
    error,
    getToken,
    clearError,
    checkAuthState,
  } = useAmplifyAuth();

  // Amplifyの初期化
  useEffect(() => {
    const initializeAmplify = async () => {
      try {
        // Amplify設定を適用
        configureAmplify();

        // 初期認証状態をチェック
        await checkAuthState();

        console.log("AWS Amplify認証システムが初期化されました");
      } catch (error) {
        console.error("Amplify初期化エラー:", error);
      } finally {
        setIsInitialized(true);
      }
    };

    initializeAmplify();
  }, [checkAuthState]);

  // 認証状態が変更された時にAPIクライアントのトークンを更新
  useEffect(() => {
    const updateApiToken = async () => {
      if (isAuthenticated) {
        const token = await getToken();
        if (token) {
          apiClient.setAuthToken(token);
        }
      } else {
        apiClient.clearAuthToken();
      }
    };

    if (isInitialized) {
      updateApiToken();
    }
  }, [isAuthenticated, isInitialized, getToken]);

  // トークンの自動更新（30分ごと）
  useEffect(() => {
    if (!isAuthenticated || !isInitialized) return;

    const refreshInterval = setInterval(async () => {
      try {
        const token = await getToken();
        if (token) {
          apiClient.setAuthToken(token);
          console.log("認証トークンが更新されました");
        }
      } catch (error) {
        console.error("トークン更新エラー:", error);
        // トークン更新に失敗した場合はサインアウト
        await signOut();
      }
    }, 30 * 60 * 1000); // 30分

    return () => clearInterval(refreshInterval);
  }, [isAuthenticated, isInitialized, getToken, signOut]);

  const contextValue: AuthContextType = {
    // Amplify認証メソッド
    signIn,
    signOut,
    signUp,
    confirmSignUp,
    resendConfirmationCode,
    resetPassword,
    confirmResetPassword,

    // 状態
    isLoading,
    error,
    isAuthenticated,

    // ユーティリティ
    getToken,
    clearError,
  };

  // 初期化が完了するまでローディング表示
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">認証システムを初期化中...</p>
        </div>
      </div>
    );
  }

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

/**
 * 認証コンテキストを使用するためのフック
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
