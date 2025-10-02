import React from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useAuth } from "@/hooks/use-auth";

interface AuthStatusProps {
  showDetails?: boolean;
  className?: string;
}

/**
 * 認証状態表示コンポーネント
 *
 * 開発時のデバッグ用に認証状態を表示する
 */
export const AuthStatus: React.FC<AuthStatusProps> = ({ showDetails = false, className = "" }) => {
  const { user, isAuthenticated } = useAuthStore();
  const { isLoading, error } = useAuth();

  if (!showDetails && process.env.NODE_ENV === "production") {
    return null;
  }

  return (
    <div className={`bg-gray-100 border border-gray-300 rounded-lg p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">認証状態</h3>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-600">認証済み:</span>
          <span className={isAuthenticated ? "text-green-600" : "text-red-600"}>{isAuthenticated ? "はい" : "いいえ"}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">ローディング:</span>
          <span className={isLoading ? "text-yellow-600" : "text-gray-600"}>{isLoading ? "はい" : "いいえ"}</span>
        </div>

        {error && (
          <div className="flex justify-between">
            <span className="text-gray-600">エラー:</span>
            <span className="text-red-600 truncate max-w-32" title={error}>
              {error}
            </span>
          </div>
        )}

        {user && (
          <div className="mt-3 pt-2 border-t border-gray-200">
            <div className="flex justify-between">
              <span className="text-gray-600">ユーザーID:</span>
              <span className="text-gray-900">{user.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">メール:</span>
              <span className="text-gray-900 truncate max-w-32" title={user.email}>
                {user.email}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">ユーザー名:</span>
              <span className="text-gray-900 truncate max-w-32" title={user.username}>
                {user.username}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
