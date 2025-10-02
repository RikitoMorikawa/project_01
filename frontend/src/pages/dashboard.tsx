import React, { useState, useEffect } from "react";
import { Layout } from "@/components/layout";
import { Card, Button, Loading } from "@/components/ui";
import { withAuthGuard } from "@/components/auth/AuthGuard";
import { useAuth } from "@/hooks/use-auth";

// ダッシュボードのデータ型定義
interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  apiCalls: number;
  systemHealth: "healthy" | "warning" | "error";
}

interface RecentActivity {
  id: string;
  type: "login" | "api_call" | "user_created" | "system_event";
  message: string;
  timestamp: string;
}

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  // 認証されたユーザー情報を取得
  const { user, logout } = useAuth();

  useEffect(() => {
    // ダッシュボードデータを取得
    const fetchDashboardData = async () => {
      try {
        // TODO: 実際のAPI呼び出しを実装
        // const [statsResponse, activitiesResponse] = await Promise.all([
        //   apiClient.get('/api/v1/dashboard/stats'),
        //   apiClient.get('/api/v1/dashboard/activities')
        // ]);

        // 仮のデータ（開発用）
        await new Promise((resolve) => setTimeout(resolve, 1000));

        setStats({
          totalUsers: 1234,
          activeUsers: 89,
          apiCalls: 45678,
          systemHealth: "healthy",
        });

        setActivities([
          {
            id: "1",
            type: "login",
            message: "ユーザーがログインしました",
            timestamp: "2024-01-15T10:30:00Z",
          },
          {
            id: "2",
            type: "api_call",
            message: "API呼び出しが実行されました",
            timestamp: "2024-01-15T10:25:00Z",
          },
          {
            id: "3",
            type: "user_created",
            message: "新しいユーザーが作成されました",
            timestamp: "2024-01-15T10:20:00Z",
          },
          {
            id: "4",
            type: "system_event",
            message: "システムヘルスチェックが完了しました",
            timestamp: "2024-01-15T10:15:00Z",
          },
        ]);
      } catch (error) {
        console.error("ダッシュボードデータの取得に失敗:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "text-green-600";
      case "warning":
        return "text-yellow-600";
      case "error":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "login":
        return "👤";
      case "api_call":
        return "🔗";
      case "user_created":
        return "✨";
      case "system_event":
        return "⚙️";
      default:
        return "📝";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString("ja-JP");
  };

  if (loading) {
    return (
      <Layout
        title="ダッシュボード - CSR Lambda API System"
        headerProps={{
          isAuthenticated: true,
          user: user,
        }}
      >
        <div className="container py-8">
          <Loading size="lg" text="ダッシュボードを読み込み中..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title="ダッシュボード - CSR Lambda API System"
      headerProps={{
        isAuthenticated: true,
        user: user,
        onLogout: logout,
      }}
    >
      <div className="container py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">ダッシュボード</h1>
          <p className="text-gray-600">ようこそ、{user?.username || user?.email}さん。システムの概要をご確認ください。</p>
        </div>

        {/* 統計カード */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 text-lg">👥</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">総ユーザー数</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalUsers.toLocaleString()}</p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-green-600 text-lg">🟢</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">アクティブユーザー</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.activeUsers.toLocaleString()}</p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-purple-600 text-lg">📊</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">API呼び出し数</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.apiCalls.toLocaleString()}</p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <span className="text-gray-600 text-lg">❤️</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">システム状態</p>
                  <p className={`text-2xl font-bold ${getHealthStatusColor(stats.systemHealth)}`}>
                    {stats.systemHealth === "healthy" ? "正常" : stats.systemHealth === "warning" ? "警告" : "エラー"}
                  </p>
                </div>
              </div>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 最近のアクティビティ */}
          <div className="lg:col-span-2">
            <Card>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">最近のアクティビティ</h2>
                <Button variant="outline" size="sm">
                  すべて表示
                </Button>
              </div>

              <div className="space-y-4">
                {activities.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <span className="text-lg">{getActivityIcon(activity.type)}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900">{activity.message}</p>
                      <p className="text-xs text-gray-500">{formatTimestamp(activity.timestamp)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* クイックアクション */}
          <div>
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-6">クイックアクション</h2>

              <div className="space-y-3">
                <Button fullWidth variant="primary">
                  新しいプロジェクト作成
                </Button>
                <Button fullWidth variant="outline">
                  ユーザー管理
                </Button>
                <Button fullWidth variant="outline">
                  API設定
                </Button>
                <Button fullWidth variant="outline">
                  システム監視
                </Button>
              </div>
            </Card>

            {/* システム情報 */}
            <Card className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">システム情報</h3>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">バージョン</span>
                  <span className="text-gray-900">v1.0.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最終更新</span>
                  <span className="text-gray-900">2024-01-15</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">稼働時間</span>
                  <span className="text-gray-900">99.99%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">リージョン</span>
                  <span className="text-gray-900">ap-northeast-1</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}

// 認証ガードを適用（未認証ユーザーはログインページにリダイレクト）
export default withAuthGuard(Dashboard);
