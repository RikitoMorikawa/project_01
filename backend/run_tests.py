#!/usr/bin/env python3
"""
テスト実行スクリプト
Test execution script
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """コマンドを実行して結果を表示 / Execute command and display results"""
    print(f"\n{'='*60}")
    print(f"実行中: {description}")
    print(f"Running: {description}")
    print(f"コマンド / Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        print("✅ 成功 / Success")
        if result.stdout:
            print("標準出力 / STDOUT:")
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ 失敗 / Failed")
        print(f"終了コード / Exit code: {e.returncode}")
        
        if e.stdout:
            print("標準出力 / STDOUT:")
            print(e.stdout)
        
        if e.stderr:
            print("標準エラー / STDERR:")
            print(e.stderr)
        
        return False


def main():
    """メイン実行関数 / Main execution function"""
    print("🧪 CSR Lambda API システム テスト実行")
    print("🧪 CSR Lambda API System Test Execution")
    
    # 仮想環境の確認 / Check virtual environment
    if not os.environ.get('VIRTUAL_ENV') and not sys.prefix != sys.base_prefix:
        print("⚠️  警告: 仮想環境が有効化されていない可能性があります")
        print("⚠️  Warning: Virtual environment may not be activated")
        print("   以下のコマンドで仮想環境を有効化してください:")
        print("   Please activate virtual environment with:")
        print("   source venv/bin/activate")
        print()
    
    # テスト結果を追跡 / Track test results
    test_results = []
    
    # 1. 単体テスト実行 / Execute unit tests
    unit_test_success = run_command(
        "python -m pytest tests/test_auth_endpoints.py -v",
        "認証エンドポイント単体テスト / Authentication endpoints unit tests"
    )
    test_results.append(("認証エンドポイント単体テスト", unit_test_success))
    
    user_test_success = run_command(
        "python -m pytest tests/test_user_endpoints.py -v",
        "ユーザーエンドポイント単体テスト / User endpoints unit tests"
    )
    test_results.append(("ユーザーエンドポイント単体テスト", user_test_success))
    
    health_test_success = run_command(
        "python -m pytest tests/test_health_endpoints.py -v",
        "ヘルスチェックエンドポイント単体テスト / Health check endpoints unit tests"
    )
    test_results.append(("ヘルスチェックエンドポイント単体テスト", health_test_success))
    
    repo_test_success = run_command(
        "python -m pytest tests/test_repositories.py -v",
        "リポジトリ単体テスト / Repository unit tests"
    )
    test_results.append(("リポジトリ単体テスト", repo_test_success))
    
    cognito_test_success = run_command(
        "python -m pytest tests/test_auth_cognito.py -v",
        "Cognito認証単体テスト / Cognito authentication unit tests"
    )
    test_results.append(("Cognito認証単体テスト", cognito_test_success))
    
    # 2. 統合テスト実行 / Execute integration tests
    integration_test_success = run_command(
        "python -m pytest tests/test_integration_api.py -v",
        "API統合テスト / API integration tests"
    )
    test_results.append(("API統合テスト", integration_test_success))
    
    # 3. E2Eテスト実行 / Execute E2E tests
    e2e_test_success = run_command(
        "python -m pytest tests/test_e2e_auth_flow.py -v",
        "認証フローE2Eテスト / Authentication flow E2E tests"
    )
    test_results.append(("認証フローE2Eテスト", e2e_test_success))
    
    # 4. 全テスト実行（オプション）/ Execute all tests (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        all_test_success = run_command(
            "python -m pytest tests/ -v --tb=short",
            "全テスト実行 / All tests execution"
        )
        test_results.append(("全テスト実行", all_test_success))
    
    # 5. カバレッジレポート生成（オプション）/ Generate coverage report (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        coverage_success = run_command(
            "python -m pytest tests/ --cov=app --cov-report=html --cov-report=term",
            "カバレッジレポート生成 / Coverage report generation"
        )
        test_results.append(("カバレッジレポート", coverage_success))
    
    # 結果サマリー / Results summary
    print(f"\n{'='*60}")
    print("📊 テスト結果サマリー / Test Results Summary")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in test_results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{status} {test_name}")
    
    print(f"\n📈 統計 / Statistics:")
    print(f"   合計テスト / Total tests: {total_tests}")
    print(f"   成功 / Passed: {passed_tests}")
    print(f"   失敗 / Failed: {failed_tests}")
    print(f"   成功率 / Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 全てのテストが成功しました！")
        print("🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests}個のテストが失敗しました")
        print(f"⚠️  {failed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)