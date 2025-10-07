# テストガイド

## 概要

このドキュメントは、CSR Lambda API システムの包括的なテスト戦略と実行手順を説明します。

## テスト戦略

### テストピラミッド

```
        /\
       /  \
      / E2E \     <- 少数の統合テスト
     /______\
    /        \
   / Integration \ <- 中程度の統合テスト
  /______________\
 /                \
/ Unit Tests       \ <- 多数の単体テスト
/__________________\
```

### テストレベル

1. **単体テスト (Unit Tests)**

   - 個別の関数・クラスのテスト
   - 高速実行、高カバレッジ
   - モック・スタブを使用

2. **統合テスト (Integration Tests)**

   - コンポーネント間の連携テスト
   - データベース、API の実際の動作確認
   - テスト環境での実行

3. **E2E テスト (End-to-End Tests)**

   - ユーザーシナリオの完全なテスト
   - ブラウザ自動化
   - 本番類似環境での実行

4. **パフォーマンステスト**

   - 負荷テスト、ストレステスト
   - レスポンス時間、スループットの測定

5. **セキュリティテスト**
   - 脆弱性スキャン
   - 認証・認可のテスト

## バックエンドテスト

### 単体テスト

#### 実行方法

```bash
cd backend

# 全単体テストの実行
python -m pytest tests/unit/ -v

# カバレッジ付きで実行
python -m pytest tests/unit/ --cov=app --cov-report=html

# 特定のテストファイルの実行
python -m pytest tests/unit/test_user_service.py -v

# 特定のテストケースの実行
python -m pytest tests/unit/test_user_service.py::test_create_user -v
```

#### テスト構成

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService
from app.models.user import User
from app.exceptions import ValidationError

