import React, { useState } from "react";
import { Card, Button, Input, Form, Loading, ErrorDisplay } from "@/components/ui";
import { User, UserProfile as UserProfileType } from "@/types";

export interface UserProfileProps {
  user: User;
  profile?: UserProfileType;
  loading?: boolean;
  error?: string;
  onSave?: (profileData: Partial<UserProfileType>) => Promise<void>;
  onCancel?: () => void;
  editable?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({ user, profile, loading = false, error, onSave, onCancel, editable = false }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    firstName: profile?.firstName || "",
    lastName: profile?.lastName || "",
    bio: profile?.bio || "",
    avatarUrl: profile?.avatarUrl || "",
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!onSave) return;

    try {
      setSaveLoading(true);
      setSaveError(null);

      await onSave(formData);
      setIsEditing(false);
    } catch (error: any) {
      setSaveError(error.message || "プロフィールの保存に失敗しました");
    } finally {
      setSaveLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      firstName: profile?.firstName || "",
      lastName: profile?.lastName || "",
      bio: profile?.bio || "",
      avatarUrl: profile?.avatarUrl || "",
    });
    setIsEditing(false);
    setSaveError(null);
    onCancel?.();
  };

  const getInitials = (username: string) => {
    return username.charAt(0).toUpperCase();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <Card>
        <div className="flex justify-center py-12">
          <Loading size="lg" text="プロフィールを読み込み中..." />
        </div>
      </Card>
    );
  }

  if (error) {
    return <ErrorDisplay type="card" title="プロフィールの読み込みに失敗しました" message={error} showRetry onRetry={() => window.location.reload()} />;
  }

  return (
    <div className="space-y-6">
      {/* プロフィールヘッダー */}
      <Card>
        <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-4 sm:space-y-0 sm:space-x-6">
          {/* アバター */}
          <div className="relative">
            {formData.avatarUrl ? (
              <img src={formData.avatarUrl} alt={user.username} className="w-24 h-24 rounded-full object-cover" />
            ) : (
              <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-3xl font-bold">{getInitials(user.username)}</span>
              </div>
            )}

            {isEditing && (
              <button className="absolute bottom-0 right-0 bg-blue-500 text-white rounded-full p-2 hover:bg-blue-600 transition">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            )}
          </div>

          {/* ユーザー情報 */}
          <div className="flex-1">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {formData.firstName || formData.lastName ? `${formData.firstName} ${formData.lastName}`.trim() : user.username}
                </h1>
                <p className="text-gray-600">@{user.username}</p>
                <p className="text-sm text-gray-500">{user.email}</p>
              </div>

              {editable && (
                <div className="mt-4 sm:mt-0">
                  {isEditing ? (
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline" onClick={handleCancel}>
                        キャンセル
                      </Button>
                      <Button size="sm" onClick={handleSave} loading={saveLoading}>
                        保存
                      </Button>
                    </div>
                  ) : (
                    <Button size="sm" onClick={() => setIsEditing(true)}>
                      プロフィール編集
                    </Button>
                  )}
                </div>
              )}
            </div>

            {/* 自己紹介 */}
            {(formData.bio || isEditing) && (
              <div className="mt-4">
                {isEditing ? (
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleInputChange}
                    placeholder="自己紹介を入力してください..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-700">{formData.bio}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* プロフィール詳細 */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">プロフィール詳細</h2>

        {saveError && (
          <div className="mb-4">
            <ErrorDisplay type="inline" message={saveError} />
          </div>
        )}

        {isEditing ? (
          <Form onSubmit={handleSave} loading={saveLoading} showSubmitButton={false}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="名前" name="firstName" value={formData.firstName} onChange={handleInputChange} placeholder="名前を入力" fullWidth />

              <Input label="姓" name="lastName" value={formData.lastName} onChange={handleInputChange} placeholder="姓を入力" fullWidth />
            </div>

            <Input
              label="アバター画像URL"
              name="avatarUrl"
              type="url"
              value={formData.avatarUrl}
              onChange={handleInputChange}
              placeholder="https://example.com/avatar.jpg"
              fullWidth
            />
          </Form>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">名前</label>
                <p className="mt-1 text-sm text-gray-900">{formData.firstName || "未設定"}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">姓</label>
                <p className="mt-1 text-sm text-gray-900">{formData.lastName || "未設定"}</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">メールアドレス</label>
              <p className="mt-1 text-sm text-gray-900">{user.email}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">ユーザーID</label>
              <p className="mt-1 text-sm text-gray-900">{user.cognitoUserId}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">登録日</label>
                <p className="mt-1 text-sm text-gray-900">{formatDate(user.createdAt)}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">最終更新</label>
                <p className="mt-1 text-sm text-gray-900">{formatDate(user.updatedAt)}</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* アクティビティ履歴 */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">最近のアクティビティ</h2>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 text-sm">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-gray-600">プロフィールを更新しました</span>
            <span className="text-gray-400">{formatDate(user.updatedAt)}</span>
          </div>
          <div className="flex items-center space-x-3 text-sm">
            <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            <span className="text-gray-600">アカウントを作成しました</span>
            <span className="text-gray-400">{formatDate(user.createdAt)}</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default UserProfile;
