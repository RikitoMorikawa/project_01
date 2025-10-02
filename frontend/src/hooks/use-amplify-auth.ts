import { useState, useEffect, useCallback } from "react";
import {
  signIn,
  signOut,
  signUp,
  confirmSignUp,
  resendSignUpCode,
  resetPassword,
  confirmResetPassword,
  getCurrentUser,
  fetchAuthSession,
  AuthUser,
} from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useNotifications } from "@/stores/ui-store";

// Amplify認証の型定義
export interface AmplifyAuthUser {
  userId: string;
  username: string;
  email?: string;
  signInDetails?: any;
}

export interface SignUpParams {
  username: string;
  password: string;
  email: string;
}

export interface ConfirmSignUpParams {
  username: string;
  confirmationCode: string;
}

export interface ResetPasswordParams {
  username: string;
}

export interface ConfirmResetPasswordParams {
  username: string;
  confirmationCode: string;
  newPassword: string;
}

// AWS Amplify認証フック
export const useAmplifyAuth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [amplifyUser, setAmplifyUser] = useState<AmplifyAuthUser | null>(null);

  const { setUser, setLoading, setError: setStoreError, login, logout } = useAuthStore();
  const notifications = useNotifications();

  // 現在の認証ユーザーを取得
  const checkAuthState = useCallback(async () => {
    try {
      setIsLoading(true);
      const user = await getCurrentUser();
      const session = await fetchAuthSession();

      if (user && session.tokens?.accessToken) {
        const amplifyUserData: AmplifyAuthUser = {
          userId: user.userId,
          username: user.username,
          email: user.signInDetails?.loginId,
        };

        setAmplifyUser(amplifyUserData);

        // Zustandストアにユーザー情報を設定
        // 注意: AmplifyのユーザーデータをアプリケーションのUser型に変換
        const appUser = {
          id: 0, // バックエンドから取得する必要がある
          cognitoUserId: user.userId,
          email: user.signInDetails?.loginId || "",
          username: user.username,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        setUser(appUser);

        // JWTトークンを取得してAPIクライアントに設定
        const token = session.tokens.accessToken.toString();
        if (typeof window !== "undefined") {
          localStorage.setItem("auth_token", token);
        }
      }
    } catch (error) {
      console.log("認証されていないユーザー:", error);
      setAmplifyUser(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [setUser]);

  // Amplify Hubイベントリスナー
  useEffect(() => {
    const unsubscribe = Hub.listen("auth", ({ payload }) => {
      switch (payload.event) {
        case "signedIn":
          console.log("ユーザーがサインインしました");
          checkAuthState();
          break;
        case "signedOut":
          console.log("ユーザーがサインアウトしました");
          setAmplifyUser(null);
          logout();
          break;
        case "tokenRefresh":
          console.log("トークンがリフレッシュされました");
          checkAuthState();
          break;
        case "tokenRefresh_failure":
          console.log("トークンリフレッシュに失敗しました");
          handleSignOut();
          break;
      }
    });

    // 初期認証状態をチェック
    checkAuthState();

    return unsubscribe;
  }, [checkAuthState, logout]);

  // サインイン
  const handleSignIn = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      setStoreError(null);

      const { isSignedIn, nextStep } = await signIn({
        username: email,
        password,
      });

      if (isSignedIn) {
        await checkAuthState();
        notifications.success("ログイン成功", "ダッシュボードにリダイレクトします");

        // ダッシュボードにリダイレクト
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1000);
      } else {
        // 追加の認証ステップが必要な場合
        console.log("追加の認証ステップが必要:", nextStep);
        throw new Error("追加の認証ステップが必要です");
      }
    } catch (error: any) {
      const errorMessage = error.message || "ログインに失敗しました";
      setError(errorMessage);
      setStoreError(errorMessage);
      notifications.error("ログインエラー", errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // サインアウト
  const handleSignOut = async () => {
    try {
      setIsLoading(true);
      await signOut();

      // ローカルストレージをクリア
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
      }

      notifications.success("ログアウト完了");

      // ログインページにリダイレクト
      window.location.href = "/login";
    } catch (error: any) {
      console.error("サインアウトエラー:", error);
      // エラーが発生してもローカル状態はクリア
      logout();
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
      }
      notifications.warning("ログアウト", "サーバーエラーが発生しましたが、ローカルからログアウトしました");
      window.location.href = "/login";
    } finally {
      setIsLoading(false);
    }
  };

  // サインアップ
  const handleSignUp = async ({ username, password, email }: SignUpParams) => {
    try {
      setIsLoading(true);
      setError(null);

      const { isSignUpComplete, userId, nextStep } = await signUp({
        username: email, // Cognitoではemailをusernameとして使用
        password,
        options: {
          userAttributes: {
            email,
            preferred_username: username,
          },
        },
      });

      if (!isSignUpComplete && nextStep.signUpStep === "CONFIRM_SIGN_UP") {
        notifications.success("確認コード送信", "メールアドレスに確認コードを送信しました");
        return { requiresConfirmation: true, userId };
      }

      return { requiresConfirmation: false, userId };
    } catch (error: any) {
      const errorMessage = error.message || "サインアップに失敗しました";
      setError(errorMessage);
      notifications.error("サインアップエラー", errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // サインアップ確認
  const handleConfirmSignUp = async ({ username, confirmationCode }: ConfirmSignUpParams) => {
    try {
      setIsLoading(true);
      setError(null);

      const { isSignUpComplete } = await confirmSignUp({
        username,
        confirmationCode,
      });

      if (isSignUpComplete) {
        notifications.success("アカウント確認完了", "ログインしてください");
        return true;
      }

      return false;
    } catch (error: any) {
      const errorMessage = error.message || "確認に失敗しました";
      setError(errorMessage);
      notifications.error("確認エラー", errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 確認コード再送信
  const handleResendConfirmationCode = async (username: string) => {
    try {
      setIsLoading(true);
      await resendSignUpCode({ username });
      notifications.success("確認コード再送信", "メールアドレスに確認コードを再送信しました");
    } catch (error: any) {
      const errorMessage = error.message || "確認コードの再送信に失敗しました";
      setError(errorMessage);
      notifications.error("再送信エラー", errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // パスワードリセット
  const handleResetPassword = async ({ username }: ResetPasswordParams) => {
    try {
      setIsLoading(true);
      setError(null);

      const { nextStep } = await resetPassword({ username });

      if (nextStep.resetPasswordStep === "CONFIRM_RESET_PASSWORD_WITH_CODE") {
        notifications.success("リセットコード送信", "メールアドレスにパスワードリセットコードを送信しました");
        return true;
      }

      return false;
    } catch (error: any) {
      const errorMessage = error.message || "パスワードリセットに失敗しました";
      setError(errorMessage);
      notifications.error("パスワードリセットエラー", errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // パスワードリセット確認
  const handleConfirmResetPassword = async ({ username, confirmationCode, newPassword }: ConfirmResetPasswordParams) => {
    try {
      setIsLoading(true);
      setError(null);

      await confirmResetPassword({
        username,
        confirmationCode,
        newPassword,
      });

      notifications.success("パスワード変更完了", "新しいパスワードでログインしてください");
      return true;
    } catch (error: any) {
      const errorMessage = error.message || "パスワード変更に失敗しました";
      setError(errorMessage);
      notifications.error("パスワード変更エラー", errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 現在のJWTトークンを取得
  const getToken = async (): Promise<string | null> => {
    try {
      const session = await fetchAuthSession();
      return session.tokens?.accessToken?.toString() || null;
    } catch (error) {
      console.error("トークン取得エラー:", error);
      return null;
    }
  };

  return {
    // 状態
    amplifyUser,
    isLoading,
    error,
    isAuthenticated: !!amplifyUser,

    // アクション
    signIn: handleSignIn,
    signOut: handleSignOut,
    signUp: handleSignUp,
    confirmSignUp: handleConfirmSignUp,
    resendConfirmationCode: handleResendConfirmationCode,
    resetPassword: handleResetPassword,
    confirmResetPassword: handleConfirmResetPassword,
    getToken,
    checkAuthState,

    // ユーティリティ
    clearError: () => setError(null),
  };
};
