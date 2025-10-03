# GitHub Personal Access Token 設定手順

## 概要

CodePipeline が GitHub リポジトリと連携するために必要な Personal Access Token の設定手順です。

## 前提条件

- GitHub アカウント: リポジトリへのアクセス権限
- AWS CLI: 設定済み（ap-northeast-1 リージョン）
- 適切な IAM 権限: Systems Manager Parameter Store への書き込み権限

## 手順

### 1. GitHub Personal Access Token の作成

1. GitHub にログインし、右上のプロフィール画像をクリック
2. **Settings** を選択
3. 左サイドバーの **Developer settings** をクリック
4. **Personal access tokens** → **Tokens (classic)** を選択
5. **Generate new token** → **Generate new token (classic)** をクリック

#### トークン設定

- **Note**: `CodePipeline-project_01` (識別しやすい名前)
- **Expiration**: `90 days` または `No expiration` (セキュリティ要件に応じて)
- **Select scopes**: 以下をチェック
  - ✅ `repo` (Full control of private repositories)
    - ✅ `repo:status` (Access commit status)
    - ✅ `repo_deployment` (Access deployment status)
    - ✅ `public_repo` (Access public repositories)
    - ✅ `repo:invite` (Access repository invitations)
  - ✅ `admin:repo_hook` (Full control of repository hooks)
    - ✅ `write:repo_hook` (Write repository hooks)
    - ✅ `read:repo_hook` (Read repository hooks)

6. **Generate token** をクリック
7. **重要**: 生成されたトークンをコピーして安全な場所に保存
   - このトークンは一度しか表示されません
   - 例: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. AWS Systems Manager Parameter Store への保存

生成したトークンを AWS に安全に保存します。

```bash
# 環境変数として設定（一時的）
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Parameter Store に暗号化して保存
aws ssm put-parameter \
    --name "/codepipeline/github/token" \
    --value "$GITHUB_TOKEN" \
    --type "SecureString" \
    --description "GitHub Personal Access Token for CodePipeline" \
    --region ap-northeast-1

# 保存確認
aws ssm get-parameter \
    --name "/codepipeline/github/token" \
    --with-decryption \
    --region ap-northeast-1 \
    --query "Parameter.Value" \
    --output text
```

### 3. 環境別パラメータの設定

各環境用に個別のパラメータを設定することも可能です：

```bash
# 開発環境用
aws ssm put-parameter \
    --name "/codepipeline/dev/github/token" \
    --value "$GITHUB_TOKEN" \
    --type "SecureString" \
    --description "GitHub Token for Dev Environment" \
    --region ap-northeast-1

# ステージング環境用
aws ssm put-parameter \
    --name "/codepipeline/staging/github/token" \
    --value "$GITHUB_TOKEN" \
    --type "SecureString" \
    --description "GitHub Token for Staging Environment" \
    --region ap-northeast-1

# 本番環境用
aws ssm put-parameter \
    --name "/codepipeline/prod/github/token" \
    --value "$GITHUB_TOKEN" \
    --type "SecureString" \
    --description "GitHub Token for Production Environment" \
    --region ap-northeast-1
```

## セキュリティ考慮事項

### トークンの管理

1. **定期的な更新**: トークンは定期的に更新する
2. **最小権限の原則**: 必要最小限の権限のみを付与
3. **監査ログ**: Parameter Store へのアクセスを監視
4. **暗号化**: 必ず SecureString タイプで保存

### アクセス制御

Parameter Store へのアクセスを制限する IAM ポリシー例：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter", "ssm:GetParameters"],
      "Resource": ["arn:aws:ssm:ap-northeast-1:*:parameter/codepipeline/*/github/token"]
    }
  ]
}
```

## トラブルシューティング

### よくある問題

1. **権限不足エラー**

   - GitHub トークンの権限を確認
   - AWS IAM 権限を確認

2. **トークンの有効期限切れ**

   - GitHub で新しいトークンを生成
   - Parameter Store の値を更新

3. **リージョンの不一致**
   - ap-northeast-1 リージョンを使用していることを確認

### 確認コマンド

```bash
# Parameter Store の値を確認
aws ssm describe-parameters \
    --parameter-filters "Key=Name,Values=/codepipeline" \
    --region ap-northeast-1

# 特定のパラメータの詳細を確認
aws ssm get-parameter \
    --name "/codepipeline/github/token" \
    --region ap-northeast-1
```

## 次のステップ

1. トークンの設定完了後、CloudFormation テンプレートでパラメータを参照
2. CodePipeline の作成・更新を実行
3. GitHub Webhook の動作確認

## 参考リンク

- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [AWS CodePipeline GitHub Integration](https://docs.aws.amazon.com/codepipeline/latest/userguide/GitHub-create-personal-token-CLI.html)
