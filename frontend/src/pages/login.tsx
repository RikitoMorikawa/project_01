import React, { useState } from "react";
import Link from "next/link";
import { Layout } from "@/components/layout";
import { Button, Input, Card } from "@/components/ui";
import { useAuth } from "@/hooks/use-auth";
import { LoginCredentials } from "@/types";
import { withGuestGuard } from "@/components/auth/AuthGuard";

interface LoginForm {
  email: string;
  password: string;
}

interface LoginError {
  email?: string;
  password?: string;
  general?: string;
}

function Login() {
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<LoginError>({});

  // 新しい認証フックを使用
  const { login, isLoginPending, error } = useAuth();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    // エラーをクリア
    if (errors[name as keyof LoginError]) {
      setErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: LoginError = {};

    if (!form.email) {
      newErrors.email = "メールアドレスを入力してください";
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      newErrors.email = "有効なメールアドレスを入力してください";
    }

    if (!form.password) {
      newErrors.password = "パスワードを入力してください";
    } else if (form.password.length < 8) {
      newErrors.password = "パスワードは8文字以上で入力してください";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // 新しい認証システムを使用
    const credentials: LoginCredentials = {
      email: form.email,
      password: form.password,
    };

    login(credentials);
  };

  const handleForgotPassword = () => {
    // パスワードリセット画面に遷移
    window.location.href = "/forgot-password";
  };

  const handleSocialLogin = (provider: "google" | "github") => {
    // ソーシャルログイン処理
    console.log(`${provider}でログイン`);
    // TODO: 実際のソーシャルログイン処理を実装
  };

  return (
    <Layout title="ログイン - CSR Lambda API System" description="アカウントにログインしてサービスをご利用ください" showHeader={false} showFooter={false}>
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          {/* ロゴ */}
          <div className="flex justify-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
            </Link>
          </div>

          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">アカウントにログイン</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            または{" "}
            <Link href="/register" className="font-medium text-blue-600 hover:text-blue-500">
              新しいアカウントを作成
            </Link>
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <Card className="py-8 px-4 sm:px-10">
            {/* エラーメッセージ */}
            {(errors.general || error) && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{errors.general || error}</p>
              </div>
            )}

            {/* ログインフォーム */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <Input
                label="メールアドレス"
                type="email"
                name="email"
                value={form.email}
                onChange={handleInputChange}
                error={errors.email}
                fullWidth
                autoComplete="email"
                placeholder="your@example.com"
              />

              <Input
                label="パスワード"
                type="password"
                name="password"
                value={form.password}
                onChange={handleInputChange}
                error={errors.password}
                fullWidth
                autoComplete="current-password"
                placeholder="パスワードを入力"
              />

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                    ログイン状態を保持
                  </label>
                </div>

                <button type="button" onClick={handleForgotPassword} className="text-sm text-blue-600 hover:text-blue-500">
                  パスワードを忘れた場合
                </button>
              </div>

              <Button type="submit" loading={isLoginPending} fullWidth size="lg">
                ログイン
              </Button>
            </form>

            {/* ソーシャルログイン */}
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
                <Button variant="outline" onClick={() => handleSocialLogin("google")} className="w-full">
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

                <Button variant="outline" onClick={() => handleSocialLogin("github")} className="w-full">
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
          </Card>

          {/* 追加リンク */}
          <div className="mt-6 text-center">
            <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
              ← ホームに戻る
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}

// ゲストガードを適用（認証済みユーザーはダッシュボードにリダイレクト）
export default withGuestGuard(Login);
