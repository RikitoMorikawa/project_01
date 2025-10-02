/**
 * Jest設定ファイル
 * Jest configuration file
 */

const nextJest = require("next/jest");

const createJestConfig = nextJest({
  // Next.jsアプリのパスを指定 / Provide the path to your Next.js app
  dir: "./",
});

// Jestのカスタム設定 / Custom Jest configuration
const customJestConfig = {
  // テスト環境の設定 / Test environment setup
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",

  // TypeScript設定 / TypeScript configuration
  globals: {
    "ts-jest": {
      tsconfig: "tsconfig.test.json",
    },
  },

  // モジュールパスマッピング / Module path mapping
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },

  // テストファイルのパターン / Test file patterns
  testMatch: ["<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}", "<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}"],

  // カバレッジ設定 / Coverage configuration
  collectCoverageFrom: ["src/**/*.{js,jsx,ts,tsx}", "!src/**/*.d.ts", "!src/pages/_app.tsx", "!src/pages/_document.tsx", "!src/pages/api/**"],

  // カバレッジしきい値 / Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },

  // テスト実行時の設定 / Test execution settings
  verbose: true,
  clearMocks: true,
  restoreMocks: true,

  // モックファイルの場所 / Mock files location
  moduleDirectories: ["node_modules", "<rootDir>/"],

  // 変換対象外のファイル / Files to ignore for transformation
  transformIgnorePatterns: ["/node_modules/", "^.+\\.module\\.(css|sass|scss)$"],
};

// Next.jsの設定とマージして出力 / Merge with Next.js config and export
module.exports = createJestConfig(customJestConfig);
