#!/bin/bash

# セキュリティテストスクリプト
# CI/CD パイプラインで実行されるセキュリティテストを自動化

set -e

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
REPORTS_DIR="$PROJECT_ROOT/security-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 使用方法
usage() {
    cat << EOF
使用方法: $0 [オプション]

オプション:
    -u, --url URL           テスト対象のベース URL（デフォルト: http://localhost:8000）
    -e, --environment ENV   環境名（dev, staging, prod）
    -s, --skip-unit        単体テストをスキップ
    -v, --verbose          詳細ログを出力
    -h, --help             このヘルプを表示

例:
    $0 --url https://api.example.com --environment prod
    $0 --skip-unit --verbose
EOF
}

# デフォルト設定
BASE_URL="http://localhost:8000"
ENVIRONMENT="dev"
SKIP_UNIT_TESTS=false
VERBOSE=false

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--skip-unit)
            SKIP_UNIT_TESTS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            usage
            exit 1
            ;;
    esac
done

# レポートディレクトリの作成
mkdir -p "$REPORTS_DIR"

log_info "セキュリティテストを開始します"
log_info "対象URL: $BASE_URL"
log_info "環境: $ENVIRONMENT"
log_info "レポート出力先: $REPORTS_DIR"

# Python 仮想環境の確認
check_python_env() {
    log_info "Python 環境を確認中..."
    
    cd "$BACKEND_DIR"
    
    if [[ ! -d "venv" ]]; then
        log_warning "Python 仮想環境が見つかりません。作成中..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # 依存関係のインストール
    if [[ -f "requirements.txt" ]]; then
        log_info "依存関係をインストール中..."
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    # テスト用の追加依存関係
    pip install pytest pytest-cov pytest-asyncio requests > /dev/null 2>&1
    
    log_success "Python 環境の準備が完了しました"
}

# 単体テストの実行
run_unit_tests() {
    if [[ "$SKIP_UNIT_TESTS" == "true" ]]; then
        log_info "単体テストをスキップします"
        return 0
    fi
    
    log_info "セキュリティ関連の単体テストを実行中..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # セキュリティミドルウェアのテスト
    if [[ -f "tests/security/test_security_middleware.py" ]]; then
        log_info "セキュリティミドルウェアのテストを実行中..."
        
        if [[ "$VERBOSE" == "true" ]]; then
            pytest tests/security/test_security_middleware.py -v \
                --cov=app.middleware.security \
                --cov-report=html:$REPORTS_DIR/coverage_security_$TIMESTAMP \
                --cov-report=term
        else
            pytest tests/security/test_security_middleware.py \
                --cov=app.middleware.security \
                --cov-report=html:$REPORTS_DIR/coverage_security_$TIMESTAMP \
                > "$REPORTS_DIR/unit_tests_$TIMESTAMP.log" 2>&1
        fi
        
        if [[ $? -eq 0 ]]; then
            log_success "セキュリティミドルウェアのテストが成功しました"
        else
            log_error "セキュリティミドルウェアのテストが失敗しました"
            if [[ "$VERBOSE" == "false" ]]; then
                log_info "詳細ログ: $REPORTS_DIR/unit_tests_$TIMESTAMP.log"
            fi
            return 1
        fi
    else
        log_warning "セキュリティミドルウェアのテストファイルが見つかりません"
    fi
    
    # 認証関連のテスト
    if [[ -f "tests/test_auth_cognito.py" ]]; then
        log_info "認証機能のテストを実行中..."
        
        if [[ "$VERBOSE" == "true" ]]; then
            pytest tests/test_auth_cognito.py -v
        else
            pytest tests/test_auth_cognito.py >> "$REPORTS_DIR/unit_tests_$TIMESTAMP.log" 2>&1
        fi
        
        if [[ $? -eq 0 ]]; then
            log_success "認証機能のテストが成功しました"
        else
            log_error "認証機能のテストが失敗しました"
            return 1
        fi
    fi
    
    log_success "単体テストが完了しました"
}

