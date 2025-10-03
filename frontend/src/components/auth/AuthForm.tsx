/**
 * 認証フォームコンポーネント
 *
 * ログイン、ユーザー登録、パスワードリセットなどの認証関連フォームを
 * 統一されたインターフェースで提供する。バリデーション、エラーハンドリング、
 * ソーシャルログイン機能を含む。
 */
import React, { useState } from "react";
import { Form, Input, Button } from "@/components/ui";
import PasswordStrengthIndicator from "./PasswordStrengthIndicator";

/**
 * 認証フォームのプロパティ
 */
export interface AuthFormProps {
  /** フォームの種類 */
  type: "login" | "register" | "forgot-password" | "reset-password";
  /** フォーム送信時のコールバック */
  onSubmit: (data: any) => Promise<void>;
  /** ローディング状態 */
  loading?: boolean;
  /** エラーメッセージ */
  error?: string | null;
  /** 成功メッセージ */
  success?: string | null;
  /** フォームの初期値 */
  initialData?: Record<string, string>;
  /** パスワード強度インジケーターの表示 */
  showPasswordStrength?: boolean;
  /** ソーシャルログインボタンの表示 */
  showSocialLogin?: boolean;
  /** ソーシャルログイン時のコールバック */
  onSocialLogin?: (provider: "google" | "github") => void;
}

/**
 * 認証フォームコンポーネント
 */
