import React, { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { Layout } from "@/components/layout";
import { Button, Loading, ErrorDisplay } from "@/components/ui";
import { UserProfile } from "@/components/users";
import { useUser, useUpdateUser, useDeleteUser } from "@/hooks/use-users";
import { withAuthGuard } from "@/components/auth/AuthGuard";
import { UserProfile as UserProfileType } from "@/types";

const UserDetailPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const userId = typeof id === "string" ? parseInt(id, 10) : null;

  const [profile, setProfile] = useState<UserProfileType | null>(null);

  // ユーザー情報を取得
  const { data: user, isLoading: loading, error: userError } = useUser(userId || 0);
  const updateUserMutation = useUpdateUser();
  const deleteUserMutation = useDeleteUser();

  const error = userError?.message || null;

  const handleSaveProfile = async (profileData: Partial<UserProfileType>) => {
    if (!userId) return;

    try {
      // 実際の実装では、プロフィール更新APIを呼び出す
      // await updateUserMutation.mutateAsync({ id: userId, data: profileData });
      console.log("Profile update:", profileData);

      // 仮のプロフィール更新
      setProfile((prev) => ({ ...prev, ...profileData } as UserProfileType));
    } catch (error: any) {
      throw new Error(error.message || "プロフィールの保存に失敗しました");
    }
  };

  const handleDeleteUser = async () => {
    if (!user) return;

    const confirmed = window.confirm(`${user.username} を削除してもよろしいですか？\n\nこの操作は取り消すことができません。`);

    if (confirmed) {
      try {
        await deleteUserMutation.mutateAsync(user.id);
        router.push("/users");
      } catch (error: any) {
        alert(error.message || "ユーザーの削除に失敗しました");
      }
    }
  };

  if (loading) {
    return (
      <Layout
        title="ユーザー詳細 | CSR Lambda API"
        description="ユーザーの詳細情報"
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
      title={`${user.username} | ユーザー詳細 | CSR Lambda API`}
      description={`${user.username} のプロフィール情報`}
      headerProps={{
        title: "CSR Lambda API",
        showAuth: true,
        showNavigation: true,
      }}
    >
      <div className="container mx-auto py-8">
        {/* ページヘッダー */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
                <Link href="/users" className="hover:text-gray-700">
                  ユーザー管理
                </Link>
                <span>/</span>
                <span className="text-gray-900">{user.username}</span>
              </nav>

              <h1 className="text-3xl font-bold text-gray-900">ユーザー詳細</h1>
              <p className="text-gray-600 mt-1">{user.username} のプロフィール情報</p>
            </div>

            <div className="flex space-x-3">
              <Link href={`/users/${user.id}/edit`}>
                <Button variant="outline">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                  編集
                </Button>
              </Link>

              <Button variant="danger" onClick={handleDeleteUser} loading={deleteUserMutation.isPending}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                削除
              </Button>
            </div>
          </div>
        </div>

        {/* ユーザープロフィール */}
        <UserProfile user={user} profile={profile || undefined} onSave={handleSaveProfile} editable={true} />
      </div>
    </Layout>
  );
};

// 認証ガードを適用
export default withAuthGuard(UserDetailPage);
