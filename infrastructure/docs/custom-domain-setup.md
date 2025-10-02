# カスタムドメインと SSL 証明書の設定ガイド

このドキュメントでは、CSR Lambda API システムでカスタムドメインと SSL 証明書を設定する方法について説明します。

## 概要

システムは以下のドメイン設定をサポートしています：

- **開発環境**: CloudFront デフォルトドメイン（例：`d123456789.cloudfront.net`）
- **ステージング環境**: カスタムドメイン対応（例：`staging.example.com`）
- **本番環境**: カスタムドメイン対応（例：`www.example.com`）

## 前提条件

1. **ドメインの所有**: 設定したいドメインを所有していること
2. **Route 53 ホストゾーン**: ドメインの DNS 管理が Route 53 で行われていること
3. **AWS Certificate Manager**: SSL 証明書が`us-east-1`リージョンで発行されていること

## 手順

### 1. Route 53 ホストゾーンの設定

ドメインの DNS 管理を Route 53 で行う必要があります。

```bash
# ホストゾーンの作成
aws route53 create-hosted-zone \
    --name example.com \
    --caller-reference $(date +%s)

# ホストゾーンIDの確認
aws route53 list-hosted-zones \
    --query "HostedZones[?Name=='example.com.'].Id" \
    --output text
```

### 2. SSL 証明書の取得

CloudFront で使用する SSL 証明書は`us-east-1`リージョンで発行する必要があります。

```bash
# SSL証明書のリクエスト
aws acm request-certificate \
    --domain-name example.com \
    --subject-alternative-names "*.example.com" \
    --validation-method DNS \
    --region us-east-1

# 証明書ARNの確認
aws acm list-certificates \
    --region us-east-1 \
    --query "CertificateSummaryList[?DomainName=='example.com'].CertificateArn" \
    --output text
```

### 3. DNS 検証の完了

ACM で発行した証明書の DNS 検証を完了します。

```bash
# 検証レコードの確認
aws acm describe-certificate \
    --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
    --region us-east-1 \
    --query "Certificate.DomainValidationOptions"

# Route 53に検証レコードを追加（手動またはスクリプトで）
```

### 4. デプロイメントの実行

カスタムドメインを使用してシステムをデプロイします。

#### ステージング環境の例

```bash
./infrastructure/scripts/deploy-with-custom-domain.sh \
    staging \
    staging.example.com \
    arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
    Z1D633PJN98FT9
```

#### 本番環境の例

```bash
./infrastructure/scripts/deploy-with-custom-domain.sh \
    prod \
    www.example.com \
    arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
    Z1D633PJN98FT9
```

## 設定パラメータ

### CloudFormation パラメータ

| パラメータ名        | 説明                     | 必須                   | 例                          |
| ------------------- | ------------------------ | ---------------------- | --------------------------- |
| `CustomDomainName`  | カスタムドメイン名       | No                     | `www.example.com`           |
| `SSLCertificateArn` | SSL 証明書の ARN         | カスタムドメイン使用時 | `arn:aws:acm:us-east-1:...` |
| `HostedZoneId`      | Route 53 ホストゾーン ID | カスタムドメイン使用時 | `Z1D633PJN98FT9`            |

### 環境別設定

#### 開発環境 (dev)

- CloudFront: 無効（デフォルト）
- カスタムドメイン: 非対応
- SSL: CloudFront デフォルト証明書

#### ステージング環境 (staging)

- CloudFront: 有効
- カスタムドメイン: 対応
- SSL: ACM 証明書または CloudFront デフォルト証明書
- WAF: 基本ルール

#### 本番環境 (prod)

- CloudFront: 有効
- カスタムドメイン: 対応
- SSL: ACM 証明書推奨
- WAF: 強化されたセキュリティルール

## セキュリティ設定

### SSL/TLS 設定

- **最小プロトコルバージョン**: TLS 1.2
- **暗号化スイート**: CloudFront 推奨設定
- **HSTS**: 有効（本番環境）

### セキュリティヘッダー

本番環境では以下のセキュリティヘッダーが自動的に設定されます：

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

## トラブルシューティング

### よくある問題

#### 1. 証明書が見つからない

**症状**: CloudFormation デプロイ時に証明書エラー

**解決方法**:

- 証明書が`us-east-1`リージョンにあることを確認
- 証明書のステータスが`ISSUED`であることを確認
- 証明書 ARN が正しいことを確認

#### 2. DNS 解決ができない

**症状**: カスタムドメインにアクセスできない

**解決方法**:

- Route 53 の DNS レコードが正しく設定されていることを確認
- DNS 伝播の完了を待つ（最大 48 時間）
- `dig`コマンドで DNS 解決を確認

```bash
dig www.example.com
```

#### 3. CloudFront ディストリビューションエラー

**症状**: CloudFront ディストリビューションの作成に失敗

**解決方法**:

- カスタムドメインが他の CloudFront ディストリビューションで使用されていないことを確認
- 証明書のドメイン名とカスタムドメイン名が一致することを確認

### ログとモニタリング

#### CloudFront ログ

CloudFront アクセスログは専用の S3 バケットに保存されます：

```
{project-name}-{environment}-cloudfront-logs-{account-id}
```

#### WAF ログ

WAF ログは CloudWatch Logs に出力されます：

```
/aws/wafv2/{project-name}-{environment}
```

#### アラーム

以下のメトリクスでアラームが設定されます：

- CloudFront 4xx/5xx エラー率
- CloudFront オリジンレイテンシ
- WAF ブロック済みリクエスト数

## 費用について

### CloudFront 料金

- **リクエスト料金**: 10,000 リクエストあたり約$0.0075
- **データ転送料金**: 1GB あたり約$0.085（最初の 10TB）
- **SSL 証明書**: カスタム証明書使用時は月額$600（専用 IP）

### Route 53 料金

- **ホストゾーン**: 月額$0.50
- **DNS クエリ**: 100 万クエリあたり$0.40

### ACM 料金

- **パブリック証明書**: 無料
- **プライベート証明書**: 月額$400（使用しない場合）

## 参考資料

- [CloudFront カスタムドメイン設定](https://docs.aws.amazon.com/cloudfront/latest/DeveloperGuide/CNAMEs.html)
- [ACM 証明書の検証](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-validate-dns.html)
- [Route 53 ホストゾーン管理](https://docs.aws.amazon.com/route53/latest/developerguide/hosted-zones-working-with.html)
