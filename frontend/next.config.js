/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for S3 deployment
  output: "export",
  trailingSlash: true,

  // パフォーマンス最適化設定
  images: {
    unoptimized: true,
    formats: ["image/webp", "image/avif"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // 実験的機能
  experimental: {
    esmExternals: false,
    // バンドル分析を有効化
    bundlePagesRouterDependencies: true,
    // 最適化されたパッケージ
    optimizePackageImports: ["@aws-amplify/ui-react", "aws-amplify", "react-query", "axios"],
  },

  // Webpack 設定のカスタマイズ
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 本番環境でのバンドル最適化
    if (!dev && !isServer) {
      // Tree shaking の強化
      config.optimization.usedExports = true;
      config.optimization.sideEffects = false;

      // バンドル分割の最適化
      config.optimization.splitChunks = {
        chunks: "all",
        cacheGroups: {
          // ベンダーライブラリを分離
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: "vendors",
            chunks: "all",
            priority: 10,
          },
          // AWS Amplify を分離
          amplify: {
            test: /[\\/]node_modules[\\/](@aws-amplify|aws-amplify)[\\/]/,
            name: "amplify",
            chunks: "all",
            priority: 20,
          },
          // React 関連を分離
          react: {
            test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
            name: "react",
            chunks: "all",
            priority: 30,
          },
          // 共通コンポーネントを分離
          common: {
            name: "common",
            minChunks: 2,
            chunks: "all",
            priority: 5,
            reuseExistingChunk: true,
          },
        },
      };

      // 圧縮設定の最適化
      config.optimization.minimize = true;

      // 不要なモジュールを除外
      config.resolve.alias = {
        ...config.resolve.alias,
        // moment.js の代わりに date-fns を使用
        moment: "date-fns",
      };

      // バンドルサイズ分析（環境変数で有効化）
      if (process.env.ANALYZE === "true") {
        const { BundleAnalyzerPlugin } = require("webpack-bundle-analyzer");
        config.plugins.push(
          new BundleAnalyzerPlugin({
            analyzerMode: "static",
            openAnalyzer: false,
            reportFilename: "bundle-analyzer-report.html",
          })
        );
      }
    }

    // 開発環境での高速化
    if (dev) {
      // 高速リフレッシュの最適化
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }

    return config;
  },

  // コンパイラ設定
  compiler: {
    // 本番環境でのコンソールログ削除
    removeConsole:
      process.env.NODE_ENV === "production"
        ? {
            exclude: ["error", "warn"],
          }
        : false,

    // styled-components の最適化
    styledComponents: true,
  },

  // 静的最適化
  staticPageGenerationTimeout: 60,

  // パフォーマンス設定
  poweredByHeader: false,
  generateEtags: false,

  // 圧縮設定
  compress: true,

  // Environment-specific configuration
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_AWS_REGION: process.env.NEXT_PUBLIC_AWS_REGION,
    NEXT_PUBLIC_COGNITO_USER_POOL_ID: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID,
    NEXT_PUBLIC_COGNITO_CLIENT_ID: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID,
  },

  // セキュリティヘッダー
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
      {
        source: "/static/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
