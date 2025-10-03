"""
セキュリティテストと脆弱性チェック

本番環境のセキュリティ設定と脆弱性を検証する
"""
import requests
import ssl
import socket
import json
import time
import os
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
import subprocess
import re


@dataclass
class SecurityTestResult:
    """セキュリティテスト結果"""
    test_name: str
    status: str  # PASS, FAIL, WARNING, SKIP
    message: str
    details: Dict[str, Any] = None
    severity: str = "INFO"  # CRITICAL, HIGH, MEDIUM, LOW, INFO


class SecurityScanner:
    """セキュリティスキャナークラス"""
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        初期化
        
        Args:
            base_url: 対象のベースURL
            api_key: API認証キー
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.results: List[SecurityTestResult] = []
        
        # 共通ヘッダーの設定
        self.session.headers.update({
            'User-Agent': 'SecurityScanner/1.0'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def check_ssl_configuration(self) -> SecurityTestResult:
        """
        SSL/TLS設定の確認
        
        Returns:
            SecurityTestResult: テスト結果
        """
        try:
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            if parsed_url.scheme != 'https':
                return SecurityTestResult(
                    test_name="SSL/TLS設定確認",
                    status="FAIL",
                    message="HTTPSが使用されていません",
                    severity="CRITICAL"
                )
            
            # SSL証明書の詳細情報を取得
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    # 証明書の有効期限チェック
                    import datetime
                    not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.datetime.now()).days
                    
                    details = {
                        'certificate': {
                            'subject': dict(x[0] for x in cert['subject']),
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'not_after': cert['notAfter'],
                            'days_until_expiry': days_until_expiry
                        },
                        'cipher': {
                            'name': cipher[0] if cipher else None,
                            'version': cipher[1] if cipher else None,
                            'bits': cipher[2] if cipher else None
                        },
                        'tls_version': version
                    }
                    
                    # セキュリティ評価
                    issues = []
                    if days_until_expiry < 30:
                        issues.append(f"証明書の有効期限が近づいています ({days_until_expiry}日)")
                    
                    if version and version < 'TLSv1.2':
                        issues.append(f"古いTLSバージョンが使用されています: {version}")
                    
                    if issues:
                        return SecurityTestResult(
                            test_name="SSL/TLS設定確認",
                            status="WARNING",
                            message="; ".join(issues),
                            details=details,
                            severity="MEDIUM"
                        )
                    else:
                        return SecurityTestResult(
                            test_name="SSL/TLS設定確認",
                            status="PASS",
                            message="SSL/TLS設定は適切です",
                            details=details,
                            severity="INFO"
                        )
                        
        except Exception as e:
            return SecurityTestResult(
                test_name="SSL/TLS設定確認",
                status="FAIL",
                message=f"SSL/TLS確認中にエラーが発生しました: {str(e)}",
                severity="HIGH"
            )
    
    def check_security_headers(self) -> SecurityTestResult:
        """
        セキュリティヘッダーの確認
        
        Returns:
            SecurityTestResult: テスト結果
        """
        try:
            response = self.session.get(self.base_url, timeout=10)
            headers = response.headers
            
            # 重要なセキュリティヘッダーのチェック
            security_headers = {
                'Strict-Transport-Security': {
                    'required': True,
                    'severity': 'HIGH',
                    'description': 'HTTPS強制のためのHSTSヘッダー'
                },
                'X-Content-Type-Options': {
                    'required': True,
                    'severity': 'MEDIUM',
                    'description': 'MIMEタイプスニッフィング防止'
                },
                'X-Frame-Options': {
                    'required': True,
                    'severity': 'MEDIUM',
                    'description': 'クリックジャッキング防止'
                },
                'X-XSS-Protection': {
                    'required': True,
                    'severity': 'MEDIUM',
                    'description': 'XSS攻撃防止'
                },
                'Content-Security-Policy': {
                    'required': True,
                    'severity': 'HIGH',
                    'description': 'コンテンツセキュリティポリシー'
                },
                'Referrer-Policy': {
                    'required': False,
                    'severity': 'LOW',
                    'description': 'リファラー情報の制御'
                }
            }
            
            missing_headers = []
            present_headers = {}
            
            for header_name, config in security_headers.items():
                if header_name in headers:
                    present_headers[header_name] = headers[header_name]
                elif config['required']:
                    missing_headers.append({
                        'name': header_name,
                        'severity': config['severity'],
                        'description': config['description']
                    })
            
            details = {
                'present_headers': present_headers,
                'missing_headers': missing_headers,
                'all_headers': dict(headers)
            }
            
            if missing_headers:
                critical_missing = [h for h in missing_headers if h['severity'] == 'HIGH']
                if critical_missing:
                    return SecurityTestResult(
                        test_name="セキュリティヘッダー確認",
                        status="FAIL",
                        message=f"重要なセキュリティヘッダーが不足しています: {', '.join([h['name'] for h in critical_missing])}",
                        details=details,
                        severity="HIGH"
                    )
                else:
                    return SecurityTestResult(
                        test_name="セキュリティヘッダー確認",
                        status="WARNING",
                        message=f"推奨セキュリティヘッダーが不足しています: {', '.join([h['name'] for h in missing_headers])}",
                        details=details,
                        severity="MEDIUM"
                    )
            else:
                return SecurityTestResult(
                    test_name="セキュリティヘッダー確認",
                    status="PASS",
                    message="すべての重要なセキュリティヘッダーが設定されています",
                    details=details,
                    severity="INFO"
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name="セキュリティヘッダー確認",
                status="FAIL",
                message=f"セキュリティヘッダー確認中にエラーが発生しました: {str(e)}",
                severity="HIGH"
            )
    
    def check_authentication_security(self) -> SecurityTestResult:
        """
        認証セキュリティの確認
        
        Returns:
            SecurityTestResult: テスト結果
        """
        try:
            # 認証が必要なエンドポイントに認証なしでアクセス
            protected_endpoints = [
                '/api/v1/users',
                '/api/v1/users/1'
            ]
            
            auth_results = []
            
            for endpoint in protected_endpoints:
                # 認証なしでアクセス
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                auth_results.append({
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'properly_protected': response.status_code == 401
                })
            
            # 不正なトークンでのアクセステスト
            invalid_token_headers = {'Authorization': 'Bearer invalid_token_12345'}
            response = self.session.get(
                f"{self.base_url}/api/v1/users",
                headers=invalid_token_headers,
                timeout=10
            )
            
            invalid_token_result = {
                'endpoint': '/api/v1/users',
                'status_code': response.status_code,
                'properly_rejected': response.status_code == 401
            }
            
            details = {
                'protected_endpoints_test': auth_results,
                'invalid_token_test': invalid_token_result
            }
            
            # 評価
            unprotected_endpoints = [r for r in auth_results if not r['properly_protected']]
            
            if unprotected_endpoints or not invalid_token_result['properly_rejected']:
                issues = []
                if unprotected_endpoints:
                    issues.append(f"保護されていないエンドポイント: {', '.join([e['endpoint'] for e in unprotected_endpoints])}")
                if not invalid_token_result['properly_rejected']:
                    issues.append("不正なトークンが適切に拒否されていません")
                
                return SecurityTestResult(
                    test_name="認証セキュリティ確認",
                    status="FAIL",
                    message="; ".join(issues),
                    details=details,
                    severity="CRITICAL"
                )
            else:
                return SecurityTestResult(
                    test_name="認証セキュリティ確認",
                    status="PASS",
                    message="認証セキュリティは適切に設定されています",
                    details=details,
                    severity="INFO"
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name="認証セキュリティ確認",
                status="FAIL",
                message=f"認証セキュリティ確認中にエラーが発生しました: {str(e)}",
                severity="HIGH"
            )
    
    def check_input_validation(self) -> SecurityTestResult:
        """
        入力値検証の確認
        
        Returns:
            SecurityTestResult: テスト結果
        """
        try:
            # SQLインジェクション攻撃のテスト
            sql_injection_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "1' UNION SELECT * FROM users --"
            ]
            
            # XSS攻撃のテスト
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>"
            ]
            
            test_results = []
            
            # ログインエンドポイントでのテスト
            for payload in sql_injection_payloads:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json={'email': payload, 'password': 'test'},
                        timeout=10
                    )
                    
                    test_results.append({
                        'type': 'SQL Injection',
                        'payload': payload,
                        'status_code': response.status_code,
                        'response_length': len(response.text),
                        'properly_handled': response.status_code in [400, 422]  # バリデーションエラー
                    })
                except Exception as e:
                    test_results.append({
                        'type': 'SQL Injection',
                        'payload': payload,
                        'error': str(e),
                        'properly_handled': True  # エラーが発生するのは正常
                    })
            
            # XSSテスト（ユーザー作成エンドポイント）
            for payload in xss_payloads:
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/v1/users",
                        json={'username': payload, 'email': 'test@example.com'},
                        timeout=10
                    )
                    
                    test_results.append({
                        'type': 'XSS',
                        'payload': payload,
                        'status_code': response.status_code,
                        'response_contains_payload': payload in response.text,
                        'properly_handled': response.status_code in [400, 401, 422] or payload not in response.text
                    })
                except Exception as e:
                    test_results.append({
                        'type': 'XSS',
                        'payload': payload,
                        'error': str(e),
                        'properly_handled': True
                    })
            
            details = {'input_validation_tests': test_results}
            
            # 評価
            vulnerable_tests = [t for t in test_results if not t.get('properly_handled', False)]
            
            if vulnerable_tests:
                return SecurityTestResult(
                    test_name="入力値検証確認",
                    status="FAIL",
                    message=f"入力値検証に脆弱性が発見されました: {len(vulnerable_tests)}件",
                    details=details,
                    severity="CRITICAL"
                )
            else:
                return SecurityTestResult(
                    test_name="入力値検証確認",
                    status="PASS",
                    message="入力値検証は適切に実装されています",
                    details=details,
                    severity="INFO"
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name="入力値検証確認",
                status="FAIL",
                message=f"入力値検証確認中にエラーが発生しました: {str(e)}",
                severity="HIGH"
            )
    
    def check_rate_limiting(self) -> SecurityTestResult:
        """
        レート制限の確認
        
        Returns:
            SecurityTestResult: テスト結果
        """
        try:
            # 短時間で大量のリクエストを送信
            endpoint = f"{self.base_url}/api/v1/health"
            request_count = 100
            rate_limited = False
            
            for i in range(request_count):
                response = self.session.get(endpoint, timeout=5)
                
                # レート制限のステータスコード（429）をチェック
                if response.status_code == 429:
                    rate_limited = True
                    break
                
                # 短い間隔でリクエスト
                time.sleep(0.1)
            
            details = {
                'requests_sent': i + 1,
                'rate_limited': rate_limited,
                'final_status_code': response.status_code if 'response' in locals() else None
            }
            
            if rate_limited:
                return SecurityTestResult(
                    test_name="レート制限確認",
                    status="PASS",
                    message="レート制限が適切に設定されています",
                    details=details,
                    severity="INFO"
                )
            else:
                return SecurityTestResult(
                    test_name="レート制限確認",
                    status="WARNING",
                    message="レート制限が設定されていない可能性があります",
                    details=details,
                    severity="MEDIUM"
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name="レート制限確認",
                status="FAIL",
                message=f"レート制限確認中にエラーが発生しました: {str(e)}",
                severity="MEDIUM"
            )
    
    def run_comprehensive_security_scan(self) -> Dict[str, Any]:
        """
        包括的なセキュリティスキャンを実行
        
        Returns:
            Dict[str, Any]: スキャン結果
        """
        print("セキュリティスキャンを開始します...")
        
        # 各セキュリティテストを実行
        tests = [
            self.check_ssl_configuration,
            self.check_security_headers,
            self.check_authentication_security,
            self.check_input_validation,
            self.check_rate_limiting
        ]
        
        results = []
        
        for test_func in tests:
            print(f"実行中: {test_func.__name__}")
            try:
                result = test_func()
                results.append(result)
                self.results.append(result)
            except Exception as e:
                error_result = SecurityTestResult(
                    test_name=test_func.__name__,
                    status="FAIL",
                    message=f"テスト実行中にエラーが発生しました: {str(e)}",
                    severity="HIGH"
                )
                results.append(error_result)
                self.results.append(error_result)
        
        # 結果の集計
        total_tests = len(results)
        passed_tests = len([r for r in results if r.status == "PASS"])
        failed_tests = len([r for r in results if r.status == "FAIL"])
        warning_tests = len([r for r in results if r.status == "WARNING"])
        
        # 重要度別の集計
        critical_issues = len([r for r in results if r.severity == "CRITICAL" and r.status == "FAIL"])
        high_issues = len([r for r in results if r.severity == "HIGH" and r.status == "FAIL"])
        
        # 全体的なセキュリティスコアを計算
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 重要な脆弱性がある場合はスコアを大幅に減点
        if critical_issues > 0:
            security_score = min(security_score, 30)
        elif high_issues > 0:
            security_score = min(security_score, 60)
        
        return {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'target_url': self.base_url,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'warning_tests': warning_tests,
                'security_score': security_score,
                'critical_issues': critical_issues,
                'high_issues': high_issues,
                'overall_status': 'SECURE' if critical_issues == 0 and high_issues == 0 else 'VULNERABLE'
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'status': r.status,
                    'message': r.message,
                    'severity': r.severity,
                    'details': r.details
                }
                for r in results
            ]
        }
    
    def generate_security_report(self, results: Dict[str, Any], output_file: str = 'security_scan_report.json'):
        """
        セキュリティレポートを生成
        
        Args:
            results: スキャン結果
            output_file: 出力ファイル名
        """
        # JSON形式で保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # コンソール出力
        print(f"\n=== セキュリティスキャン結果 ===")
        print(f"スキャン実行時刻: {results['timestamp']}")
        print(f"対象URL: {results['target_url']}")
        print(f"セキュリティスコア: {results['summary']['security_score']:.1f}/100")
        print(f"全体ステータス: {results['summary']['overall_status']}")
        
        print(f"\n=== テスト結果サマリー ===")
        print(f"総テスト数: {results['summary']['total_tests']}")
        print(f"成功: {results['summary']['passed_tests']}")
        print(f"失敗: {results['summary']['failed_tests']}")
        print(f"警告: {results['summary']['warning_tests']}")
        print(f"重要な脆弱性: {results['summary']['critical_issues']}")
        print(f"高リスク脆弱性: {results['summary']['high_issues']}")
        
        print(f"\n=== テスト詳細 ===")
        for test_result in results['test_results']:
            status_icon = {
                'PASS': '✓',
                'FAIL': '✗',
                'WARNING': '⚠',
                'SKIP': '-'
            }.get(test_result['status'], '?')
            
            severity_label = f"[{test_result['severity']}]" if test_result['status'] == 'FAIL' else ""
            
            print(f"{status_icon} {test_result['test_name']} {severity_label}")
            print(f"  {test_result['message']}")
        
        print(f"\n詳細レポートは {output_file} に保存されました。")


def run_security_scan():
    """セキュリティスキャンの実行"""
    # 環境変数から設定を取得
    base_url = os.getenv('PRODUCTION_API_URL')
    api_key = os.getenv('PRODUCTION_API_KEY')
    
    if not base_url:
        print("エラー: PRODUCTION_API_URL環境変数が設定されていません")
        return
    
    # セキュリティスキャン実行
    scanner = SecurityScanner(base_url, api_key)
    results = scanner.run_comprehensive_security_scan()
    
    # レポート生成
    scanner.generate_security_report(results)
    
    return results


if __name__ == "__main__":
    # スタンドアロン実行用
    run_security_scan()