# 脆弱性スキャンの実行
run_vulnerability_scan() {
    log_info "脆弱性スキャンを実行中..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # 脆弱性スキャナーの実行
    if [[ -f "tests/security/vulnerability_scanner.py" ]]; then
        local scan_report="$REPORTS_DIR/vulnerability_scan_$TIMESTAMP.md"
        
        log_info "対象URL: $BASE_URL でスキャンを開始..."
        
        if [[ "$VERBOSE" == "true" ]]; then
            python tests/security/vulnerability_scanner.py "$BASE_URL" --output "$scan_report" --timeout 15
        else
            python tests/security/vulnerability_scanner.py "$BASE_URL" --output "$scan_report" --timeout 15 \
                > "$REPORTS_DIR/vulnerability_scan_$TIMESTAMP.log" 2>&1
        fi
        
        local scan_result=$?
        
        if [[ $scan_result -eq 0 ]]; then
            log_success "脆弱性スキャンが完了しました（重要な問題なし）"
        elif [[ $scan_result -eq 1 ]]; then
            log_warning "脆弱性スキャンで重要な問題が検出されました"
            log_info "詳細レポート: $scan_report"
            
            # 重要な脆弱性の概要を表示
            if [[ -f "$scan_report" ]]; then
                log_info "検出された重要な問題:"
                grep -A 2 "CRITICAL\|HIGH" "$scan_report" | head -20
            fi
            
            return 1
        else
            log_error "脆弱性スキャンでエラーが発生しました"
            if [[ "$VERBOSE" == "false" ]]; then
                log_info "詳細ログ: $REPORTS_DIR/vulnerability_scan_$TIMESTAMP.log"
            fi
            return 1
        fi
    else
        log_error "脆弱性スキャナーが見つかりません"
        return 1
    fi
}

# セキュリティ設定の検証
verify_security_config() {
    log_info "セキュリティ設定を検証中..."
    
    local config_issues=0
    
    # 環境変数の確認
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        log_info "本番環境のセキュリティ設定を確認中..."
        
        # 重要な環境変数の存在確認
        local required_vars=("DATABASE_SECRET_ARN" "JWT_SECRET_KEY" "CORS_ORIGINS")
        
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var}" ]]; then
                log_warning "環境変数 $var が設定されていません"
                ((config_issues++))
            fi
        done
        
        # CORS 設定の確認
        if [[ "${CORS_ORIGINS}" == "*" ]]; then
            log_warning "本番環境で CORS_ORIGINS がワイルドカードに設定されています"
            ((config_issues++))
        fi
        
        # デバッグモードの確認
        if [[ "${DEBUG}" == "true" || "${DEBUG}" == "1" ]]; then
            log_error "本番環境でデバッグモードが有効になっています"
            ((config_issues++))
        fi
    fi
    
    # インフラストラクチャ設定の確認
    local infra_dir="$PROJECT_ROOT/infrastructure/$ENVIRONMENT"
    if [[ -d "$infra_dir" ]]; then
        log_info "インフラストラクチャ設定を確認中..."
        
        # WAF 設定の確認
        if [[ -f "$infra_dir/waf-api.yaml" ]]; then
            if grep -q "WAFEnabled.*true" "$infra_dir/waf-api.yaml"; then
                log_success "WAF が有効になっています"
            else
                log_warning "WAF が無効になっている可能性があります"
                ((config_issues++))
            fi
        else
            log_warning "WAF 設定ファイルが見つかりません"
            ((config_issues++))
        fi
        
        # セキュリティグループの確認
        if [[ -f "$infra_dir/main.yaml" ]]; then
            if grep -q "SecurityGroup" "$infra_dir/main.yaml"; then
                log_success "セキュリティグループが設定されています"
            else
                log_warning "セキュリティグループの設定が見つかりません"
                ((config_issues++))
            fi
        fi
    fi
    
    if [[ $config_issues -eq 0 ]]; then
        log_success "セキュリティ設定の検証が完了しました"
        return 0
    else
        log_warning "セキュリティ設定で $config_issues 件の問題が見つかりました"
        return 1
    fi
}

