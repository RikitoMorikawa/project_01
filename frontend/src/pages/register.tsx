import React, { useState } from "react";
import Link from "next/link";
import { Layout } from "@/components/layout";
import { Button, Input, Card } from "@/components/ui";
import { useAuth } from "@/hooks/use-auth";
import { withGuestGuard } from "@/components/auth/AuthGuard";

interface SignUpForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface ConfirmForm {
  confirmationCode: string;
}

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  confirmationCode?: string;
  general?: string;
}

function Register() {
  const [step, setStep] = useState<"signup" | "confirm">("signup");
  const [signUpForm, setSignUpForm] = useState<SignUpForm>({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [confirmForm, setConfirmForm] = useState<ConfirmForm>({
    confirmationCode: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);

  const { signUp, confirmSignUp, resendConfirmationCode, error } = useAuth();

  const handleSignUpInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setSignUpForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    // エラーをクリア
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const handleConfirmInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfirmForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    // エラーをクリア
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const validateSignUpForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!signUpForm.username) {
      newErrors.username = "ユーザー名を入力してください";
    } else if (signUpForm.username.length < 3) {
      newErrors.username = "ユーザー名は3文字以上で入力してください";
    }

    if (!signUpForm.email) {
      newErrors.email = "メールアドレスを入力してください";
    } else if (!/\S+@\S+\.\S+/.test(signUpForm.email)) {
      newErrors.email = "有効なメールアドレスを入力してください";
    }

    if (!signUpForm.password) {
      newErrors.password = "パスワードを入力してください";
    } else if (signUpForm.password.length < 8) {
      newErrors.password = "パスワードは8文字以上で入力してください";
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/.test(signUpForm.password)) {
      newErrors.password = "パスワードは大文字、小文字、数字、特殊文字を含む必要があります";
    }

    if (!signUpForm.confirmPassword) {
      newErrors.confirmPassword = "パスワード確認を入力してください";
    } else if (signUpForm.password !== signUpForm.confirmPassword) {
      newErrors.confirmPassword = "パスワードが一致しません";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateConfirmForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!confirmForm.confirmationCode) {
      newErrors.confirmationCode = "確認コードを入力してください";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSignUpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateSignUpForm()) {
      return;
    }

    try {
      setIsLoading(true);
      setErrors({});

      const result = await signUp({
        username: signUpForm.username,
        email: signUpForm.email,
        password: signUpForm.password,
      });

      if (result.requiresConfirmation) {
        setStep("confirm");
      } else {
        // 確認が不要な場合はログインページにリダイレクト
        window.location.href = "/login";
      }
    } catch (error: any) {
      setErrors({ general: error.message || "アカウント作成に失敗しました" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateConfirmForm()) {
      return;
    }

    try {
      setIsLoading(true);
      setErrors({});

      const success = await confirmSignUp({
        username: signUpForm.email, // Cognitoではemailをusernameとして使用
        confirmationCode: confirmForm.confirmationCode,
      });

      if (success) {
        // 確認成功、ログインページにリダイレクト
        setTimeout(() => {
          window.location.href = "/login";
        }, 2000);
      }
    } catch (error: any) {
      setErrors({ general: error.message || "アカウント確認に失敗しました" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    try {
      setIsLoading(true);
      await resendConfirmationCode(signUpForm.email);
    } catch (error: any) {
      setErrors({ general: error.message || "確認コードの再送信に失敗しました" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout
      title="アカウント作成 - CSR Lambda API System"
      description="新しいアカウントを作成してサービスを開始してください"
      showHeader={false}
      showFooter={false}
    >
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

          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">{step === "signup" ? "アカウント作成" : "メール確認"}</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {step === "signup" ? (
              <>
                または{" "}
                <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
                  既存のアカウントでログイン
                </Link>
              </>
            ) : (
              "メールアドレスに送信された確認コードを入力してください"
            )}
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

            {step === "signup" ? (
              /* サインアップフォーム */
              <form onSubmit={handleSignUpSubmit} className="space-y-6">
                <Input
                  label="ユーザー名"
                  type="text"
                  name="username"
                  value={signUpForm.username}
                  onChange={handleSignUpInputChange}
                  error={errors.username}
                  fullWidth
                  autoComplete="username"
                  placeholder="ユーザー名を入力"
                />

                <Input
                  label="メールアドレス"
                  type="email"
                  name="email"
                  value={signUpForm.email}
                  onChange={handleSignUpInputChange}
                  error={errors.email}
                  fullWidth
                  autoComplete="email"
                  placeholder="your@example.com"
                />

                <Input
                  label="パスワード"
                  type="password"
                  name="password"
                  value={signUpForm.password}
                  onChange={handleSignUpInputChange}
                  error={errors.password}
                  fullWidth
                  autoComplete="new-password"
                  placeholder="8文字以上のパスワード"
                />

                <Input
                  label="パスワード確認"
                  type="password"
                  name="confirmPassword"
                  value={signUpForm.confirmPassword}
                  onChange={handleSignUpInputChange}
                  error={errors.confirmPassword}
                  fullWidth
                  autoComplete="new-password"
                  placeholder="パスワードを再入力"
                />

                <div className="flex items-center">
                  <input
                    id="agree-terms"
                    name="agree-terms"
                    type="checkbox"
                    required
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="agree-terms" className="ml-2 block text-sm text-gray-900">
                    <Link href="/terms" className="text-blue-600 hover:text-blue-500">
                      利用規約
                    </Link>
                    と
                    <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
                      プライバシーポリシー
                    </Link>
                    に同意します
                  </label>
                </div>

                <Button type="submit" loading={isLoading} fullWidth size="lg">
                  アカウントを作成
                </Button>
              </form>
            ) : (
              /* 確認コードフォーム */
              <form onSubmit={handleConfirmSubmit} className="space-y-6">
                <div className="text-center mb-6">
                  <p className="text-sm text-gray-600">
                    <strong>{signUpForm.email}</strong> に確認コードを送信しました
                  </p>
                </div>

                <Input
                  label="確認コード"
                  type="text"
                  name="confirmationCode"
                  value={confirmForm.confirmationCode}
                  onChange={handleConfirmInputChange}
                  error={errors.confirmationCode}
                  fullWidth
                  placeholder="6桁の確認コード"
                  maxLength={6}
                />

                <Button type="submit" loading={isLoading} fullWidth size="lg">
                  アカウントを確認
                </Button>

                <div className="text-center space-y-2">
                  <button
                    type="button"
                    onClick={handleResendCode}
                    disabled={isLoading}
                    className="text-sm text-blue-600 hover:text-blue-500 disabled:text-gray-400"
                  >
                    確認コードを再送信
                  </button>

                  <div>
                    <button type="button" onClick={() => setStep("signup")} className="text-sm text-gray-600 hover:text-gray-900">
                      ← アカウント作成に戻る
                    </button>
                  </div>
                </div>
              </form>
            )}

            {/* 戻るリンク */}
            <div className="mt-6 text-center">
              <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
                ← ホームに戻る
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
}

// ゲストガードを適用（認証済みユーザーはダッシュボードにリダイレクト）
export default withGuestGuard(Register);
