# AWS インフラ設定ガイド

このガイドでは、CSR Lambda API システムの AWS インフラストラクチャを設定する手順を説明します。

## 📋 前提条件

- AWS アカウント: `3165071@gmail.com`
- AWS CLI がインストール済み
- GitHub アカウントとリポジトリへのアクセス権限
- 管理者権限のある IAM ユーザー

## 🚀 セットアップ手順

### ステップ 1: AWS CLI の設定

1. **AWS CLI のインストール確認**

   ```bash
   aws --version
   ```

2. **AWS 認証情報の設定**

   ```bash
   aws configure
   ```

   以下の情報を入力してください：

   - AWS Access Key ID: [管理者権限のあるアクセスキー]
   - AWS Secret Access Key: [対応するシークレットキー]
   - Default region name: `ap-northeast-1`
   - Default output format: `json`

3. **認証情報の確認**
   ```bash
   aws sts get-caller-identity
   ```

### ステップ 2: IAM ロールとポリシーのデプロイ

1. **デプロイスクリプトの実行**

   ```bash
   # 開発環境の場合
   ./infrastructure/scripts/deploy-iam-roles.sh dev

   # ステージング環境の場合
   ./infrastructure/scripts/deploy-iam-roles.sh staging

   # 本番環境の場合
   ./infrastructure/scripts/deploy-iam-roles.sh prod
   ```

2. **出力された認証情報をメモ**
   スクリプト実行後に表示される以下の値をメモしてください：
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_CLOUDFORMATION_ROLE_ARN`

### ステップ 3: GitHub Secrets の設定

1. **GitHub リポジトリにアクセス**

   - https://github.com/RikitoMorikawa/project_01 にアクセス

2. **Secrets の設定画面に移動**

   - `Settings` タブをクリック
   - 左サイドバーの `Secrets and variables` > `Actions` をクリック

3. **以下の Secrets を追加**

   | Secret Name                   | Value                     | 説明                                |
   | ----------------------------- | ------------------------- | ----------------------------------- |
   | `AWS_ACCESS_KEY_ID`           | [ステップ 2 で取得した値] | GitHub Actions 用アクセスキー       |
   | `AWS_SECRET_ACCESS_KEY`       | [ステップ 2 で取得した値] | GitHub Actions 用シークレットキー   |
   | `AWS_CLOUDFORMATION_ROLE_ARN` | [ステップ 2 で取得した値] | CloudFormation デプロイ用ロール ARN |

4. **Secrets 追加手順**
   - `New repository secret` ボタンをクリック
   - `Name` フィールドに Secret 名を入力
   - `Secret` フィールドに値を入力
   - `Add secret` ボタンをクリック

### ステップ 4: GitHub Personal Access Token の作成（オプション）

CodePipeline を使用する場合のみ必要です。

1. **GitHub Settings にアクセス**

   - GitHub プロフィール > `Settings` > `Developer settings` > `Personal access tokens` > `Tokens (classic)`

2. **新しいトークンを生成**

   - `Generate new token` > `Generate new token (classic)` をクリック
   - Note: `CSR Lambda API - CodePipeline`
   - Expiration: `90 days` または適切な期間
   - Scopes: `repo` と `admin:repo_hook` を選択

3. **トークンをコピー**

   - 生成されたトークンをコピーして安全な場所に保存

4. **GitHub Secret に追加**
   - Secret Name: `GITHUB_TOKEN`
   - Value: [生成したトークン]

### ステップ 5: デプロイメントの確認

1. **GitHub Actions の実行確認**

   - GitHub リポジトリの `Actions` タブにアクセス
   - `develop` ブランチにプッシュして開発環境デプロイを確認

2. **AWS リソースの確認**

   ```bash
   # CloudFormation スタックの確認
   aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

   # Lambda 関数の確認
   aws lambda list-functions --query 'Functions[?contains(FunctionName, `csr-lambda-api`)].FunctionName'

   # API Gateway の確認
   aws apigateway get-rest-apis --query 'items[?contains(name, `csr-lambda-api`)].{Name:name,Id:id}'
   ```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. AWS CLI 認証エラー

```
Error: Unable to locate credentials
```

**解決方法:**

```bash
aws configure list
aws sts get-caller-identity
```

#### 2. CloudFormation デプロイエラー

```
Error: User is not authorized to perform: iam:CreateRole
```

**解決方法:**

- AWS ユーザーに管理者権限があることを確認
- IAM ポリシーで必要な権限が付与されていることを確認

#### 3. GitHub Actions デプロイエラー

```
Error: The security token included in the request is invalid
```

**解決方法:**

- GitHub Secrets の値が正しいことを確認
- AWS アクセスキーが有効であることを確認

#### 4. Lambda 関数更新エラー

```
Error: The role defined for the function cannot be assumed by Lambda
```

**解決方法:**

- IAM ロールが正しく作成されていることを確認
- Lambda 実行ロールの信頼関係を確認

## 📊 デプロイされるリソース

### IAM リソース

- **CloudFormation デプロイロール**: インフラストラクチャのデプロイ用
- **CodePipeline サービスロール**: CI/CD パイプライン用
- **CodeBuild サービスロール**: ビルドプロセス用
- **GitHub Actions ユーザー**: GitHub Actions からの AWS アクセス用

### 主要なアプリケーションリソース

- **Lambda 関数**: FastAPI バックエンド
- **API Gateway**: REST API エンドポイント
- **S3 バケット**: フロントエンドホスティング
- **CloudFront**: CDN 配信
- **Aurora MySQL**: データベース
- **VPC**: ネットワーク分離

## 🔒 セキュリティ考慮事項

### 最小権限の原則

- 各ロールは必要最小限の権限のみを付与
- 環境ごとにリソースを分離
- アクセスキーの定期的なローテーション

### 監視とログ

- CloudTrail で API 呼び出しを記録
- CloudWatch でメトリクスとログを監視
- AWS Config でリソース設定を追跡

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお知らせください：

1. 実行したコマンド
2. エラーメッセージの全文
3. AWS アカウント ID（最後の 4 桁のみ）
4. 使用している環境（dev/staging/prod）

## 🔄 次のステップ

IAM 設定が完了したら、以下の手順に進んでください：

1. **アプリケーションのデプロイ**

   - GitHub Actions ワークフローの実行
   - デプロイメントの確認

2. **監視設定**

   - CloudWatch アラームの設定
   - SNS 通知の設定

3. **セキュリティ強化**

   - WAF ルールの設定
   - セキュリティグループの最適化

4. **パフォーマンス最適化**
   - Lambda Provisioned Concurrency の設定
   - CloudFront キャッシュ設定の最適化
