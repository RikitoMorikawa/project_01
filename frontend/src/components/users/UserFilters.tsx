import React, { useState } from "react";
import { Input, Button, Card } from "@/components/ui";

export interface UserFiltersProps {
  onSearch: (query: string) => void;
  onFilter: (filters: UserFilterOptions) => void;
  onReset: () => void;
  loading?: boolean;
}

export interface UserFilterOptions {
  search: string;
  sortBy: "username" | "email" | "createdAt" | "updatedAt";
  sortOrder: "asc" | "desc";
  status?: "active" | "inactive" | "all";
}

const UserFilters: React.FC<UserFiltersProps> = ({ onSearch, onFilter, onReset, loading = false }) => {
  const [filters, setFilters] = useState<UserFilterOptions>({
    search: "",
    sortBy: "createdAt",
    sortOrder: "desc",
    status: "all",
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFilters((prev) => ({ ...prev, search: value }));

    // リアルタイム検索（デバウンス処理は親コンポーネントで実装）
    onSearch(value);
  };

  const handleFilterChange = (key: keyof UserFilterOptions, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilter(newFilters);
  };

  const handleReset = () => {
    const resetFilters: UserFilterOptions = {
      search: "",
      sortBy: "createdAt",
      sortOrder: "desc",
      status: "all",
    };
    setFilters(resetFilters);
    onReset();
  };

  return (
    <Card>
      <div className="space-y-4">
        {/* 基本検索 */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="ユーザー名またはメールアドレスで検索..."
              value={filters.search}
              onChange={handleSearchChange}
              startIcon={
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
              fullWidth
            />
          </div>

          <div className="flex space-x-2">
            <Button variant="outline" onClick={() => setShowAdvanced(!showAdvanced)} className="whitespace-nowrap">
              {showAdvanced ? "簡単検索" : "詳細検索"}
            </Button>

            <Button variant="ghost" onClick={handleReset} disabled={loading} className="whitespace-nowrap">
              リセット
            </Button>
          </div>
        </div>

        {/* 詳細フィルター */}
        {showAdvanced && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            {/* ソート項目 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ソート項目</label>
              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange("sortBy", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="createdAt">登録日</option>
                <option value="updatedAt">更新日</option>
                <option value="username">ユーザー名</option>
                <option value="email">メールアドレス</option>
              </select>
            </div>

            {/* ソート順 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ソート順</label>
              <select
                value={filters.sortOrder}
                onChange={(e) => handleFilterChange("sortOrder", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="desc">降順</option>
                <option value="asc">昇順</option>
              </select>
            </div>

            {/* ステータス */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange("status", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">すべて</option>
                <option value="active">アクティブ</option>
                <option value="inactive">非アクティブ</option>
              </select>
            </div>
          </div>
        )}

        {/* 検索結果サマリー */}
        {filters.search && (
          <div className="text-sm text-gray-600 bg-blue-50 px-3 py-2 rounded-md">
            「{filters.search}」で検索中
            {loading && <span className="ml-2">検索中...</span>}
          </div>
        )}
      </div>
    </Card>
  );
};

export default UserFilters;
