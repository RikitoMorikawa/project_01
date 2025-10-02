import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { Layout } from "@/components/layout";
import { Button, Card, Form, Input, Loading, ErrorDisplay } from "@/components/ui";
import { useUser, useUpdateUser } from "@/hooks/use-users";
import { withAuthGuard } from "@/components/auth/AuthGuard";
import { User, UserProfile as UserProfileType } from "@/types";

interface UserEditForm {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  bio: string;
  avatarUrl: string;
}

const UserEditPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const userId = typeof id === "string" ? parseInt(id, 10) : null;

  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [formData, setFormData] = useState<UserEditForm>({
    username: "",
    email: "",
    firstName: "",
    lastName: "",
    bio: "",
    avatarUrl: "",
  });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // ユーザー情報を取得
  const { data: user, isLoading: loading, error: userError } = useUser(userId || 0);
  const updateUserMutation = useUpdateUser();

  const error = userError?.message || null;

  // ユーザーデータが取得できたらフォームを初期化
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        firstName: profile?.firstName || "",
        lastName: profile?.lastName || "",
        bio: profile?.bio || "",
        avatarUrl: profile?.avatarUrl || "",
      });
    }
  }, [user, profile]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user || !userId) return;

    try {
      setSaving(true);
      setSaveError(null);

      // ユーザー基本情報の更新
      await updateUserMutation.mutateAsync({
        id: userId,
        data: {
          username: formData.username,
          email: formData.email,
        },
      });

      // 成功時はユーザー詳細ページにリダイレクト
      router.push(`/users/${userId}`);
    } catch (error: any) {
      setSaveError(error.message || "ユーザー情報の保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.back();
  };

  if (loading) {
    return (
      <Layout
        title="ユーザー編集 | CSR Lambda API"
        description="ユーザー情報の編集"
        headerProps={{
          title: "CSR Lambda API",
          showAuth: true,
          showNavigation: true,
        }}
      >
        <div className="container mx-auto py-8">
          <div className="flex justify-center">
            <Loading size="lg" text="ユーザー情報を読み込み中..." />
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !user) {
    return (
      <Layout
        title="ユーザーが見つかりません | CSR Lambda API"
        description="指定されたユーザーが見つかりません"
        headerProps={{
          title: "CSR Lambda API",
          showAuth: true,
          showNavigation: true,
        }}
      >
        <div className="container mx-auto py-8">
          <ErrorDisplay type="page" title="ユーザーが見つかりません" message={error || "指定されたユーザーが存在しないか、アクセス権限がありません"}>
            <Link href="/users">
              <Button variant="primary" size="lg">
                ユーザー一覧に戻る
              </Button>
            </Link>
          </ErrorDisplay>
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title={`${user.username} を編集 | CSR Lambda API`}
      description={`${user.username} のプロフィール情報を編集`}
      headerProps={{
        title: "CSR Lambda API",
        showAuth: true,
        showNavigation: true,
      }}
    >
      <div className="container mx-auto py-8 max-w-2xl">
        {/* ページヘッダー */}
        <div className="mb-8">
          <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
            <Link href="/users" className="hover:text-gray-700">
              ユーザー管理
            </Link>
            <span>/</span>
            <Link href={`/users/${user.id}`} className="hover:text-gray-700">
              {user.username}
            </Link>
            <span>/</span>
            <span className="text-gray-900">編集</span>
          </nav>

          <h1 className="text-3xl font-bold text-gray-900">ユーザー編集</h1>
          <p className="text-gray-600 mt-1">{user.username} のプロフィール情報を編集</p>
        </div>

        {/* 編集フォーム */}
        <Card>
          <Form
            title="ユーザー情報"
            onSubmit={handleSubmit}
            loading={saving}
            error={saveError || undefined}
            submitLabel="保存"
            cancelLabel="キャンセル"
            showSubmitButton={true}
            showCancelButton={true}
            onCancel={handleCancel}
          >
            {/* 基本情報 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">基本情報</h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="ユーザー名"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                  fullWidth
                  placeholder="ユーザー名を入力"
                />

                <Input
                  label="メールアドレス"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  fullWidth
                  placeholder="メールアドレスを入力"
                />
              </div>
            </div>

            {/* プロフィール情報 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">プロフィール情報</h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="名前" name="firstName" value={formData.firstName} onChange={handleInputChange} fullWidth placeholder="名前を入力" />

                <Input label="姓" name="lastName" value={formData.lastName} onChange={handleInputChange} fullWidth placeholder="姓を入力" />
              </div>

              <Input
                label="アバター画像URL"
                name="avatarUrl"
                type="url"
                value={formData.avatarUrl}
                onChange={handleInputChange}
                fullWidth
                placeholder="https://example.com/avatar.jpg"
                helperText="プロフィール画像のURLを入力してください"
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">自己紹介</label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="自己紹介を入力してください..."
                />
              </div>
            </div>

            {/* システム情報（読み取り専用） */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">システム情報</h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">ユーザーID</label>
                  <p className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">{user.id}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Cognito ユーザーID</label>
                  <p className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">{user.cognitoUserId}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">登録日</label>
                  <p className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                    {new Date(user.createdAt).toLocaleDateString("ja-JP", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">最終更新</label>
                  <p className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                    {new Date(user.updatedAt).toLocaleDateString("ja-JP", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            </div>
          </Form>
        </Card>
      </div>
    </Layout>
  );
};

// 認証ガードを適用
export default withAuthGuard(UserEditPage);