const AuthForm: React.FC<AuthFormProps> = ({
  type,
  onSubmit,
  loading = false,
  error,
  success,
  initialData = {},
  showPasswordStrength = false,
  showSocialLogin = false,
  onSocialLogin,
}) => {
  // フォームデータの状態管理
  const [formData, setFormData] = useState<Record<string, string>>(initialData);
  // バリデーションエラーの状態管理
  const [errors, setErrors] = useState<Record<string, string>>({});

  /**
   * 入力値変更時の処理
   *
   * @param e 入力イベント
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // 該当フィールドのエラーをクリア
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  /**
   * フォームバリデーション
   *
   * フォームの種類に応じて適切なバリデーションを実行する。
   *
   * @returns バリデーション結果（true: 成功, false: 失敗）
   */
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // 共通バリデーション - メールアドレス
    if (type !== "reset-password" && !formData.email) {
      newErrors.email = "メールアドレスを入力してください";
    } else if (type !== "reset-password" && formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "有効なメールアドレスを入力してください";
    }

    // フォームタイプ別バリデーション
    switch (type) {
      case "register":
        // ユーザー名バリデーション
        if (!formData.username) {
          newErrors.username = "ユーザー名を入力してください";
        } else if (formData.username.length < 3) {
          newErrors.username = "ユーザー名は3文字以上で入力してください";
        }
        // パスワードバリデーション（登録時）
        if (!formData.password) {
          newErrors.password = "パスワードを入力してください";
        } else if (formData.password.length < 8) {
          newErrors.password = "パスワードは8文字以上で入力してください";
        }
        // パスワード確認バリデーション
        if (!formData.confirmPassword) {
          newErrors.confirmPassword = "パスワード確認を入力してください";
        } else if (formData.password !== formData.confirmPassword) {
          newErrors.confirmPassword = "パスワードが一致しません";
        }
        break;

      case "login":
        // ログイン時のパスワードバリデーション
        if (!formData.password) {
          newErrors.password = "パスワードを入力してください";
        }
        break;

      case "reset-password":
        // 確認コードバリデーション
        if (!formData.confirmationCode) {
          newErrors.confirmationCode = "確認コードを入力してください";
        }
        // 新しいパスワードバリデーション
        if (!formData.newPassword) {
          newErrors.newPassword = "新しいパスワードを入力してください";
        } else if (formData.newPassword.length < 8) {
          newErrors.newPassword = "パスワードは8文字以上で入力してください";
        }
        // パスワード確認バリデーション
        if (!formData.confirmPassword) {
          newErrors.confirmPassword = "パスワード確認を入力してください";
        } else if (formData.newPassword !== formData.confirmPassword) {
          newErrors.confirmPassword = "パスワードが一致しません";
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * フォーム送信処理
   *
   * @param e フォーム送信イベント
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // バリデーション実行
    if (!validateForm()) {
      return;
    }

    // 親コンポーネントの送信処理を呼び出し
    await onSubmit(formData);
  };

  /**
   * フォームタイトルを取得
   *
   * @returns フォームタイトル
   */
  const getFormTitle = () => {
    switch (type) {
      case "login":
        return "ログイン";
      case "register":
        return "アカウント作成";
      case "forgot-password":
        return "パスワードリセット";
      case "reset-password":
        return "新しいパスワード設定";
      default:
        return "";
    }
  };

  /**
   * 送信ボタンのラベルを取得
   *
   * @returns 送信ボタンのラベル
   */
  const getSubmitLabel = () => {
    switch (type) {
      case "login":
        return "ログイン";
      case "register":
        return "アカウントを作成";
      case "forgot-password":
        return "リセットコードを送信";
      case "reset-password":
        return "パスワードを変更";
      default:
        return "送信";
    }
  };

  return (
    <div className="space-y-6">
      <Form
        title={getFormTitle()}
        onSubmit={handleSubmit}
        loading={loading}
        error={error || undefined}
        success={success || undefined}
        submitLabel={getSubmitLabel()}
        showSubmitButton={true}
      >
        {/* ユーザー名（登録時のみ） */}
        {type === "register" && (
          <Input
            label="ユーザー名"
            name="username"
            value={formData.username || ""}
            onChange={handleInputChange}
            error={errors.username}
            fullWidth
            autoComplete="username"
            placeholder="ユーザー名を入力"
          />
        )}

        {/* メールアドレス（パスワードリセット確認以外） */}
        {type !== "reset-password" && (
          <Input
            label="メールアドレス"
            type="email"
            name="email"
            value={formData.email || ""}
            onChange={handleInputChange}
            error={errors.email}
            fullWidth
            autoComplete="email"
            placeholder="your@example.com"
          />
        )}

        {/* 確認コード（パスワードリセット確認時） */}
        {type === "reset-password" && (
          <Input
            label="確認コード"
            name="confirmationCode"
            value={formData.confirmationCode || ""}
            onChange={handleInputChange}
            error={errors.confirmationCode}
            fullWidth
            placeholder="メールに送信された6桁のコード"
            maxLength={6}
          />
        )}

        {/* パスワード（パスワードリセット要求以外） */}
        {type !== "forgot-password" && (
          <div>
            <Input
              label={type === "reset-password" ? "新しいパスワード" : "パスワード"}
              type="password"
              name={type === "reset-password" ? "newPassword" : "password"}
              value={formData[type === "reset-password" ? "newPassword" : "password"] || ""}
              onChange={handleInputChange}
              error={errors[type === "reset-password" ? "newPassword" : "password"]}
              fullWidth
              autoComplete={type === "login" ? "current-password" : "new-password"}
              placeholder={type === "reset-password" ? "8文字以上の新しいパスワード" : "パスワードを入力"}
            />

            {/* パスワード強度インジケーター */}
            {showPasswordStrength && (type === "register" || type === "reset-password") && (
              <PasswordStrengthIndicator password={formData[type === "reset-password" ? "newPassword" : "password"] || ""} />
            )}
          </div>
        )}

        {/* パスワード確認（登録・パスワードリセット時） */}
        {(type === "register" || type === "reset-password") && (
          <Input
            label="パスワード確認"
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword || ""}
            onChange={handleInputChange}
            error={errors.confirmPassword}
            fullWidth
            autoComplete="new-password"
            placeholder="パスワードを再入力"
          />
        )}

        {/* ログイン状態保持（ログイン時のみ） */}
        {type === "login" && (
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                ログイン状態を保持
              </label>
            </div>
          </div>
        )}

        {/* 利用規約同意（登録時のみ） */}
        {type === "register" && (
          <div className="flex items-center">
            <input id="agree-terms" name="agree-terms" type="checkbox" required className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
            <label htmlFor="agree-terms" className="ml-2 block text-sm text-gray-900">
              利用規約とプライバシーポリシーに同意します
            </label>
          </div>
        )}
      </Form>

      {/* ソーシャルログイン */}
      {showSocialLogin && type === "login" && onSocialLogin && (
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">または</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <Button variant="outline" onClick={() => onSocialLogin("google")} className="w-full">
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Google
            </Button>

            <Button variant="outline" onClick={() => onSocialLogin("github")} className="w-full">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z"
                  clipRule="evenodd"
                />
              </svg>
              GitHub
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuthForm;
