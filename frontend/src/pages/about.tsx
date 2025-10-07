import React from "react";
import { Layout } from "@/components/layout";
import { Card, Button } from "@/components/ui";

export default function About() {
  const features = [
    {
      title: "サーバーレスアーキテクチャ",
      description: "AWS Lambdaを活用した自動スケーリングとコスト最適化により、トラフィックに応じて柔軟にリソースを調整します。",
      benefits: ["自動スケーリング", "コスト最適化", "高可用性", "メンテナンス不要"],
    },
    {
      title: "モダンフロントエンド",
      description: "Next.js CSRによる高速なユーザーインターフェースで、優れたユーザーエクスペリエンスを提供します。",
      benefits: ["高速レンダリング", "SEO対応", "TypeScript対応", "レスポンシブデザイン"],
    },
    {
      title: "セキュアな認証",
      description: "AWS Cognitoによる堅牢な認証・認可システムで、ユーザーデータを安全に保護します。",
      benefits: ["多要素認証", "ソーシャルログイン", "パスワードポリシー", "セッション管理"],
    },
    {
      title: "高性能データベース",
      description: "Aurora MySQLクラスターによる高可用性と高性能なデータ処理を実現します。",
      benefits: ["99.99%可用性", "自動バックアップ", "リードレプリカ", "暗号化対応"],
    },
  ];

  const techStack = [
    { category: "フロントエンド", technologies: ["Next.js 14", "React 18", "TypeScript", "Tailwind CSS"] },
    { category: "バックエンド", technologies: ["FastAPI", "Python 3.11", "Pydantic", "PyMySQL"] },
    { category: "インフラ", technologies: ["AWS Lambda", "API Gateway", "Aurora MySQL", "CloudFront"] },
    { category: "認証", technologies: ["AWS Cognito", "JWT", "OAuth 2.0", "OIDC"] },
    { category: "監視", technologies: ["CloudWatch", "X-Ray", "CloudTrail", "SNS"] },
    { category: "CI/CD", technologies: ["GitHub Actions", "CodePipeline", "CodeBuild", "CloudFormation"] },
  ];

  return (
    <Layout title="サービスについて - CSR Lambda API System" description="CSR Lambda API Systemの詳細な機能と技術スタックについてご紹介します">
      {/* ヒーローセクション */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-16">
        <div className="container">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">CSR Lambda API System について</h1>
            <p className="text-xl text-gray-600 mb-8">
              最新のサーバーレス技術とモダンなフロントエンド技術を組み合わせた、 次世代のWebアプリケーションプラットフォームです。
            </p>
          </div>
        </div>
      </section>

      {/* 概要セクション */}
      <section className="py-16 bg-white">
        <div className="container">
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 mb-6">なぜCSR Lambda API Systemなのか？</h2>
                <div className="space-y-4 text-gray-600">
                  <p>
                    従来のWebアプリケーションの課題を解決するため、最新のクラウドネイティブ技術を採用しました。
                    サーバーレスアーキテクチャにより、運用コストを削減しながら高い可用性を実現します。
                  </p>
                  <p>
                    Client-Side Rendering（CSR）により、ユーザーに高速で滑らかな操作体験を提供し、 AWS
                    Lambdaによるバックエンドで、スケーラブルで効率的なAPI処理を実現します。
                  </p>
                  <p>セキュリティ、パフォーマンス、開発効率のすべてを両立した、 現代的なWebアプリケーション開発のベストプラクティスを体現しています。</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Card className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">99.99%</div>
                  <div className="text-sm text-gray-600">可用性</div>
                </Card>
                <Card className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">&lt;100ms</div>
                  <div className="text-sm text-gray-600">レスポンス時間</div>
                </Card>
                <Card className="text-center">
                  <div className="text-3xl font-bold text-purple-600 mb-2">∞</div>
                  <div className="text-sm text-gray-600">スケーラビリティ</div>
                </Card>
                <Card className="text-center">
                  <div className="text-3xl font-bold text-orange-600 mb-2">24/7</div>
                  <div className="text-sm text-gray-600">監視体制</div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 主要機能セクション */}
      <section className="py-16 bg-gray-50">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">主要機能</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">現代的なWebアプリケーションに必要な機能を包括的に提供</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="h-full">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 mb-4">{feature.description}</p>
                <div className="space-y-2">
                  {feature.benefits.map((benefit, benefitIndex) => (
                    <div key={benefitIndex} className="flex items-center text-sm text-gray-600">
                      <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {benefit}
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* 技術スタックセクション */}
      <section className="py-16 bg-white">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">技術スタック</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">最新かつ実績のある技術を組み合わせた堅牢なアーキテクチャ</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {techStack.map((stack, index) => (
              <Card key={index}>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{stack.category}</h3>
                <div className="space-y-2">
                  {stack.technologies.map((tech, techIndex) => (
                    <div key={techIndex} className="flex items-center text-sm text-gray-600">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                      {tech}
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* アーキテクチャ図セクション */}
      <section className="py-16 bg-gray-50">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">システムアーキテクチャ</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">スケーラブルで高可用性を実現するクラウドネイティブアーキテクチャ</p>
          </div>

          <Card className="max-w-4xl mx-auto">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🏗️</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">アーキテクチャ図</h3>
              <p className="text-gray-600 mb-6">詳細なシステム構成図は開発完了後に公開予定です</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                <div>
                  <strong>フロントエンド</strong>
                  <br />
                  Next.js CSR → CloudFront → S3
                </div>
                <div>
                  <strong>API</strong>
                  <br />
                  API Gateway → Lambda → Aurora MySQL
                </div>
                <div>
                  <strong>認証</strong>
                  <br />
                  Cognito → JWT → API Gateway
                </div>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* CTAセクション */}
      <section className="py-16 bg-blue-600">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-white mb-6">今すぐ始めてみませんか？</h2>
            <p className="text-xl text-blue-100 mb-8">CSR Lambda API Systemで、次世代のWebアプリケーション開発を体験してください。</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="secondary" size="lg" onClick={() => (window.location.href = "/login")} className=" text-blue-600 hover:bg-gray-100 px-8 py-4">
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