class TestUserService:
    """ユーザーサービスの単体テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_repository = Mock()
        self.user_service = UserService(self.mock_repository)

    def test_create_user_success(self):
        """ユーザー作成成功のテスト"""
        # Arrange
        user_data = {
            'email': 'test@example.com',
            'username': 'testuser'
        }
        expected_user = User(id=1, **user_data)
        self.mock_repository.create.return_value = expected_user

        # Act
        result = self.user_service.create_user(user_data)

        # Assert
        assert result.email == user_data['email']
        assert result.username == user_data['username']
        self.mock_repository.create.assert_called_once_with(user_data)

    def test_create_user_duplicate_email(self):
        """重複メールアドレスでのユーザー作成失敗テスト"""
        # Arrange
        user_data = {
            'email': 'existing@example.com',
            'username': 'testuser'
        }
        self.mock_repository.exists_by_email.return_value = True

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            self.user_service.create_user(user_data)

        assert "既に使用されています" in str(exc_info.value)
```

### 統合テスト

#### 実行方法

```bash
# Docker Compose でテスト環境を起動
docker-compose -f docker-compose.test.yml up -d

# 統合テストの実行
python -m pytest tests/integration/ -v

# テスト環境のクリーンアップ
docker-compose -f docker-compose.test.yml down
```

#### データベース統合テスト

```python
# tests/integration/test_user_repository.py
import pytest
import pymysql
from app.database import get_database_config, create_connection
from app.repositories.user_repository import UserRepository

@pytest.fixture(scope="module")
def test_db():
    """テスト用データベースのセットアップ"""
    # テスト用データベース設定
    test_config = get_database_config()
    test_config['database'] = 'test_' + test_config['database']

    connection = pymysql.connect(**test_config)

    # テスト用テーブルの作成
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                cognito_user_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        connection.commit()

    yield connection

    # テスト後のクリーンアップ
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS users")
        connection.commit()
    connection.close()

class TestUserRepository:
    """ユーザーリポジトリの統合テスト"""

    def test_create_and_get_user(self, test_db):
        """ユーザー作成と取得のテスト"""
        repository = UserRepository(test_db, 'users')

        # ユーザー作成
        user_data = {
            'email': 'integration@example.com',
            'username': 'integrationuser',
            'cognito_user_id': 'test-cognito-id'
        }
        created_user = repository.create(user_data)

        # ユーザー取得
        retrieved_user = repository.get(created_user['id'])

        assert retrieved_user is not None
        assert retrieved_user['email'] == user_data['email']
        assert retrieved_user['username'] == user_data['username']
```

### API 統合テスト

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestUserAPI:
    """ユーザーAPI の統合テスト"""

    def test_create_user_endpoint(self):
        """ユーザー作成エンドポイントのテスト"""
        user_data = {
            'email': 'api@example.com',
            'username': 'apiuser',
            'password': 'testpassword123'
        }

        response = client.post('/api/v1/users', json=user_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data['email'] == user_data['email']
        assert response_data['username'] == user_data['username']
        assert 'id' in response_data

    def test_get_users_unauthorized(self):
        """認証なしでのユーザー一覧取得テスト"""
        response = client.get('/api/v1/users')

        assert response.status_code == 401

    @pytest.fixture
    def auth_headers(self):
        """認証ヘッダーの取得"""
        # テスト用トークンの取得ロジック
        return {'Authorization': 'Bearer test-token'}

    def test_get_users_authorized(self, auth_headers):
        """認証ありでのユーザー一覧取得テスト"""
        response = client.get('/api/v1/users', headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert isinstance(response_data, list)
```

## フロントエンドテスト

### 単体テスト (Jest + React Testing Library)

#### 実行方法

```bash
cd frontend

# 全単体テストの実行
npm test

# カバレッジ付きで実行
npm test -- --coverage

# ウォッチモードで実行
npm test -- --watch

# 特定のテストファイルの実行
npm test UserProfile.test.tsx
```

#### コンポーネントテスト

```typescript
// src/components/users/__tests__/UserProfile.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UserProfile } from "../UserProfile";
import { User } from "@/types";

const mockUser: User = {
  id: 1,
  email: "test@example.com",
  username: "testuser",
  cognitoUserId: "test-cognito-id",
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
};

describe("UserProfile", () => {
  test("ユーザー情報が正しく表示される", () => {
    render(<UserProfile user={mockUser} />);

    expect(screen.getByText("testuser")).toBeInTheDocument();
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
  });

  test("編集ボタンクリックで編集モードになる", async () => {
    const mockOnEdit = jest.fn();

    render(<UserProfile user={mockUser} onEdit={mockOnEdit} />);

    const editButton = screen.getByRole("button", { name: "編集" });
    fireEvent.click(editButton);

    await waitFor(() => {
      expect(mockOnEdit).toHaveBeenCalledWith(mockUser);
    });
  });
});
```

#### カスタムフックテスト

```typescript
// src/hooks/__tests__/use-users.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { useUsers } from "../use-users";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};

describe("useUsers", () => {
  test("ユーザー一覧を正しく取得する", async () => {
    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
  });
});
```

### E2E テスト (Playwright)

#### セットアップ

```bash
cd frontend

# Playwright のインストール
npm install -D @playwright/test
npx playwright install

# 設定ファイルの作成
npx playwright init
```

#### E2E テスト実行

```bash
# 全 E2E テストの実行
npx playwright test

# ヘッドレスモードで実行
npx playwright test --headed

# 特定のブラウザでテスト
npx playwright test --project=chromium

# デバッグモードで実行
npx playwright test --debug
```

#### E2E テストケース

```typescript
// tests/e2e/user-management.spec.ts
import { test, expect } from "@playwright/test";

test.describe("ユーザー管理機能", () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理
    await page.goto("/login");
    await page.fill("[data-testid=email-input]", "test@example.com");
    await page.fill("[data-testid=password-input]", "testpassword");
    await page.click("[data-testid=login-button]");

    // ダッシュボードページの表示を待機
    await expect(page).toHaveURL("/dashboard");
  });

  test("ユーザー一覧ページでユーザーが表示される", async ({ page }) => {
    await page.goto("/users");

    // ユーザー一覧の読み込み完了を待機
    await expect(page.locator("[data-testid=user-list]")).toBeVisible();

    // 最低1人のユーザーが表示されることを確認
    const userCards = page.locator("[data-testid=user-card]");
    await expect(userCards).toHaveCountGreaterThan(0);
  });

  test("新規ユーザーを作成できる", async ({ page }) => {
    await page.goto("/users");

    // 新規作成ボタンをクリック
    await page.click("[data-testid=create-user-button]");

    // フォームに入力
    await page.fill("[data-testid=username-input]", "newuser");
    await page.fill("[data-testid=email-input]", "newuser@example.com");

    // 作成ボタンをクリック
    await page.click("[data-testid=submit-button]");

    // 成功メッセージの確認
    await expect(page.locator("[data-testid=success-message]")).toBeVisible();

    // ユーザー一覧に新しいユーザーが表示されることを確認
    await expect(page.locator("text=newuser")).toBeVisible();
  });
});
```

## パフォーマンステスト

### 実行方法

```bash
cd backend

# 環境変数の設定
export PRODUCTION_API_URL=https://your-api-domain.com
export LOAD_TEST_USERS=50
export LOAD_TEST_REQUESTS_PER_USER=100

# パフォーマンステストの実行
python tests/performance/load_test.py

# 結果の確認
cat load_test_report.json
```

### 負荷テスト設定

```python
# パフォーマンステスト設定例
LOAD_TEST_SCENARIOS = {
    'light_load': {
        'concurrent_users': 10,
        'requests_per_user': 50,
        'ramp_up_time': 30
    },
    'normal_load': {
        'concurrent_users': 50,
        'requests_per_user': 100,
        'ramp_up_time': 60
    },
    'heavy_load': {
        'concurrent_users': 100,
        'requests_per_user': 200,
        'ramp_up_time': 120
    }
}
```

### パフォーマンス基準

| メトリクス         | 目標値      | 警告値     | 限界値     |
| ------------------ | ----------- | ---------- | ---------- |
| 平均レスポンス時間 | < 200ms     | < 500ms    | < 1000ms   |
| 95 パーセンタイル  | < 500ms     | < 1000ms   | < 2000ms   |
| エラー率           | < 0.1%      | < 1%       | < 5%       |
| スループット       | > 100 req/s | > 50 req/s | > 10 req/s |

## セキュリティテスト

### 実行方法

```bash
cd backend

# 環境変数の設定
export PRODUCTION_API_URL=https://your-api-domain.com

# セキュリティスキャンの実行
python tests/security/security_scanner.py

# 結果の確認
cat security_scan_report.json
```

### セキュリティチェック項目

1. **SSL/TLS 設定**

   - 証明書の有効性
   - TLS バージョン
   - 暗号化スイート

2. **セキュリティヘッダー**

   - HSTS
   - CSP
   - X-Frame-Options
   - X-Content-Type-Options

3. **認証・認可**

   - 未認証アクセスの拒否
   - 不正トークンの拒否
   - 権限チェック

4. **入力値検証**

   - SQL インジェクション対策
   - XSS 対策
   - バリデーション

5. **レート制限**
   - API レート制限
   - DDoS 対策

## 本番環境テスト

### ヘルスチェック

```bash
cd backend

# 環境変数の設定
export PRODUCTION_API_URL=https://your-api-domain.com
export PRODUCTION_API_KEY=your-api-key

# 本番環境ヘルスチェックの実行
python tests/production/test_production_health.py

# 結果の確認
cat production_health_check_results.json
```

### スモークテスト

```bash
# 基本的な API エンドポイントの動作確認
curl -X GET https://your-api-domain.com/api/v1/health
curl -X GET https://your-api-domain.com/api/v1/users -H "Authorization: Bearer $API_TOKEN"
```

## CI/CD でのテスト自動化

### GitHub Actions 設定

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpassword
          MYSQL_DATABASE: testdb
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest-cov

      - name: Run unit tests
        run: |
          cd backend
          python -m pytest tests/unit/ -v --cov=app --cov-report=xml

      - name: Run integration tests
        run: |
          cd backend
          python -m pytest tests/integration/ -v
        env:
          DATABASE_URL: mysql://root:testpassword@localhost:3306/testdb

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run unit tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/

  security-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Run security scan
        run: |
          cd backend
          python tests/security/security_scanner.py
        env:
          PRODUCTION_API_URL: ${{ secrets.PRODUCTION_API_URL }}
```

## テストデータ管理

### テストデータベース

```python
# tests/fixtures/test_data.py
import pytest
from app.models.user import User

@pytest.fixture
def sample_users():
    """サンプルユーザーデータ"""
    return [
        User(
            id=1,
            email='user1@example.com',
            username='user1',
            cognito_user_id='cognito-1'
        ),
        User(
            id=2,
            email='user2@example.com',
            username='user2',
            cognito_user_id='cognito-2'
        )
    ]

@pytest.fixture
def clean_database(test_db):
    """テスト前後でデータベースをクリーンアップ"""
    yield test_db

    # テスト後のクリーンアップ
    test_db.query(User).delete()
    test_db.commit()
```

### モックデータ

```typescript
// frontend/src/__tests__/mocks/api.ts
import { rest } from "msw";
import { User } from "@/types";

const mockUsers: User[] = [
  {
    id: 1,
    email: "test1@example.com",
    username: "testuser1",
    cognitoUserId: "cognito-1",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
];

export const handlers = [
  rest.get("/api/v1/users", (req, res, ctx) => {
    return res(ctx.json(mockUsers));
  }),

  rest.post("/api/v1/users", (req, res, ctx) => {
    const newUser = req.body as Partial<User>;
    return res(ctx.status(201), ctx.json({ ...newUser, id: Date.now() }));
  }),
];
```

## テスト結果の分析

### カバレッジレポート

```bash
# バックエンドカバレッジ
cd backend
python -m pytest --cov=app --cov-report=html
open htmlcov/index.html

# フロントエンドカバレッジ
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

### テストメトリクス

| メトリクス           | 目標値  | 現在値 |
| -------------------- | ------- | ------ |
| 単体テストカバレッジ | > 80%   | 85%    |
| 統合テストカバレッジ | > 70%   | 75%    |
| E2E テスト成功率     | > 95%   | 98%    |
| テスト実行時間       | < 10 分 | 8 分   |

## トラブルシューティング

### よくある問題

1. **テストの不安定性**

   - 非同期処理の適切な待機
   - テストデータの分離
   - 外部依存関係のモック化

2. **パフォーマンステストの失敗**

   - ネットワーク環境の確認
   - テスト対象環境の負荷状況
   - テストシナリオの見直し

3. **E2E テストのタイムアウト**
   - 待機時間の調整
   - 要素セレクターの見直し
   - ページ読み込み完了の確認

### デバッグ方法

```bash
# テストのデバッグ実行
python -m pytest tests/unit/test_user_service.py::test_create_user -v -s --pdb

# フロントエンドテストのデバッグ
npm test -- --detectOpenHandles --forceExit

# E2E テストのデバッグ
npx playwright test --debug --headed
```
