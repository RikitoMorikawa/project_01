#!/bin/bash

# 最終統合テストと検証実行スクリプト
# 本番環境での動作確認、パフォーマンステスト、セキュリティテストを実行

set -e  # エラー時に終了

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# カラー出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ヘルプ表示
show_help() {
    cat << EOF
最終統合テストと検証実行スクリプト

使用方法:
    $0 [オプション]

オプション:
    -h, --help              このヘルプを表示
    -u, --url URL          本番環境のAPI URL
    -k, --api-key KEY      API認証キー
    -c, --config FILE      設定ファイルのパス (デフォルト: test_config.json)
    -o, --output FILE      出力ファイル名 (デフォルト: comprehensive_test_report.json)
    --fail-fast            重要なテスト失敗時に早期終了
    --skip-unit-tests      単体テストをスキップ
    --skip-performance     パフォーマンステストをスキップ
    --skip-security        セキュリティテストをスキップ
    --light-load           軽量な負荷テストを実行

例:
    $0 --url https://api.example.com --api-key your-key
    $0 --config prod_test_config.json --fail-fast
    $0 --light-load --skip-unit-tests

環境変数:
    PRODUCTION_API_URL     本番環境のAPI URL
    PRODUCTION_API_KEY     API認証キー
    LOAD_TEST_USERS        負荷テストの同時ユーザー数
    LOAD_TEST_REQUESTS_PER_USER  ユーザーあたりのリクエスト数
EOF
}

# デフォルト値
CONFIG_FILE="test_config.json"
OUTPUT_FILE="comprehensive_test_report.json"
PRODUCTION_URL=""
API_KEY=""
FAIL_FAST=false
SKIP_UNIT_TESTS=false
SKIP_PERFORMANCE=false
SKIP_SECURITY=false
LIGHT_LOAD=false

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--url)
            PRODUCTION_URL="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --skip-unit-tests)
            SKIP_UNIT_TESTS=true
            shift
            ;;
        --skip-performance)
            SKIP_PERFORMANCE=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --light-load)
            LIGHT_LOAD=true
            shift
            ;;
        *)
            log_error "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# 前提条件のチェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # Python のチェック
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 が見つかりません"
        exit 1
    fi
    
    # Node.js のチェック
    if ! command -v node &> /dev/null; then
        log_error "Node.js が見つかりません"
        exit 1
    fi
    
    # npm のチェック
    if ! command -v npm &> /dev/null; then
        log_error "npm が見つかりません"
        exit 1
    fi
    
    # pip のチェック
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        log_error "pip が見つかりません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# 環境変数の設定
setup_environment() {
    log_info "環境変数を設定中..."
    
    # 本番環境URL
    if [[ -n "$PRODUCTION_URL" ]]; then
        export PRODUCTION_API_URL="$PRODUCTION_URL"
    elif [[ -z "$PRODUCTION_API_URL" ]]; then
        log_warning "本番環境URLが設定されていません。一部のテストがスキップされます。"
    fi
    
    # API キー
    if [[ -n "$API_KEY" ]]; then
        export PRODUCTION_API_KEY="$API_KEY"
    fi
    
    # 軽量負荷テストの設定
    if [[ "$LIGHT_LOAD" == true ]]; then
        export LOAD_TEST_USERS=5
        export LOAD_TEST_REQUESTS_PER_USER=10
        export LOAD_TEST_RAMP_UP=10
        log_info "軽量負荷テスト設定を適用しました"
    fi
    
    log_success "環境変数設定完了"
}

# 依存関係のインストール
install_dependencies() {
    log_info "依存関係をインストール中..."
    
    # バックエンド依存関係
    if [[ "$SKIP_UNIT_TESTS" != true ]]; then
        log_info "バックエンド依存関係をインストール中..."
        cd "$PROJECT_ROOT/backend"
        
        # 仮想環境の作成（存在しない場合）
        if [[ ! -d "venv" ]]; then
            python3 -m venv venv
        fi
        
        # 仮想環境の有効化
        source venv/bin/activate
        
        # 依存関係のインストール
        pip install -r requirements.txt
        
        cd "$PROJECT_ROOT"
    fi
    
    # フロントエンド依存関係
    if [[ "$SKIP_UNIT_TESTS" != true ]]; then
        log_info "フロントエンド依存関係をインストール中..."
        cd "$PROJECT_ROOT/frontend"
        npm ci
        cd "$PROJECT_ROOT"
    fi
    
    log_success "依存関係インストール完了"
}

