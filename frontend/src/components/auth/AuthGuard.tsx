import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuthStore } from "@/stores/auth-store";
import { useAmplifyAuth } from "@/hooks/use-amplify-auth";
import Loading from "@/components/ui/Loading";

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  redirectTo?: string;
  fallback?: React.ReactNode;
}

/**
 * 認証ガードコンポーネント
 *
 * 認証が必要なページを保護し、未認証ユーザーをリダイレクトする
 */
export const AuthGuard: React.FC<AuthGuardProps> = ({ children, requireAuth = true, redirectTo = "/login", fallback }) => {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { isLoading, checkAuthState } = useAmplifyAuth();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Amplifyの認証状態を確認
        await checkAuthState();
      } catch (error) {
        console.error("認証状態確認エラー:", error);
      } finally {
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [checkAuthState]);

  useEffect(() => {
    // 認証チェックが完了し、認証が必要なページで未認証の場合
    if (!isChecking && !isLoading && requireAuth && !isAuthenticated) {
      // 現在のパスを保存してログイン後にリダイレクト
      const returnUrl = router.asPath;
      const loginUrl = `${redirectTo}?returnUrl=${encodeURIComponent(returnUrl)}`;
      router.replace(loginUrl);
    }
  }, [isChecking, isLoading, requireAuth, isAuthenticated, router, redirectTo]);

  // 認証チェック中またはAmplifyローディング中
  if (isChecking || isLoading) {
    return (
      fallback || (
        <div className="min-h-screen flex items-center justify-center">
          <Loading size="lg" text="認証状態を確認中..." />
        </div>
      )
    );
  }

  // 認証が必要で未認証の場合は何も表示しない（リダイレクト処理中）
  if (requireAuth && !isAuthenticated) {
    return null;
  }

  // 認証済みまたは認証不要の場合は子コンポーネントを表示
  return <>{children}</>;
};

/**
 * 認証済みユーザー専用ページ用のHOC
 */
export const withAuthGuard = <P extends object>(
  Component: React.ComponentType<P>,
  options?: {
    redirectTo?: string;
    fallback?: React.ReactNode;
  }
) => {
  const WrappedComponent = (props: P) => (
    <AuthGuard requireAuth={true} redirectTo={options?.redirectTo} fallback={options?.fallback}>
      <Component {...props} />
    </AuthGuard>
  );

  WrappedComponent.displayName = `withAuthGuard(${Component.displayName || Component.name})`;

  return WrappedComponent;
};

/**
 * 未認証ユーザー専用ページ用のHOC（ログインページなど）
 */
export const withGuestGuard = <P extends object>(Component: React.ComponentType<P>, redirectTo: string = "/dashboard") => {
  const WrappedComponent = (props: P) => {
    const router = useRouter();
    const { isAuthenticated } = useAuthStore();
    const { isLoading } = useAmplifyAuth();
    const [isChecking, setIsChecking] = useState(true);

    useEffect(() => {
      setIsChecking(false);
    }, []);

    useEffect(() => {
      // 認証済みユーザーがゲスト専用ページにアクセスした場合
      if (!isChecking && !isLoading && isAuthenticated) {
        router.replace(redirectTo);
      }
    }, [isChecking, isLoading, isAuthenticated, router]);

    // 認証チェック中
    if (isChecking || isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <Loading size="lg" text="認証状態を確認中..." />
        </div>
      );
    }

    // 認証済みユーザーの場合は何も表示しない（リダイレクト処理中）
    if (isAuthenticated) {
      return null;
    }

    // 未認証ユーザーの場合はコンポーネントを表示
    return <Component {...props} />;
  };

  WrappedComponent.displayName = `withGuestGuard(${Component.displayName || Component.name})`;

  return WrappedComponent;
};
