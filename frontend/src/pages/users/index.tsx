import React, { useState, useCallback } from "react";
import { Layout } from "@/components/layout";
import { Button, Card } from "@/components/ui";
import { UserList, UserFilters, UserFilterOptions } from "@/components/users";
import { useUsers, useDeleteUser } from "@/hooks/use-users";
import { withAuthGuard } from "@/components/auth/AuthGuard";
import { User } from "@/types";
import Link from "next/link";

const UsersPage: React.FC = () => {
  const [filters, setFilters] = useState<UserFilterOptions>({
    search: "",
    sortBy: "createdAt",
    sortOrder: "desc",
    status: "all",
  });
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // ユーザー一覧を取得
  const {
    data: usersData,
    isLoading: loading,
    error: usersError,
    refetch,
  } = useUsers({
    search: filters.search,
    page: 1,
    page_size: 20,
  });
  const deleteUserMutation = useDeleteUser();

  const users = usersData?.data || [];
  const hasMore = usersData ? usersData.page < usersData.total_pages : false;
  const error = usersError?.message || null;

  const handleSearch = useCallback((query: string) => {
    setFilters((prev) => ({ ...prev, search: query }));
  }, []);

  const handleFilter = useCallback((newFilters: UserFilterOptions) => {
    setFilters(newFilters);
  }, []);

  const handleReset = useCallback(() => {
    const resetFilters: UserFilterOptions = {
      search: "",
      sortBy: "createdAt",
      sortOrder: "desc",
      status: "all",
    };
    setFilters(resetFilters);
    refetch();
  }, [refetch]);

  const handleEdit = (user: User) => {
    // ユーザー編集ページに遷移
    window.location.href = `/users/${user.id}/edit`;
  };

  const handleDelete = async (user: User) => {
    if (window.confirm(`${user.username} を削除してもよろしいですか？`)) {
      try {
        await deleteUserMutation.mutateAsync(user.id);
        // 成功時は自動的にリストが更新される
      } catch (error) {
        console.error("ユーザー削除エラー:", error);
        alert("ユーザーの削除に失敗しました");
      }
    }
  };

  const handleLoadMore = () => {
    // 追加データの読み込み処理（実装は省略）
    console.log("Load more users");
  };

  return (
    <Layout
      title="ユーザー管理 | CSR Lambda API"
      description="システムに登録されているユーザーの一覧と管理"
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
              <h1 className="text-3xl font-bold text-gray-900">ユーザー管理</h1>
              <p className="text-gray-600 mt-1">システムに登録されているユーザーの一覧と管理</p>
            </div>

            <div className="flex space-x-3">
              <Button variant="outline" onClick={() => refetch()}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                更新
              </Button>

              <Link href="/users/new">
                <Button>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  新規ユーザー
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* 統計情報 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">総ユーザー数</p>
                <p className="text-2xl font-semibold text-gray-900">{usersData?.total || 0}</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">アクティブユーザー</p>
                <p className="text-2xl font-semibold text-gray-900">{users.length}</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">今月の新規登録</p>
                <p className="text-2xl font-semibold text-gray-900">0</p>
              </div>
            </div>
          </Card>
        </div>

        {/* 検索・フィルター */}
        <div className="mb-6">
          <UserFilters onSearch={handleSearch} onFilter={handleFilter} onReset={handleReset} loading={loading} />
        </div>

        {/* ユーザー一覧 */}
        <UserList
          users={users}
          loading={loading}
          error={error || undefined}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onLoadMore={handleLoadMore}
          hasMore={hasMore}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
        />
      </div>
    </Layout>
  );
};

// 認証ガードを適用（未認証ユーザーはログインページにリダイレクト）
export default withAuthGuard(UsersPage);
