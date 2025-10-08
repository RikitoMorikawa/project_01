#!/usr/bin/env python3

import os
import sys
import getpass
import pymysql

def test_rds_connection():
    """RDS接続をテストする"""
    
    # RDS接続情報
    db_host = "csr-lambda-api-dev-aurora-instance-1.cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
    db_port = 3306
    db_name = "csr_lambda_dev"
    db_user = "dev_user"
    
    # パスワードを入力
    print(f"RDS接続テスト")
    print(f"ホスト: {db_host}")
    print(f"データベース: {db_name}")
    print(f"ユーザー: {db_user}")
    print()
    
    db_password = getpass.getpass("RDSパスワードを入力してください: ")
    
    try:
        print("RDS接続を試行中...")
        
        # PyMySQLで直接接続
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection:
            with connection.cursor() as cursor:
                # 基本的な接続テスト
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
                if result['test'] == 1:
                    print("✅ RDS接続成功!")
                    
                    # データベース情報を取得
                    cursor.execute("SELECT DATABASE() as db_name, USER() as user_name, VERSION() as version")
                    db_info = cursor.fetchone()
                    print(f"   データベース: {db_info['db_name']}")
                    print(f"   ユーザー: {db_info['user_name']}")
                    print(f"   MySQLバージョン: {db_info['version']}")
                    
                    # テーブル一覧を取得
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    print(f"   テーブル数: {len(tables)}")
                    if tables:
                        print("   テーブル一覧:")
                        for table in tables:
                            table_name = list(table.values())[0]
                            print(f"     - {table_name}")
                    
                    # .env.dev.rds ファイルを更新
                    env_content = f"""# Development Environment RDS Configuration
ENVIRONMENT=dev

# RDS Database Configuration (Development)
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DATABASE_URL=mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}

# AWS Configuration
AWS_REGION=ap-northeast-1
COGNITO_USER_POOL_ID=ap-northeast-1_HluYCXwCo
COGNITO_CLIENT_ID=71mnemjh6en2qpd5cmv21qp30u

# API Configuration
API_TITLE=CSR Lambda API - Development (RDS)
CORS_ORIGINS=["https://d2m0cmcbfsdzr7.cloudfront.net", "http://localhost:3000"]

# CloudFront Configuration
CLOUDFRONT_DISTRIBUTION_ID=E1RDC06Y79TYSS
CLOUDFRONT_DOMAIN_NAME=d2m0cmcbfsdzr7.cloudfront.net
FRONTEND_URL=https://d2m0cmcbfsdzr7.cloudfront.net
S3_FRONTEND_BUCKET=csr-lambda-api-dev-main-frontends3bucket-a8n79be9xmun
"""
                    
                    with open("../backend/.env.dev.rds", "w") as f:
                        f.write(env_content)
                    
                    print("✅ .env.dev.rds ファイルを更新しました")
                    return True
                
    except Exception as e:
        print(f"❌ RDS接続失敗: {e}")
        print()
        print("考えられる原因:")
        print("1. パスワードが間違っている")
        print("2. セキュリティグループでアクセスが制限されている")
        print("3. RDSインスタンスが停止している")
        print("4. ネットワーク接続の問題")
        return False

if __name__ == "__main__":
    success = test_rds_connection()
    sys.exit(0 if success else 1)