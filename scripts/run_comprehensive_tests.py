#!/usr/bin/env python3
"""
包括的テスト実行スクリプト

本番環境での最終統合テストと検証を自動実行する
"""
import os
import sys
import json
import time
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import argparse


@dataclass
class TestResult:
    """テスト結果"""
    name: str
    status: str  # PASS, FAIL, SKIP
    duration: float
    details: Dict[str, Any] = None
    error: str = None


class ComprehensiveTestRunner:
    """包括的テストランナー"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初期化
        
        Args:
            config: テスト設定
        """
        self.config = config
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        
        # プロジェクトルートディレクトリの設定
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
    
    def run_command(self, command: List[str], cwd: Path = None, timeout: int = 300) -> Dict[str, Any]:
        """
        コマンドを実行
        
        Args:
            command: 実行するコマンド
            cwd: 作業ディレクトリ
            timeout: タイムアウト（秒）
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            start_time = time.time()
            
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'コマンドがタイムアウトしました ({timeout}秒)',
                'duration': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0
            }
    
    def run_backend_unit_tests(self) -> TestResult:
        """
        バックエンド単体テストの実行
        
        Returns:
            TestResult: テスト結果
        """
        print("バックエンド単体テストを実行中...")
        
        start_time = time.time()
        
        # 依存関係のインストール
        install_result = self.run_command(
            ['pip', 'install', '-r', 'requirements.txt'],
            cwd=self.backend_dir
        )
        
        if not install_result['success']:
            return TestResult(
                name="バックエンド単体テスト",
                status="FAIL",
                duration=time.time() - start_time,
                error=f"依存関係のインストールに失敗: {install_result['stderr']}"
            )
        
        # 単体テストの実行
        test_result = self.run_command(
            ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            cwd=self.backend_dir,
            timeout=600
        )
        
        duration = time.time() - start_time
        
        if test_result['success']:
            return TestResult(
                name="バックエンド単体テスト",
                status="PASS",
                duration=duration,
                details={
                    'stdout': test_result['stdout'],
                    'test_count': test_result['stdout'].count('PASSED')
                }
            )
        else:
            return TestResult(
                name="バックエンド単体テスト",
                status="FAIL",
                duration=duration,
                error=test_result['stderr'],
                details={'stdout': test_result['stdout']}
            )
    
    def run_frontend_unit_tests(self) -> TestResult:
        """
        フロントエンド単体テストの実行
        
        Returns:
            TestResult: テスト結果
        """
        print("フロントエンド単体テストを実行中...")
        
        start_time = time.time()
        
        # 依存関係のインストール
        install_result = self.run_command(
            ['npm', 'ci'],
            cwd=self.frontend_dir
        )
        
        if not install_result['success']:
            return TestResult(
                name="フロントエンド単体テスト",
                status="FAIL",
                duration=time.time() - start_time,
                error=f"依存関係のインストールに失敗: {install_result['stderr']}"
            )
        
        # 単体テストの実行
        test_result = self.run_command(
            ['npm', 'test', '--', '--watchAll=false', '--coverage'],
            cwd=self.frontend_dir,
            timeout=600
        )
        
        duration = time.time() - start_time
        
        if test_result['success']:
            return TestResult(
                name="フロントエンド単体テスト",
                status="PASS",
                duration=duration,
                details={
                    'stdout': test_result['stdout'],
                    'coverage_info': 'カバレッジレポートが生成されました'
                }
            )
        else:
            return TestResult(
                name="フロントエンド単体テスト",
                status="FAIL",
                duration=duration,
                error=test_result['stderr'],
                details={'stdout': test_result['stdout']}
            )
    
    async def run_production_health_check(self) -> TestResult:
        """
        本番環境ヘルスチェックの実行
        
        Returns:
            TestResult: テスト結果
        """
        print("本番環境ヘルスチェックを実行中...")
        
        start_time = time.time()
        
        try:
            # 本番環境ヘルスチェックスクリプトの実行
            sys.path.append(str(self.backend_dir))
            from tests.production.test_production_health import ProductionHealthChecker
            
            base_url = self.config.get('production_api_url')
            api_key = self.config.get('production_api_key')
            
            if not base_url:
                return TestResult(
                    name="本番環境ヘルスチェック",
                    status="SKIP",
                    duration=0,
                    error="PRODUCTION_API_URL が設定されていません"
                )
            
            checker = ProductionHealthChecker(base_url, api_key)
            results = checker.run_comprehensive_check()
            
            duration = time.time() - start_time
            
            if results['summary']['overall_status'] == 'PASS':
                return TestResult(
                    name="本番環境ヘルスチェック",
                    status="PASS",
                    duration=duration,
                    details=results
                )
            else:
                return TestResult(
                    name="本番環境ヘルスチェック",
                    status="FAIL",
                    duration=duration,
                    error=f"成功率: {results['summary']['success_rate']:.1f}%",
                    details=results
                )
                
        except Exception as e:
            return TestResult(
                name="本番環境ヘルスチェック",
                status="FAIL",
                duration=time.time() - start_time,
                error=str(e)
            )
    
    async def run_performance_test(self) -> TestResult:
        """
        パフォーマンステストの実行
        
        Returns:
            TestResult: テスト結果
        """
        print("パフォーマンステストを実行中...")
        
        start_time = time.time()
        
        try:
            # パフォーマンステストスクリプトの実行
            sys.path.append(str(self.backend_dir))
            from tests.performance.load_test import run_performance_test
            
            base_url = self.config.get('production_api_url')
            
            if not base_url:
                return TestResult(
                    name="パフォーマンステスト",
                    status="SKIP",
                    duration=0,
                    error="PRODUCTION_API_URL が設定されていません"
                )
            
            # 環境変数の設定
            os.environ['PRODUCTION_API_URL'] = base_url
            if self.config.get('production_api_key'):
                os.environ['PRODUCTION_API_KEY'] = self.config['production_api_key']
            
            # 軽量なテスト設定
            os.environ['LOAD_TEST_USERS'] = str(self.config.get('load_test_users', 5))
            os.environ['LOAD_TEST_REQUESTS_PER_USER'] = str(self.config.get('load_test_requests', 10))
            os.environ['LOAD_TEST_RAMP_UP'] = str(self.config.get('load_test_ramp_up', 10))
            
            results = await run_performance_test()
            
            duration = time.time() - start_time
            
            # パフォーマンス基準の評価
            success_rate = results['summary']['success_rate']
            avg_response_time = results['response_time_stats']['avg']
            
            if success_rate >= 95 and avg_response_time <= 2.0:
                status = "PASS"
                error = None
            elif success_rate >= 90 and avg_response_time <= 5.0:
                status = "PASS"
                error = "パフォーマンスが基準を下回っていますが許容範囲内です"
            else:
                status = "FAIL"
                error = f"パフォーマンス基準未達: 成功率{success_rate:.1f}%, 平均応答時間{avg_response_time:.3f}秒"
            
            return TestResult(
                name="パフォーマンステスト",
                status=status,
                duration=duration,
                error=error,
                details=results
            )
            
        except Exception as e:
            return TestResult(
                name="パフォーマンステスト",
                status="FAIL",
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def run_security_scan(self) -> TestResult:
        """
        セキュリティスキャンの実行
        
        Returns:
            TestResult: テスト結果
        """
        print("セキュリティスキャンを実行中...")
        
        start_time = time.time()
        
        try:
            # セキュリティスキャンスクリプトの実行
            sys.path.append(str(self.backend_dir))
            from tests.security.security_scanner import run_security_scan
            
            base_url = self.config.get('production_api_url')
            
            if not base_url:
                return TestResult(
                    name="セキュリティスキャン",
                    status="SKIP",
                    duration=0,
                    error="PRODUCTION_API_URL が設定されていません"
                )
            
            # 環境変数の設定
            os.environ['PRODUCTION_API_URL'] = base_url
            if self.config.get('production_api_key'):
                os.environ['PRODUCTION_API_KEY'] = self.config['production_api_key']
            
            results = run_security_scan()
            
            duration = time.time() - start_time
            
            # セキュリティ評価
            security_score = results['summary']['security_score']
            critical_issues = results['summary']['critical_issues']
            
            if critical_issues == 0 and security_score >= 80:
                status = "PASS"
                error = None
            elif critical_issues == 0 and security_score >= 60:
                status = "PASS"
                error = "セキュリティスコアが低めですが重要な脆弱性はありません"
            else:
                status = "FAIL"
                error = f"セキュリティ問題: スコア{security_score:.1f}, 重要な脆弱性{critical_issues}件"
            
            return TestResult(
                name="セキュリティスキャン",
                status=status,
                duration=duration,
                error=error,
                details=results
            )
            
        except Exception as e:
            return TestResult(
                name="セキュリティスキャン",
                status="FAIL",
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def run_build_verification(self) -> TestResult:
        """
        ビルド検証テストの実行
        
        Returns:
            TestResult: テスト結果
        """
        print("ビルド検証テストを実行中...")
        
        start_time = time.time()
        
        # フロントエンドビルドの確認
        build_result = self.run_command(
            ['npm', 'run', 'build'],
            cwd=self.frontend_dir,
            timeout=300
        )
        
        duration = time.time() - start_time
        
        if build_result['success']:
            # ビルド成果物の確認
            build_dir = self.frontend_dir / '.next'
            if build_dir.exists():
                return TestResult(
                    name="ビルド検証テスト",
                    status="PASS",
                    duration=duration,
                    details={
                        'build_output': build_result['stdout'],
                        'build_size': 'ビルド成果物が正常に生成されました'
                    }
                )
            else:
                return TestResult(
                    name="ビルド検証テスト",
                    status="FAIL",
                    duration=duration,
                    error="ビルド成果物が生成されませんでした"
                )
        else:
            return TestResult(
                name="ビルド検証テスト",
                status="FAIL",
                duration=duration,
                error=build_result['stderr'],
                details={'stdout': build_result['stdout']}
            )
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        包括的テストの実行
        
        Returns:
            Dict[str, Any]: 全体のテスト結果
        """
        print("=== 包括的テスト実行を開始します ===")
        self.start_time = time.time()
        
        # テストの実行順序
        test_functions = [
            ('ビルド検証', self.run_build_verification),
            ('バックエンド単体テスト', self.run_backend_unit_tests),
            ('フロントエンド単体テスト', self.run_frontend_unit_tests),
            ('本番環境ヘルスチェック', self.run_production_health_check),
            ('パフォーマンステスト', self.run_performance_test),
            ('セキュリティスキャン', self.run_security_scan),
        ]
        
        for test_name, test_func in test_functions:
            print(f"\n--- {test_name} ---")
            
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                self.results.append(result)
                
                # 結果の表示
                status_icon = "✓" if result.status == "PASS" else "✗" if result.status == "FAIL" else "⚠"
                print(f"{status_icon} {result.name}: {result.status} ({result.duration:.2f}秒)")
                
                if result.error:
                    print(f"  エラー: {result.error}")
                
                # 重要なテストが失敗した場合は早期終了するかどうか
                if result.status == "FAIL" and self.config.get('fail_fast', False):
                    print(f"重要なテスト '{result.name}' が失敗したため、テストを中断します。")
                    break
                    
            except Exception as e:
                error_result = TestResult(
                    name=test_name,
                    status="FAIL",
                    duration=0,
                    error=f"テスト実行中に予期しないエラーが発生しました: {str(e)}"
                )
                self.results.append(error_result)
                print(f"✗ {test_name}: FAIL (エラー)")
                print(f"  エラー: {str(e)}")
        
        self.end_time = time.time()
        
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        テスト結果のサマリーを生成
        
        Returns:
            Dict[str, Any]: サマリー情報
        """
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        skipped_tests = len([r for r in self.results if r.status == "SKIP"])
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # 全体的な成功判定
        critical_failures = [r for r in self.results if r.status == "FAIL" and r.name in [
            "本番環境ヘルスチェック", "セキュリティスキャン"
        ]]
        
        overall_status = "PASS" if failed_tests == 0 else "FAIL"
        if critical_failures:
            overall_status = "CRITICAL_FAIL"
        
        summary = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration': total_duration,
            'overall_status': overall_status,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'skipped_tests': skipped_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'test_results': [
                {
                    'name': r.name,
                    'status': r.status,
                    'duration': r.duration,
                    'error': r.error,
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any], output_file: str = 'comprehensive_test_report.json'):
        """
        テストレポートを生成
        
        Args:
            summary: テスト結果サマリー
            output_file: 出力ファイル名
        """
        # JSON形式で保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # コンソール出力
        print(f"\n{'='*60}")
        print(f"包括的テスト結果サマリー")
        print(f"{'='*60}")
        print(f"実行時刻: {summary['timestamp']}")
        print(f"総実行時間: {summary['total_duration']:.2f}秒")
        print(f"全体ステータス: {summary['overall_status']}")
        
        print(f"\n--- テスト結果 ---")
        print(f"総テスト数: {summary['summary']['total_tests']}")
        print(f"成功: {summary['summary']['passed_tests']}")
        print(f"失敗: {summary['summary']['failed_tests']}")
        print(f"スキップ: {summary['summary']['skipped_tests']}")
        print(f"成功率: {summary['summary']['success_rate']:.1f}%")
        
        print(f"\n--- 詳細結果 ---")
        for result in summary['test_results']:
            status_icon = {
                'PASS': '✓',
                'FAIL': '✗',
                'SKIP': '⚠'
            }.get(result['status'], '?')
            
            print(f"{status_icon} {result['name']}: {result['status']} ({result['duration']:.2f}秒)")
            if result['error']:
                print(f"  エラー: {result['error']}")
        
        # 推奨事項
        if summary['overall_status'] == "FAIL":
            print(f"\n--- 推奨事項 ---")
            failed_results = [r for r in summary['test_results'] if r['status'] == 'FAIL']
            for result in failed_results:
                print(f"• {result['name']}: {result['error']}")
        
        print(f"\n詳細レポートは {output_file} に保存されました。")


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='包括的テスト実行スクリプト')
    parser.add_argument('--config', '-c', default='test_config.json', help='設定ファイルのパス')
    parser.add_argument('--production-url', help='本番環境URL')
    parser.add_argument('--api-key', help='API認証キー')
    parser.add_argument('--fail-fast', action='store_true', help='重要なテスト失敗時に早期終了')
    parser.add_argument('--output', '-o', default='comprehensive_test_report.json', help='出力ファイル名')
    
    args = parser.parse_args()
    
    # 設定の読み込み
    config = {}
    
    # 設定ファイルから読み込み
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # コマンドライン引数で上書き
    if args.production_url:
        config['production_api_url'] = args.production_url
    if args.api_key:
        config['production_api_key'] = args.api_key
    if args.fail_fast:
        config['fail_fast'] = True
    
    # 環境変数から設定を取得
    config.setdefault('production_api_url', os.getenv('PRODUCTION_API_URL'))
    config.setdefault('production_api_key', os.getenv('PRODUCTION_API_KEY'))
    config.setdefault('load_test_users', int(os.getenv('LOAD_TEST_USERS', '5')))
    config.setdefault('load_test_requests', int(os.getenv('LOAD_TEST_REQUESTS_PER_USER', '10')))
    config.setdefault('load_test_ramp_up', int(os.getenv('LOAD_TEST_RAMP_UP', '10')))
    
    # テスト実行
    runner = ComprehensiveTestRunner(config)
    summary = await runner.run_comprehensive_tests()
    
    # レポート生成
    runner.generate_report(summary, args.output)
    
    # 終了コード
    if summary['overall_status'] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())