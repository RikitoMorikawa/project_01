import React from "react";
import { Layout } from "@/components/layout";
import { Button, Card } from "@/components/ui";

// サービス内容を柔軟に変更できる設定
const SERVICE_CONFIG = {
  hero: {
    title: "CSR Lambda API System",
    subtitle: "最新のサーバーレス技術で構築された高性能Webアプリケーション",
    description: "Next.js CSR + AWS Lambda + Aurora MySQL の組み合わせで、スケーラブルで高速なアプリケーションを提供します。",
    ctaText: "サービスを開始",
    secondaryCtaText: "詳細を見る",
  },
  features: [
    {
      title: "サーバーレスアーキテクチャ",
      description: "AWS Lambdaを活用した自動スケーリングとコスト最適化",
      icon: "⚡",
    },
    {
      title: "リアルタイム処理",
      description: "CSRによる高速なユーザーインターフェース",
      icon: "🚀",
    },
    {
      title: "セキュアな認証",
      description: "AWS Cognitoによる堅牢な認証・認可システム",
      icon: "🔒",
    },
    {
      title: "高可用性",
      description: "Aurora MySQLクラスターによる99.99%の可用性",
      icon: "🛡️",
    },
  ],
  stats: [
    { label: "アップタイム", value: "99.99%" },
    { label: "レスポンス時間", value: "<100ms" },
    { label: "セキュリティ", value: "SOC2準拠" },
    { label: "スケーラビリティ", value: "無制限" },
  ],
};

export default function Home() {
  const handleGetStarted = () => {
    // ログイン画面またはサインアップ画面に遷移
    window.location.href = "/login";
  };

  const handleLearnMore = () => {
    // サービス詳細ページに遷移
    window.location.href = "/about";
  };

  return (
    <Layout title={`${SERVICE_CONFIG.hero.title} - ホーム`} description={SERVICE_CONFIG.hero.description}>
      {/* ヒーローセクション */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div className="container">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">{SERVICE_CONFIG.hero.title}</h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8">{SERVICE_CONFIG.hero.subtitle}</p>
            <p className="text-lg text-gray-600 mb-10 max-w-2xl mx-auto">{SERVICE_CONFIG.hero.description}</p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" onClick={handleGetStarted} className="px-8 py-4">
                {SERVICE_CONFIG.hero.ctaText}
              </Button>
              <Button variant="outline" size="lg" onClick={handleLearnMore} className="px-8 py-4">
                {SERVICE_CONFIG.hero.secondaryCtaText}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 統計セクション */}
      <section className="py-16 bg-white">
        <div className="container">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {SERVICE_CONFIG.stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">{stat.value}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 機能セクション */}
      <section className="py-20 bg-gray-50">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">主な機能</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">最新のクラウド技術を活用した、高性能で拡張性の高いソリューション</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {SERVICE_CONFIG.features.map((feature, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTAセクション */}
      <section className="py-20 bg-blue-600">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">今すぐ始めましょう</h2>
            <p className="text-xl text-blue-100 mb-8">数分でアカウントを作成し、すぐにサービスをご利用いただけます。</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="secondary" size="lg" onClick={handleGetStarted} className=" text-blue-600 hover:bg-gray-100 px-8 py-4">
                無料で始める
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => (window.location.href = "/contact")}
                className="border-white text-white hover:bg-white hover:text-blue-600 px-8 py-4"
              >
                お問い合わせ
              </Button>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}