# 単体テストの実行
run_unit_tests() {
    if [[ "$SKIP_UNIT_TESTS" == true ]]; then
        log_info "単体テストをスキップしました"
        return 0
    fi
    
    log_info "単体テストを実行中..."
    
    # バックエンド単体テスト
    log_info "バックエンド単体テストを実行中..."
    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate
    
    if python -m pytest tests/ -v --tb=short; then
        log_success "バックエンド単体テスト完了"
    else
        log_error "バックエンド単体テストが失敗しました"
        if [[ "$FAIL_FAST" == true ]]; then
            exit 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
    
    # フロントエンド単体テスト
    log_info "フロントエンド単体テストを実行中..."
    cd "$PROJECT_ROOT/frontend"
    
    if npm test -- --watchAll=false --coverage; then
        log_success "フロントエンド単体テスト完了"
    else
        log_error "フロントエンド単体テストが失敗しました"
        if [[ "$FAIL_FAST" == true ]]; then
            exit 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
}

# 包括的テストの実行
run_comprehensive_tests() {
    log_info "包括的テストを実行中..."
    
    cd "$PROJECT_ROOT"
    
    # Python スクリプトの実行
    PYTHON_ARGS=()
    
    if [[ -n "$CONFIG_FILE" ]]; then
        PYTHON_ARGS+=(--config "$CONFIG_FILE")
    fi
    
    if [[ -n "$OUTPUT_FILE" ]]; then
        PYTHON_ARGS+=(--output "$OUTPUT_FILE")
    fi
    
    if [[ -n "$PRODUCTION_URL" ]]; then
        PYTHON_ARGS+=(--production-url "$PRODUCTION_URL")
    fi
    
    if [[ -n "$API_KEY" ]]; then
        PYTHON_ARGS+=(--api-key "$API_KEY")
    fi
    
    if [[ "$FAIL_FAST" == true ]]; then
        PYTHON_ARGS+=(--fail-fast)
    fi
    
    # 仮想環境の有効化
    if [[ -d "backend/venv" ]]; then
        source backend/venv/bin/activate
    fi
    
    # 包括的テストの実行
    if python3 scripts/run_comprehensive_tests.py "${PYTHON_ARGS[@]}"; then
        log_success "包括的テスト完了"
        return 0
    else
        log_error "包括的テストが失敗しました"
        return 1
    fi
}

# 結果の表示
show_results() {
    log_info "テスト結果を表示中..."
    
    if [[ -f "$OUTPUT_FILE" ]]; then
        # JSON ファイルから結果を抽出して表示
        if command -v jq &> /dev/null; then
            echo
            echo "=== テスト結果サマリー ==="
            jq -r '.summary | "総テスト数: \(.total_tests), 成功: \(.passed_tests), 失敗: \(.failed_tests), 成功率: \(.success_rate)%"' "$OUTPUT_FILE"
            
            echo
            echo "=== 失敗したテスト ==="
            jq -r '.test_results[] | select(.status == "FAIL") | "- \(.name): \(.error // "詳細不明")"' "$OUTPUT_FILE"
        else
            log_info "詳細な結果は $OUTPUT_FILE を確認してください"
        fi
    else
        log_warning "結果ファイルが見つかりません: $OUTPUT_FILE"
    fi
}

# クリーンアップ
cleanup() {
    log_info "クリーンアップ中..."
    
    # 一時ファイルの削除
    rm -f /tmp/test_*.log
    
    # テスト用データベースファイルの削除
    rm -f backend/test.db
    
    log_success "クリーンアップ完了"
}

# メイン実行
main() {
    log_info "最終統合テストと検証を開始します"
    echo "設定:"
    echo "  設定ファイル: $CONFIG_FILE"
    echo "  出力ファイル: $OUTPUT_FILE"
    echo "  本番環境URL: ${PRODUCTION_API_URL:-'未設定'}"
    echo "  早期終了: $FAIL_FAST"
    echo "  軽量負荷テスト: $LIGHT_LOAD"
    echo
    
    # 実行開始時刻
    START_TIME=$(date +%s)
    
    # 各ステップの実行
    check_prerequisites
    setup_environment
    install_dependencies
    run_unit_tests
    
    # 包括的テストの実行
    if run_comprehensive_tests; then
        TEST_RESULT=0
        log_success "すべてのテストが完了しました"
    else
        TEST_RESULT=1
        log_error "一部のテストが失敗しました"
    fi
    
    # 結果の表示
    show_results
    
    # 実行時間の計算
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo
    log_info "総実行時間: ${DURATION}秒"
    
    # クリーンアップ
    cleanup
    
    # 終了
    if [[ $TEST_RESULT -eq 0 ]]; then
        log_success "最終統合テストと検証が正常に完了しました"
        exit 0
    else
        log_error "最終統合テストと検証で問題が発見されました"
        exit 1
    fi
}

# シグナルハンドリング
trap cleanup EXIT

# メイン実行
main "$@"