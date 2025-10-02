import React, { useState } from "react";
import Link from "next/link";
import { Layout } from "@/components/layout";
import { Button, Input, Card } from "@/components/ui";
import { useAuth } from "@/hooks/use-auth";
import { withGuestGuard } from "@/components/auth/AuthGuard";

interface ForgotPasswordForm {
  email: string;
}

interface ResetPasswordForm {
  confirmationCode: string;
  newPassword: string;
  confirmPassword: string;
}

interface FormErrors {
  email?: string;
  confirmationCode?: string;
  newPassword?: string;
  confirmPassword?: string;
  general?: string;
}

function ForgotPassword() {
  const [step, setStep] = useState<"request" | "confirm">("request");
  const [forgotForm, setForgotForm] = useState<ForgotPasswordForm>({
    email: "",
  });
  const [resetForm, setResetForm] = useState<ResetPasswordForm>({
    confirmationCode: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);

  const { resetPassword, confirmResetPassword, error } = useAuth();

  const handleForgotInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForgotForm((prev) => ({
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

  const handleResetInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setResetForm((prev) => ({
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

  const validateForgotForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!forgotForm.email) {
      newErrors.email = "メールアドレスを入力してください";
    } else if (!/\S+@\S+\.\S+/.test(forgotForm.email)) {
      newErrors.email = "有効なメールアドレスを入力してください";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateResetForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!resetForm.confirmationCode) {
      newErrors.confirmationCode = "確認コードを入力してください";
    }

    if (!resetForm.newPassword) {
      newErrors.newPassword = "新しいパスワードを入力してください";
    } else if (resetForm.newPassword.length < 8) {
      newErrors.newPassword = "パスワードは8文字以上で入力してください";
    }

    if (!resetForm.confirmPassword) {
      newErrors.confirmPassword = "パスワード確認を入力してください";
    } else if (resetForm.newPassword !== resetForm.confirmPassword) {
      newErrors.confirmPassword = "パスワードが一致しません";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForgotForm()) {
      return;
    }

    try {
      setIsLoading(true);
      setErrors({});

      const success = await resetPassword({ username: forgotForm.email });

      if (success) {
        setStep("confirm");
      }
    } catch (error: any) {
      setErrors({ general: error.message || "パスワードリセットの送信に失敗しました" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateResetForm()) {
      return;
    }

    try {
      setIsLoading(true);
      setErrors({});

      const success = await confirmResetPassword({
        username: forgotForm.email,
        confirmationCode: resetForm.confirmationCode,
        newPassword: resetForm.newPassword,
      });

      if (success) {
        // パスワード変更成功、ログインページにリダイレクト
        setTimeout(() => {
          window.location.href = "/login";
        }, 2000);
      }
    } catch (error: any) {
      setErrors({ general: error.message || "パスワードの変更に失敗しました" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout
      title="パスワードリセット - CSR Lambda API System"
      description="パスワードをリセットしてアカウントにアクセスしてください"
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

          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">{step === "request" ? "パスワードリセット" : "新しいパスワード設定"}</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {step === "request"
              ? "メールアドレスを入力してリセットコードを受け取ってください"
              : "メールに送信された確認コードと新しいパスワードを入力してください"}
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

            {step === "request" ? (
              /* パスワードリセット要求フォーム */
              <form onSubmit={handleForgotSubmit} className="space-y-6">
                <Input
                  label="メールアドレス"
                  type="email"
                  name="email"
                  value={forgotForm.email}
                  onChange={handleForgotInputChange}
                  error={errors.email}
                  fullWidth
                  autoComplete="email"
                  placeholder="your@example.com"
                />

                <Button type="submit" loading={isLoading} fullWidth size="lg">
                  リセットコードを送信
                </Button>
              </form>
            ) : (
              /* パスワードリセット確認フォーム */
              <form onSubmit={handleResetSubmit} className="space-y-6">
                <Input
                  label="確認コード"
                  type="text"
                  name="confirmationCode"
                  value={resetForm.confirmationCode}
                  onChange={handleResetInputChange}
                  error={errors.confirmationCode}
                  fullWidth
                  placeholder="メールに送信された6桁のコード"
                />

                <Input
                  label="新しいパスワード"
                  type="password"
                  name="newPassword"
                  value={resetForm.newPassword}
                  onChange={handleResetInputChange}
                  error={errors.newPassword}
                  fullWidth
                  autoComplete="new-password"
                  placeholder="8文字以上の新しいパスワード"
                />

                <Input
                  label="パスワード確認"
                  type="password"
                  name="confirmPassword"
                  value={resetForm.confirmPassword}
                  onChange={handleResetInputChange}
                  error={errors.confirmPassword}
                  fullWidth
                  autoComplete="new-password"
                  placeholder="新しいパスワードを再入力"
                />

                <Button type="submit" loading={isLoading} fullWidth size="lg">
                  パスワードを変更
                </Button>

                <div className="text-center">
                  <button type="button" onClick={() => setStep("request")} className="text-sm text-blue-600 hover:text-blue-500">
                    ← メールアドレス入力に戻る
                  </button>
                </div>
              </form>
            )}

            {/* 戻るリンク */}
            <div className="mt-6 text-center">
              <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
                ← ログインページに戻る
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
}

// ゲストガードを適用（認証済みユーザーはダッシュボードにリダイレクト）
export default withGuestGuard(ForgotPassword);
