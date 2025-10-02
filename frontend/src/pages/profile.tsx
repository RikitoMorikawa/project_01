import React, { useState } from "react";
import { Layout } from "@/components/layout";
import { Card, Button, Input } from "@/components/ui";
import { withAuthGuard } from "@/components/auth/AuthGuard";
import { useAuth } from "@/hooks/use-auth";

interface UserProfile {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  bio: string;
  avatarUrl?: string;
}

function Profile() {
  const { user, logout } = useAuth();

  const [profile, setProfile] = useState<UserProfile>({
    username: user?.username || "",
    email: user?.email || "",
    firstName: "",
    lastName: "",
    bio: "",
  });

  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setProfile((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // TODO: 実際のAPI呼び出しを実装
      // await apiClient.put('/api/v1/profile', profile);

      // 仮の処理
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setEditing(false);
      console.log("プロフィール更新完了:", profile);
    } catch (error) {
      console.error("プロフィール更新エラー:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    // 元の値に戻す処理があればここに追加
  };

  return (
    <Layout
      title="プロフィール - CSR Lambda API System"
      headerProps={{
        isAuthenticated: true,
        user: user,
        onLogout: logout,
      }}
    >
      <div className="container py-8">
        <div className="max-w-2xl mx-auto">
          {/* ヘッダー */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">プロフィール</h1>
            <p className="text-gray-600">アカウント情報を管理できます。</p>
          </div>

          {/* プロフィールカード */}
          <Card className="mb-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">基本情報</h2>
              {!editing ? (
                <Button variant="outline" onClick={() => setEditing(true)}>
                  編集
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button variant="outline" onClick={handleCancel} disabled={loading}>
                    キャンセル
                  </Button>
                  <Button onClick={handleSave} loading={loading}>
                    保存
                  </Button>
                </div>
              )}
            </div>

            {/* アバター */}
            <div className="flex items-center mb-6">
              <div className="w-20 h-20 bg-gray-300 rounded-full flex items-center justify-center mr-4">
                {profile.avatarUrl ? (
                  <img src={profile.avatarUrl} alt="プロフィール画像" className="w-20 h-20 rounded-full object-cover" />
                ) : (
                  <span className="text-2xl font-bold text-gray-600">
                    {profile.firstName.charAt(0)}
                    {profile.lastName.charAt(0)}
                  </span>
                )}
              </div>
              {editing && (
                <Button variant="outline" size="sm">
                  画像を変更
                </Button>
              )}
            </div>

            {/* フォーム */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input label="ユーザー名" name="username" value={profile.username} onChange={handleInputChange} disabled={!editing} fullWidth />

              <Input label="メールアドレス" name="email" type="email" value={profile.email} onChange={handleInputChange} disabled={!editing} fullWidth />

              <Input label="姓" name="lastName" value={profile.lastName} onChange={handleInputChange} disabled={!editing} fullWidth />

              <Input label="名" name="firstName" value={profile.firstName} onChange={handleInputChange} disabled={!editing} fullWidth />
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">自己紹介</label>
              <textarea
                name="bio"
                value={profile.bio}
                onChange={handleInputChange}
                disabled={!editing}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="自己紹介を入力してください"
              />
            </div>
          </Card>

          {/* セキュリティ設定 */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">セキュリティ設定</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b border-gray-200">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">パスワード</h3>
                  <p className="text-sm text-gray-500">最終更新: 2024年1月15日</p>
                </div>
                <Button variant="outline" size="sm">
                  変更
                </Button>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-gray-200">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">二要素認証</h3>
                  <p className="text-sm text-gray-500">アカウントのセキュリティを強化</p>
                </div>
                <Button variant="outline" size="sm">
                  設定
                </Button>
              </div>

              <div className="flex items-center justify-between py-3">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">ログインセッション</h3>
                  <p className="text-sm text-gray-500">他のデバイスでのログインを管理</p>
                </div>
                <Button variant="outline" size="sm">
                  管理
                </Button>
              </div>
            </div>
          </Card>

          {/* 危険な操作 */}
          <Card className="mt-6 border-red-200">
            <h2 className="text-xl font-semibold text-red-600 mb-6">危険な操作</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between py-3">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">アカウント削除</h3>
                  <p className="text-sm text-gray-500">アカウントとすべてのデータが完全に削除されます。この操作は取り消せません。</p>
                </div>
                <Button variant="danger" size="sm">
                  削除
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
// 認証ガードを適用（未認証ユーザーはログインページにリダイレクト）
export default withAuthGuard(Profile);
