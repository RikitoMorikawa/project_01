import React from "react";
import Link from "next/link";
import { Card, Button } from "@/components/ui";
import { User } from "@/types";

export interface UserCardProps {
  user: User;
  onEdit?: (user: User) => void;
  onDelete?: (user: User) => void;
  showActions?: boolean;
  compact?: boolean;
}

const UserCard: React.FC<UserCardProps> = ({ user, onEdit, onDelete, showActions = true, compact = false }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ja-JP", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getInitials = (username: string) => {
    return username.charAt(0).toUpperCase();
  };

  if (compact) {
    return (
      <Card padding="sm" className="hover:shadow-md transition-shadow">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-semibold">{getInitials(user.username)}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user.username}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
          {showActions && (
            <div className="flex space-x-1">
              <Button size="sm" variant="ghost" onClick={() => onEdit?.(user)}>
                編集
              </Button>
            </div>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="flex items-start space-x-4">
        {/* アバター */}
        <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
          <span className="text-white text-xl font-bold">{getInitials(user.username)}</span>
        </div>

        {/* ユーザー情報 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900 truncate">{user.username}</h3>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">アクティブ</span>
          </div>

          <p className="text-gray-600 mb-2">{user.email}</p>

          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center space-x-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <span>登録日: {formatDate(user.createdAt)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>最終更新: {formatDate(user.updatedAt)}</span>
            </div>
          </div>
        </div>

        {/* アクション */}
        {showActions && (
          <div className="flex flex-col space-y-2">
            <Link href={`/users/${user.id}`}>
              <Button size="sm" variant="outline" className="w-full">
                詳細
              </Button>
            </Link>
            {onEdit && (
              <Button size="sm" variant="ghost" onClick={() => onEdit(user)}>
                編集
              </Button>
            )}
            {onDelete && (
              <Button size="sm" variant="danger" onClick={() => onDelete(user)}>
                削除
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default UserCard;
