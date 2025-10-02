import React, { useState } from "react";
import { Button, Loading, ErrorDisplay } from "@/components/ui";
import UserCard from "./UserCard";
import { User } from "@/types";

export interface UserListProps {
  users: User[];
  loading?: boolean;
  error?: string;
  onEdit?: (user: User) => void;
  onDelete?: (user: User) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  viewMode?: "grid" | "list";
  onViewModeChange?: (mode: "grid" | "list") => void;
}

const UserList: React.FC<UserListProps> = ({
  users,
  loading = false,
  error,
  onEdit,
  onDelete,
  onLoadMore,
  hasMore = false,
  viewMode = "grid",
  onViewModeChange,
}) => {
  const [selectedUsers, setSelectedUsers] = useState<Set<number>>(new Set());

  const handleSelectUser = (userId: number) => {
    const newSelected = new Set(selectedUsers);
    if (newSelected.has(userId)) {
      newSelected.delete(userId);
    } else {
      newSelected.add(userId);
    }
    setSelectedUsers(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedUsers.size === users.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(users.map((user) => user.id)));
    }
  };

  const handleBulkDelete = () => {
    if (selectedUsers.size > 0 && onDelete) {
      const usersToDelete = users.filter((user) => selectedUsers.has(user.id));
      // 実際の実装では、バルク削除APIを呼び出す
      console.log("Bulk delete users:", usersToDelete);
      setSelectedUsers(new Set());
    }
  };

  if (error) {
    return <ErrorDisplay type="card" title="ユーザー一覧の読み込みに失敗しました" message={error} showRetry onRetry={() => window.location.reload()} />;
  }

  return (
    <div className="space-y-4">
      {/* ツールバー */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            {users.length} 件のユーザー
            {selectedUsers.size > 0 && ` (${selectedUsers.size} 件選択中)`}
          </span>

          {selectedUsers.size > 0 && (
            <div className="flex space-x-2">
              <Button size="sm" variant="danger" onClick={handleBulkDelete}>
                選択したユーザーを削除
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setSelectedUsers(new Set())}>
                選択解除
              </Button>
            </div>
          )}
        </div>

        {/* 表示モード切り替え */}
        {onViewModeChange && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">表示:</span>
            <div className="flex border border-gray-300 rounded-md">
              <button
                onClick={() => onViewModeChange("grid")}
                className={`px-3 py-1 text-sm rounded-l-md ${viewMode === "grid" ? "bg-blue-500 text-white" : "bg-white text-gray-700 hover:bg-gray-50"}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                  />
                </svg>
              </button>
              <button
                onClick={() => onViewModeChange("list")}
                className={`px-3 py-1 text-sm rounded-r-md ${viewMode === "list" ? "bg-blue-500 text-white" : "bg-white text-gray-700 hover:bg-gray-50"}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 一括選択 */}
      {users.length > 0 && (
        <div className="flex items-center space-x-2 py-2 border-b border-gray-200">
          <input
            type="checkbox"
            checked={selectedUsers.size === users.length && users.length > 0}
            onChange={handleSelectAll}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label className="text-sm text-gray-600">すべて選択</label>
        </div>
      )}

      {/* ユーザー一覧 */}
      {users.length === 0 && !loading ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">ユーザーが見つかりません</h3>
          <p className="mt-1 text-sm text-gray-500">検索条件を変更してみてください。</p>
        </div>
      ) : (
        <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" : "space-y-3"}>
          {users.map((user) => (
            <div key={user.id} className="relative">
              {/* 選択チェックボックス */}
              <div className="absolute top-2 left-2 z-10">
                <input
                  type="checkbox"
                  checked={selectedUsers.has(user.id)}
                  onChange={() => handleSelectUser(user.id)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              <UserCard user={user} onEdit={onEdit} onDelete={onDelete} compact={viewMode === "list"} />
            </div>
          ))}
        </div>
      )}

      {/* ローディング */}
      {loading && (
        <div className="flex justify-center py-8">
          <Loading size="md" text="ユーザーを読み込み中..." />
        </div>
      )}

      {/* もっと読み込む */}
      {hasMore && !loading && (
        <div className="flex justify-center pt-6">
          <Button variant="outline" onClick={onLoadMore}>
            さらに読み込む
          </Button>
        </div>
      )}
    </div>
  );
};

export default UserList;