# 依存関係の脆弱性チェック
check_dependency_vulnerabilities() {
    log_info "依存関係の脆弱性をチェック中..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Python 依存関係の脆弱性チェック
    if command -v safety &> /dev/null; then
        log_info "Safety を使用して Python 依存関係をチェック中..."
        
        local safety_report="$REPORTS_DIR/safety_check_$TIMESTAMP.txt"
        
        if safety check --output text > "$safety_report" 2>&1; then
            log_success "Python 依存関係に既知の脆弱性は見つかりませんでした"
        else
            log_warning "Python 依存関係で脆弱性が検出されました"
            log_info "詳細レポート: $safety_report"
            
            if [[ "$VERBOSE" == "true" ]]; then
                cat "$safety_report"
            fi
        fi
    else
        log_info "Safety をインストール中..."
        pip install safety > /dev/null 2>&1
        
        local safety_report="$REPORTS_DIR/safety_check_$TIMESTAMP.txt"
        
        if safety check --output text > "$safety_report" 2>&1; then
            log_success "Python 依存関係に既知の脆弱性は見つかりませんでした"
        else
            log_warning "Python 依存関係で脆弱性が検出されました"
            log_info "詳細レポート: $safety_report"
        fi
    fi
    
    # Node.js 依存関係の脆弱性チェック（フロントエンドがある場合）
    local frontend_dir="$PROJECT_ROOT/frontend"
    if [[ -d "$frontend_dir" && -f "$frontend_dir/package.json" ]]; then
        log_info "Node.js 依存関係の脆弱性をチェック中..."
        
        cd "$frontend_dir"
        
        if command -v npm &> /dev/null; then
            local npm_audit_report="$REPORTS_DIR/npm_audit_$TIMESTAMP.json"
            
            if npm audit --json > "$npm_audit_report" 2>&1; then
                local vulnerabilities=$(jq '.metadata.vulnerabilities.total' "$npm_audit_report" 2>/dev/null || echo "0")
                
                if [[ "$vulnerabilities" -eq 0 ]]; then
                    log_success "Node.js 依存関係に脆弱性は見つかりませんでした"
                else
                    log_warning "Node.js 依存関係で $vulnerabilities 件の脆弱性が検出されました"
                    log_info "詳細レポート: $npm_audit_report"
                    
                    if [[ "$VERBOSE" == "true" ]]; then
                        npm audit
                    fi
                fi
            else
                log_warning "npm audit の実行に失敗しました"
            fi
        else
            log_info "npm が見つかりません。Node.js 依存関係のチェックをスキップします"
        fi
    fi
}

# レポートの生成
generate_summary_report() {
    log_info "サマリーレポートを生成中..."
    
    local summary_report="$REPORTS_DIR/security_summary_$TIMESTAMP.md"
    
    cat > "$summary_report" << EOF
# セキュリティテストサマリーレポート

## 基本情報
- 実行日時: $(date)
- 対象URL: $BASE_URL
- 環境: $ENVIRONMENT
- テスト実行者: $(whoami)

## テスト結果

### 実行されたテスト
EOF
    
    if [[ "$SKIP_UNIT_TESTS" == "false" ]]; then
        echo "- ✅ 単体テスト（セキュリティミドルウェア）" >> "$summary_report"
    else
        echo "- ⏭️ 単体テスト（スキップ）" >> "$summary_report"
    fi
    
    echo "- ✅ 脆弱性スキャン" >> "$summary_report"
    echo "- ✅ セキュリティ設定検証" >> "$summary_report"
    echo "- ✅ 依存関係脆弱性チェック" >> "$summary_report"
    
    cat >> "$summary_report" << EOF

### 生成されたレポート
EOF
    
    # 生成されたレポートファイルをリスト
    for report_file in "$REPORTS_DIR"/*_"$TIMESTAMP".*; do
        if [[ -f "$report_file" ]]; then
            local filename=$(basename "$report_file")
            echo "- [$filename](./$filename)" >> "$summary_report"
        fi
    done
    
    cat >> "$summary_report" << EOF

### 推奨事項
1. 定期的にセキュリティテストを実行してください
2. 依存関係を最新の状態に保ってください
3. セキュリティ設定を定期的に見直してください
4. 脆弱性が検出された場合は速やかに対応してください

### 次のステップ
- 検出された問題の修正
- セキュリティポリシーの更新
- チームへの結果共有
EOF
    
    log_success "サマリーレポートを生成しました: $summary_report"
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo
        cat "$summary_report"
    fi
}

# メイン実行フロー
main() {
    local exit_code=0
    
    # Python 環境の準備
    check_python_env || exit_code=1
    
    # 単体テストの実行
    run_unit_tests || exit_code=1
    
    # 脆弱性スキャンの実行
    run_vulnerability_scan || exit_code=1
    
    # セキュリティ設定の検証
    verify_security_config || exit_code=1
    
    # 依存関係の脆弱性チェック
    check_dependency_vulnerabilities || exit_code=1
    
    # サマリーレポートの生成
    generate_summary_report
    
    # 結果の表示
    echo
    if [[ $exit_code -eq 0 ]]; then
        log_success "すべてのセキュリティテストが正常に完了しました"
        log_info "レポートディレクトリ: $REPORTS_DIR"
    else
        log_error "セキュリティテストで問題が検出されました"
        log_info "詳細はレポートを確認してください: $REPORTS_DIR"
    fi
    
    exit $exit_code
}

# スクリプトの実行
main "$@"