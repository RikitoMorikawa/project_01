/**
 * データ管理ページ
 *
 * ユーザーの個人データ管理機能を提供
 * GDPR の権利（アクセス、修正、削除、ポータビリティ）に対応
 */

import React, { useState, useEffect } from "react";
import Head from "next/head";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import ConsentManager from "@/components/auth/ConsentManager";

// データエクスポート結果の型定義
interface ExportData {
  export_info: {
    exported_at: string;
    exported_by_user_id: number;
    data_format: string;
  };
  user_data: any;
  profile_data: any;
  consent_history: any;
  access_history: any[];
}

// アクセス履歴の型定義
interface AccessHistoryItem {
  id: number;
  action: string;
  data_category: string;
  details: any;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

const DataManagementPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<"overview" | "consents" | "access-history" | "export" | "delete">("overview");
  const [loading, setLoading] = useState(false);
  const [exportData, setExportData] = useState<ExportData | null>(null);
  const [accessHistory, setAccessHistory] = useState<AccessHistoryItem[]>([]);
  const [consentData, setConsentData] = useState<any>({});

  // 認証チェック
  useEffect(() => {
    if (!isAuthenticated) {
      // ログインページにリダイレクト
      window.location.href = "/login";
    }
  }, [isAuthenticated]);

  // 同意状況の取得
  const fetchConsentStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/v1/consent/status", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConsentData(data.consents);
      }
    } catch (error) {
      console.error("同意状況の取得に失敗しました:", error);
    } finally {
      setLoading(false);
    }
  };

  // アクセス履歴の取得
  const fetchAccessHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/v1/consent/history", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAccessHistory(data);
      }
    } catch (error) {
      console.error("アクセス履歴の取得に失敗しました:", error);
    } finally {
      setLoading(false);
    }
  };

  // データエクスポート
  const handleDataExport = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/v1/data/export", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setExportData(data);

        // JSON ファイルとしてダウンロード
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `user-data-export-${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        alert("データのエクスポートが完了しました。ファイルがダウンロードされます。");
      } else {
        alert("データエクスポートに失敗しました。");
      }
    } catch (error) {
      console.error("データエクスポートエラー:", error);
      alert("データエクスポートに失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // データ削除リクエスト
  const handleDataDeletionRequest = async () => {
    const confirmed = window.confirm(
      "アカウントとすべての個人データの削除をリクエストしますか？\n" + "この操作は取り消すことができません。\n" + "削除処理には最大30日かかる場合があります。"
    );

    if (!confirmed) return;

    try {
      setLoading(true);
      const response = await fetch("/api/v1/data/deletion-request", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.message);
      } else {
        alert("削除リクエストの送信に失敗しました。");
      }
    } catch (error) {
      console.error("削除リクエストエラー:", error);
      alert("削除リクエストの送信に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // 初期データ読み込み
  useEffect(() => {
    if (isAuthenticated) {
      fetchConsentStatus();
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <div>認証中...</div>;
  }

  return (
    <>
      <Head>
        <title>データ管理 | CSR Lambda API システム</title>
        <meta name="description" content="個人データの管理・設定ページ" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* ヘッダー */}
          <div className="bg-white shadow rounded-lg p-8 mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">データ管理</h1>
            <p className="text-gray-600">
              あなたの個人データの管理と設定を行えます。 GDPR に基づく権利（アクセス、修正、削除、ポータビリティ）を行使できます。
            </p>
          </div>

          {/* タブナビゲーション */}
          <div className="bg-white shadow rounded-lg mb-8">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 px-6">
                {[
                  { id: "overview", label: "概要", icon: "📊" },
                  { id: "consents", label: "同意設定", icon: "✅" },
                  { id: "access-history", label: "アクセス履歴", icon: "📋" },
                  { id: "export", label: "データエクスポート", icon: "📥" },
                  { id: "delete", label: "データ削除", icon: "🗑️" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id ? "border-blue-500 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* タブコンテンツ */}
          <div className="space-y-8">
            {/* 概要タブ */}
            {activeTab === "overview" && (
              <div className="bg-white shadow rounded-lg p-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">データ管理概要</h2>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">あなたの権利</h3>

                    <div className="space-y-3">
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mt-1">
                          <span className="text-blue-600 text-sm">👁️</span>
                        </div>
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900">アクセス権</h4>
                          <p className="text-sm text-gray-600">保存されている個人データを確認できます</p>
                        </div>
                      </div>

                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center mt-1">
                          <span className="text-green-600 text-sm">✏️</span>
                        </div>
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900">修正権</h4>
                          <p className="text-sm text-gray-600">不正確な個人データの修正を要求できます</p>
                        </div>
                      </div>

                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-6 h-6 bg-red-100 rounded-full flex items-center justify-center mt-1">
                          <span className="text-red-600 text-sm">🗑️</span>
                        </div>
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900">削除権（忘れられる権利）</h4>
                          <p className="text-sm text-gray-600">個人データの削除を要求できます</p>
                        </div>
                      </div>

                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center mt-1">
                          <span className="text-purple-600 text-sm">📦</span>
                        </div>
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900">データポータビリティ権</h4>
                          <p className="text-sm text-gray-600">構造化されたデータの取得・移転ができます</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">アカウント情報</h3>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <dl className="space-y-2">
                        <div>
                          <dt className="text-sm font-medium text-gray-500">ユーザー名</dt>
                          <dd className="text-sm text-gray-900">{user?.username}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">メールアドレス</dt>
                          <dd className="text-sm text-gray-900">{user?.email}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">アカウント作成日</dt>
                          <dd className="text-sm text-gray-900">{user?.createdAt ? new Date(user.createdAt).toLocaleDateString("ja-JP") : "不明"}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 同意設定タブ */}
            {activeTab === "consents" && (
              <ConsentManager
                mode="settings"
                initialConsents={consentData}
                onConsentChange={(consentType, consented) => {
                  // 同意状況の更新をAPIに送信
                  fetch("/api/v1/consent", {
                    method: "POST",
                    headers: {
                      Authorization: `Bearer ${localStorage.getItem("token")}`,
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      consent_type: consentType,
                      consent_version: "1.0",
                      consented,
                    }),
                  }).then(() => {
                    fetchConsentStatus(); // 同意状況を再取得
                  });
                }}
              />
            )}

            {/* アクセス履歴タブ */}
            {activeTab === "access-history" && (
              <div className="bg-white shadow rounded-lg p-8">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">アクセス履歴</h2>
                  <button
                    onClick={fetchAccessHistory}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? "読み込み中..." : "更新"}
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日時</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">アクション</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">データカテゴリ</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IPアドレス</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {accessHistory.map((item) => (
                        <tr key={item.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{new Date(item.created_at).toLocaleString("ja-JP")}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.action}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.data_category}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.ip_address}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {accessHistory.length === 0 && <div className="text-center py-8 text-gray-500">アクセス履歴がありません</div>}
                </div>
              </div>
            )}

            {/* データエクスポートタブ */}
            {activeTab === "export" && (
              <div className="bg-white shadow rounded-lg p-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">データエクスポート</h2>

                <div className="space-y-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-blue-900 mb-2">データポータビリティ権の行使</h3>
                    <p className="text-blue-800 text-sm">
                      GDPR に基づき、あなたの個人データを構造化された形式で取得できます。
                      エクスポートされるデータには、アカウント情報、プロファイル、同意履歴、アクセス履歴が含まれます。
                    </p>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">エクスポート内容</h3>
                    <ul className="list-disc list-inside text-gray-700 space-y-2">
                      <li>ユーザーアカウント情報（メールアドレス、ユーザー名等）</li>
                      <li>プロファイル情報（氏名、自己紹介等）</li>
                      <li>同意履歴（プライバシーポリシー、利用規約等への同意状況）</li>
                      <li>アクセス履歴（直近100件のデータアクセス記録）</li>
                    </ul>
                  </div>

                  <div className="flex space-x-4">
                    <button
                      onClick={handleDataExport}
                      disabled={loading}
                      className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {loading ? "エクスポート中..." : "データをエクスポート"}
                    </button>
                  </div>

                  {exportData && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="text-green-800 font-medium mb-2">エクスポート完了</h4>
                      <p className="text-green-700 text-sm">
                        データのエクスポートが完了しました。 エクスポート日時: {new Date(exportData.export_info.exported_at).toLocaleString("ja-JP")}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* データ削除タブ */}
            {activeTab === "delete" && (
              <div className="bg-white shadow rounded-lg p-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">データ削除</h2>

                <div className="space-y-6">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-red-900 mb-2">⚠️ 重要な注意事項</h3>
                    <div className="text-red-800 text-sm space-y-2">
                      <p>この操作により、あなたのアカウントとすべての個人データが削除されます。</p>
                      <p>削除されたデータは復元できません。</p>
                      <p>削除処理には最大30日かかる場合があります。</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">削除されるデータ</h3>
                    <ul className="list-disc list-inside text-gray-700 space-y-2">
                      <li>ユーザーアカウント情報</li>
                      <li>プロファイル情報</li>
                      <li>同意履歴</li>
                      <li>アクセス履歴</li>
                      <li>その他すべての個人データ</li>
                    </ul>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="text-yellow-800 font-medium mb-2">削除前の確認事項</h4>
                    <div className="text-yellow-700 text-sm space-y-1">
                      <p>• 必要なデータは事前にエクスポートしてください</p>
                      <p>• 削除後はサービスを利用できなくなります</p>
                      <p>• 法的要件により一部データは匿名化して保持される場合があります</p>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-gray-200">
                    <button
                      onClick={handleDataDeletionRequest}
                      disabled={loading}
                      className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                    >
                      {loading ? "処理中..." : "データ削除をリクエスト"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* フッター */}
          <div className="bg-white shadow rounded-lg p-6 text-center mt-8">
            <p className="text-gray-600 mb-4">データ管理に関するご質問やサポートが必要な場合は、お気軽にお問い合わせください。</p>

            <div className="flex justify-center space-x-4">
              <Link href="/" className="text-blue-600 hover:text-blue-500">
                ホームに戻る
              </Link>
              <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
                プライバシーポリシー
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default DataManagementPage;
