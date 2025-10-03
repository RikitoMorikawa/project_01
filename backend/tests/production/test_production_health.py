"""
本番環境での動作確認テスト

本番環境のエンドポイントに対して基本的な動作確認を行う
"""
import pytest
import requests
import os
from typing import Dict, Any
import time
import json


class ProductionHealthChecker:
    """本番環境ヘルスチェッククラス"""
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        初期化
        
        Args:
            base_url: 本番環境のベースURL
            api_key: API認証キー（必要に応じて）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # 共通ヘッダーの設定
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ProductionHealthChecker/1.0'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def check_health_endpoint(self) -> Dict[str, Any]:
        """
        ヘルスチェックエンドポイントの確認
        
        Returns:
            Dict[str, Any]: テスト結果
        """
        try:
            response = self.session.get(f'{self.base_url}/api/v1/health', timeout=30)
            
            return {
                'endpoint': '/api/v1/health',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'success': response.status_code == 200,
                'response_data': response.json() if response.status_code == 200 else None,
                'error': None
            }
        except Exception as e:
            return {
                'endpoint': '/api/v1/health',
                'status_code': None,
                'response_time': None,
                'success': False,
                'response_data': None,
                'error': str(e)
            }
    
    def check_database_connectivity(self) -> Dict[str, Any]:
        """
        データベース接続確認
        
        Returns:
            Dict[str, Any]: テスト結果
        """
        try:
            response = self.session.get(f'{self.base_url}/api/v1/health/db', timeout=30)
            
            return {
                'endpoint': '/api/v1/health/db',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'success': response.status_code == 200,
                'response_data': response.json() if response.status_code == 200 else None,
                'error': None
            }
        except Exception as e:
            return {
                'endpoint': '/api/v1/health/db',
                'status_code': None,
                'response_time': None,
                'success': False,
                'response_data': None,
                'error': str(e)
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """
        主要APIエンドポイントの確認
        
        Returns:
            Dict[str, Any]: テスト結果
        """
        endpoints = [
            {'method': 'GET', 'path': '/api/v1/users', 'auth_required': True},
            {'method': 'POST', 'path': '/api/v1/auth/login', 'auth_required': False},
        ]
        
        results = []
        
        for endpoint in endpoints:
            try:
                method = getattr(self.session, endpoint['method'].lower())
                
                # 認証が必要な場合のテストデータ
                if endpoint['auth_required'] and not self.api_key:
                    # 認証なしでアクセスして401が返ることを確認
                    response = method(f"{self.base_url}{endpoint['path']}", timeout=30)
                    expected_status = 401
                else:
                    response = method(f"{self.base_url}{endpoint['path']}", timeout=30)
                    expected_status = 200
                
                results.append({
                    'endpoint': endpoint['path'],
                    'method': endpoint['method'],
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'success': response.status_code == expected_status,
                    'error': None
                })
                
            except Exception as e:
                results.append({
                    'endpoint': endpoint['path'],
                    'method': endpoint['method'],
                    'status_code': None,
                    'response_time': None,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total_endpoints': len(endpoints),
            'successful_endpoints': sum(1 for r in results if r['success']),
            'results': results
        }
    
    def check_ssl_certificate(self) -> Dict[str, Any]:
        """
        SSL証明書の確認
        
        Returns:
            Dict[str, Any]: テスト結果
        """
        try:
            import ssl
            import socket
            from urllib.parse import urlparse
            
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=30) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'ssl_valid': True,
                        'certificate_info': {
                            'subject': dict(x[0] for x in cert['subject']),
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'version': cert['version'],
                            'not_before': cert['notBefore'],
                            'not_after': cert['notAfter']
                        },
                        'error': None
                    }
                    
        except Exception as e:
            return {
                'ssl_valid': False,
                'certificate_info': None,
                'error': str(e)
            }
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """
        包括的なヘルスチェックを実行
        
        Returns:
            Dict[str, Any]: 全体のテスト結果
        """
        print("本番環境動作確認テストを開始します...")
        
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'tests': {}
        }
        
        # 1. ヘルスチェックエンドポイント
        print("1. ヘルスチェックエンドポイントを確認中...")
        results['tests']['health_check'] = self.check_health_endpoint()
        
        # 2. データベース接続確認
        print("2. データベース接続を確認中...")
        results['tests']['database_connectivity'] = self.check_database_connectivity()
        
        # 3. APIエンドポイント確認
        print("3. 主要APIエンドポイントを確認中...")
        results['tests']['api_endpoints'] = self.check_api_endpoints()
        
        # 4. SSL証明書確認
        print("4. SSL証明書を確認中...")
        results['tests']['ssl_certificate'] = self.check_ssl_certificate()
        
        # 全体の成功率を計算
        total_tests = 0
        successful_tests = 0
        
        for test_name, test_result in results['tests'].items():
            if test_name == 'api_endpoints':
                total_tests += test_result['total_endpoints']
                successful_tests += test_result['successful_endpoints']
            else:
                total_tests += 1
                if test_result.get('success', False) or test_result.get('ssl_valid', False):
                    successful_tests += 1
        
        results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'overall_status': 'PASS' if successful_tests == total_tests else 'FAIL'
        }
        
        return results


def test_production_environment():
    """本番環境テストの実行"""
    # 環境変数から本番環境URLを取得
    prod_url = os.getenv('PRODUCTION_API_URL')
    api_key = os.getenv('PRODUCTION_API_KEY')
    
    if not prod_url:
        pytest.skip("PRODUCTION_API_URL環境変数が設定されていません")
    
    checker = ProductionHealthChecker(prod_url, api_key)
    results = checker.run_comprehensive_check()
    
    # 結果をファイルに保存
    with open('production_health_check_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 本番環境動作確認テスト結果 ===")
    print(f"テスト実行時刻: {results['timestamp']}")
    print(f"対象URL: {results['base_url']}")
    print(f"総テスト数: {results['summary']['total_tests']}")
    print(f"成功テスト数: {results['summary']['successful_tests']}")
    print(f"成功率: {results['summary']['success_rate']:.1f}%")
    print(f"全体ステータス: {results['summary']['overall_status']}")
    
    # テスト結果の詳細表示
    for test_name, test_result in results['tests'].items():
        print(f"\n--- {test_name} ---")
        if test_name == 'api_endpoints':
            for endpoint_result in test_result['results']:
                status = "✓" if endpoint_result['success'] else "✗"
                print(f"{status} {endpoint_result['method']} {endpoint_result['endpoint']}")
        else:
            success = test_result.get('success', test_result.get('ssl_valid', False))
            status = "✓" if success else "✗"
            print(f"{status} {test_name}")
            if not success and test_result.get('error'):
                print(f"  エラー: {test_result['error']}")
    
    # 全体テストが成功した場合のみパス
    assert results['summary']['overall_status'] == 'PASS', f"本番環境テストが失敗しました。成功率: {results['summary']['success_rate']:.1f}%"


if __name__ == "__main__":
    # スタンドアロン実行用
    test_production_environment()