#!/usr/bin/env python3

import sys
import os

# RDS接続情報
DB_CLUSTER_ENDPOINT = "csr-lambda-api-dev-aurora.cluster-cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
DB_INSTANCE_ENDPOINT = "csr-lambda-api-dev-aurora-instance-1.cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
DB_PORT = 3306
DB_NAME = "csr_lambda_dev"
DB_USER = "dev_user"
NEW_PASSWORD = "DevPassword123!"

def test_with_pymysql():
    """PyMySQLを使用してテスト"""
    try:
        import pymysql
        print("✅ PyMySQLが利用可能です")
        
        # クラスターエンドポイントでテスト
        print(f"🔄 クラスターエンドポイントで接続テスト: {DB_CLUSTER_ENDPOINT}")
        try:
            connection = pymysql.connect(
                host=DB_CLUSTER_ENDPOINT,
                port=DB_PORT,
                user=DB_USER,
                password=NEW_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                ssl={'ssl_disabled': False},
                connect_timeout=10
            )
            
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    if result['test'] == 1:
                        print("✅ クラスターエンドポイント接続成功!")
                        return DB_CLUSTER_ENDPOINT, connection
                        
        except Exception as e:
            print(f"❌ クラスターエンドポイント接続失敗: {e}")
        
        # インスタンスエンドポイントでテスト
        print(f"🔄 インスタンスエンドポイントで接続テスト: {DB_INSTANCE_ENDPOINT}")
        try:
            connection = pymysql.connect(
                host=DB_INSTANCE_ENDPOINT,
                port=DB_PORT,
                user=DB_USER,
                password=NEW_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                ssl={'ssl_disabled': False},
                connect_timeout=10
            )
            
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    if result['test'] == 1:
                        print("✅ インスタンスエンドポイント接続成功!")
                        return DB_INSTANCE_ENDPOINT, connection
                        
        except Exception as e:
            print(f"❌ インスタンスエンドポイント接続失敗: {e}")
            
        return None, None
        
    except ImportError:
        print("❌ PyMySQLがインストールされていません")
        print("インストール方法: pip3 install pymysql")
        return None, None

def test_with_mysql_connector():
    """mysql-connector-pythonを使用してテスト"""
    try:
        import mysql.connector
        print("✅ mysql-connector-pythonが利用可能です")
        
        # クラスターエンドポイントでテスト
        print(f"🔄 クラスターエンドポイントで接続テスト: {DB_CLUSTER_ENDPOINT}")
        try:
            connection = mysql.connector.connect(
                host=DB_CLUSTER_ENDPOINT,
                port=DB_PORT,
                user=DB_USER,
                password=NEW_PASSWORD,
                database=DB_NAME,
                ssl_disabled=False,
                connection_timeout=10
            )
            
            cursor = connection.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ クラスターエンドポイント接続成功!")
                cursor.close()
                return DB_CLUSTER_ENDPOINT, connection
                
        except Exception as e:
            print(f"❌ クラスターエンドポイント接続失敗: {e}")
        
        # インスタンスエンドポイントでテスト
        print(f"🔄 インスタンスエンドポイントで接続テスト: {DB_INSTANCE_ENDPOINT}")
        try:
            connection = mysql.connector.connect(
                host=DB_INSTANCE_ENDPOINT,
                port=DB_PORT,
                user=DB_USER,
                password=NEW_PASSWORD,
                database=DB_NAME,
                ssl_disabled=False,
                connection_timeout=10
            )
            
            cursor = connection.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ インスタンスエンドポイント接続成功!")
                cursor.close()
                return DB_INSTANCE_ENDPOINT, connection
                
        except Exception as e:
            print(f"❌ インスタンスエンドポイント接続失敗: {e}")
            
        return None, None
        
    except ImportError:
        print("❌ mysql-connector-pythonがインストールされていません")
        print("インストール方法: pip3 install mysql-connector-python")
        return None, None

def get_database_info(endpoint, connection_type):
    """データベース情報を取得"""
    if connection_type == "pymysql":
        import pymysql
        connection = pymysql.connect(
            host=endpoint,
            port=DB_PORT,
            user=DB_USER,
            password=NEW_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl_disabled': False}
        )
        
        with connection:
            with connection.cursor() as cursor:
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
    
    elif connection_type == "mysql.connector":
        import mysql.connector
        connection = mysql.connector.connect(
            host=endpoint,
            port=DB_PORT,
            user=DB_USER,
            password=NEW_PASSWORD,
            database=DB_NAME,
            ssl_disabled=False
        )
        
        cursor = connection.cursor()
        
        # データベース情報を取得
        cursor.execute("SELECT DATABASE() as db_name, USER() as user_name, VERSION() as version")
        db_info = cursor.fetchone()
        print(f"   データベース: {db_info[0]}")
        print(f"   ユーザー: {db_info[1]}")
        print(f"   MySQLバージョン: {db_info[2]}")
        
        # テーブル一覧を取得
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"   テーブル数: {len(tables)}")
        if tables:
            print("   テーブル一覧:")
            for table in tables:
                print(f"     - {table[0]}")
        
        cursor.close()
        connection.close()

def update_env_file(endpoint):
    """環境設定ファイルを更新"""
    env_content = f"""# Development Environment RDS Configuration
ENVIRONMENT=dev

# RDS Database Configuration (Development)
DB_HOST={endpoint}
DB_PORT={DB_PORT}
DB_NAME={DB_NAME}
DB_USER={DB_USER}
DB_PASSWORD={NEW_PASSWORD}
DATABASE_URL=mysql+pymysql://{DB_USER}:{NEW_PASSWORD}@{endpoint}:{DB_PORT}/{DB_NAME}

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

def main():
    print("🔄 RDS接続テスト - Python版")
    print(f"クラスターエンドポイント: {DB_CLUSTER_ENDPOINT}")
    print(f"インスタンスエンドポイント: {DB_INSTANCE_ENDPOINT}")
    print(f"データベース: {DB_NAME}")
    print(f"ユーザー: {DB_USER}")
    print()
    
    # PyMySQLでテスト
    endpoint, connection = test_with_pymysql()
    connection_type = "pymysql"
    
    # PyMySQLで失敗した場合はmysql-connector-pythonでテスト
    if endpoint is None:
        endpoint, connection = test_with_mysql_connector()
        connection_type = "mysql.connector"
    
    if endpoint:
        print(f"✅ 接続成功! 使用エンドポイント: {endpoint}")
        
        # データベース情報を取得
        print("🔄 データベース情報を取得中...")
        get_database_info(endpoint, connection_type)
        
        # 環境設定ファイルを更新
        print("🔄 .env.dev.rds ファイルを更新中...")
        update_env_file(endpoint)
        
        print()
        print("🎉 === RDS接続設定完了 ===")
        print(f"エンドポイント: {endpoint}")
        print(f"パスワード: {NEW_PASSWORD}")
        print(f"接続文字列: mysql+pymysql://{DB_USER}:{NEW_PASSWORD}@{endpoint}:{DB_PORT}/{DB_NAME}")
        
    else:
        print("❌ すべての接続方法で失敗しました")
        print()
        print("🔧 トラブルシューティング:")
        print("1. パスワード変更がまだ反映されていない可能性があります（数分待ってから再試行）")
        print("2. 必要なPythonライブラリをインストール:")
        print("   pip3 install pymysql")
        print("   または")
        print("   pip3 install mysql-connector-python")
        print("3. ネットワーク接続を確認")
        sys.exit(1)

if __name__ == "__main__":
    main()