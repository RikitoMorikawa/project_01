# Aurora MySQL vs RDS MySQL 比較

## 🏗️ 現在の構成

### 作成されたデータベース

- **タイプ**: Aurora MySQL
- **クラスター**: `csr-lambda-api-dev-aurora`
- **インスタンス**: `csr-lambda-api-dev-aurora-instance-1`
- **エンジン**: `aurora-mysql 8.0.mysql_aurora.3.10.1`
- **インスタンスクラス**: `db.r5.large`

## 📊 Aurora MySQL vs RDS MySQL 比較

### Aurora MySQL（現在使用中）

```
┌─────────────────────────────────┐
│        Aurora MySQL             │
│  ┌─────────────────────────────┐ │
│  │     Aurora Cluster          │ │
│  │  ┌─────────┐ ┌─────────┐    │ │
│  │  │Writer   │ │Reader   │    │ │
│  │  │Instance │ │Instance │    │ │
│  │  └─────────┘ └─────────┘    │ │
│  └─────────────────────────────┘ │
│         Aurora Storage           │
│    (自動スケーリング・複製)        │
└─────────────────────────────────┘
```

**特徴:**

- ✅ **高可用性**: 自動フェイルオーバー
- ✅ **自動スケーリング**: ストレージが自動拡張
- ✅ **高性能**: 最大 5 倍のパフォーマンス
- ✅ **読み取りレプリカ**: 最大 15 個まで
- ✅ **バックアップ**: 継続的バックアップ
- ✅ **グローバル展開**: Aurora Global Database
- ❌ **コスト**: RDS MySQL より高価
- ❌ **複雑性**: 設定がやや複雑

### RDS MySQL（従来型）

```
┌─────────────────────────────────┐
│         RDS MySQL               │
│  ┌─────────────────────────────┐ │
│  │      Single Instance        │ │
│  │    ┌─────────────────┐      │ │
│  │    │   MySQL Server  │      │ │
│  │    └─────────────────┘      │ │
│  └─────────────────────────────┘ │
│         EBS Storage             │
│      (手動スケーリング)          │
└─────────────────────────────────┘
```

**特徴:**

- ✅ **シンプル**: 従来の MySQL と同じ
- ✅ **コスト**: Aurora より安価
- ✅ **互換性**: 完全な MySQL 互換
- ❌ **可用性**: 単一障害点
- ❌ **スケーリング**: 手動でのスケーリング
- ❌ **パフォーマンス**: Aurora より劣る

## 💰 コスト比較（概算）

### Aurora MySQL（現在の構成）

```
db.r5.large インスタンス:
- 時間単価: ~$0.29/時間
- 月額: ~$210/月
- ストレージ: $0.10/GB/月
- I/O: $0.20/100万リクエスト
```

### RDS MySQL（同等構成）

```
db.t3.medium インスタンス:
- 時間単価: ~$0.068/時間
- 月額: ~$50/月
- ストレージ: $0.115/GB/月（gp2）
```

## 🎯 使い分けの指針

### Aurora MySQL を選ぶべき場合

- **高可用性が必要**
- **読み取り負荷が高い**
- **グローバル展開予定**
- **自動スケーリングが必要**
- **パフォーマンスを重視**

### RDS MySQL を選ぶべき場合

- **コストを重視**
- **シンプルな構成で十分**
- **小規模なアプリケーション**
- **従来の MySQL から移行**

## 🔄 現在の構成を変更する場合

### Aurora → RDS MySQL に変更

```bash
# 1. データをエクスポート
mysqldump -h aurora-endpoint -u dev_user -p csr_lambda_dev > backup.sql

# 2. RDS MySQL インスタンスを作成
aws rds create-db-instance \
    --db-instance-identifier csr-lambda-dev-mysql \
    --db-instance-class db.t3.medium \
    --engine mysql \
    --master-username dev_user \
    --master-user-password DevPassword123! \
    --allocated-storage 20

# 3. データをインポート
mysql -h rds-endpoint -u dev_user -p csr_lambda_dev < backup.sql
```

### RDS MySQL → Aurora に変更

```bash
# 1. スナップショットを作成
aws rds create-db-snapshot \
    --db-instance-identifier source-mysql \
    --db-snapshot-identifier mysql-to-aurora-snapshot

# 2. Auroraクラスターを作成
aws rds restore-db-cluster-from-snapshot \
    --db-cluster-identifier new-aurora-cluster \
    --snapshot-identifier mysql-to-aurora-snapshot \
    --engine aurora-mysql
```

## 🚨 現在の構成での注意点

### コスト管理

- **db.r5.large** は開発環境には大きすぎる可能性
- **推奨**: `db.t3.medium` または `db.t4g.medium` に変更

### 開発環境での推奨変更

```bash
# より小さなインスタンスに変更
aws rds modify-db-instance \
    --db-instance-identifier csr-lambda-api-dev-aurora-instance-1 \
    --db-instance-class db.t3.medium \
    --apply-immediately
```

## 📋 まとめ

**現在の構成**: Aurora MySQL（高性能・高可用性・高コスト）

**開発環境での推奨**:

1. **継続使用**: 本番環境と同じ構成でテスト
2. **コスト削減**: インスタンスクラスを小さく変更
3. **RDS 変更**: コスト重視なら RDS MySQL に変更

どの選択肢を取るかは、開発チームの方針とコスト予算によります。
