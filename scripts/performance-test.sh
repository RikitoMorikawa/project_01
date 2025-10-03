#!/bin/bash

# パフォーマンステストスクリプト
# Lambda 関数、API Gateway、フロントエンドのパフォーマンスをテスト

set -e

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/performance-reports"
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
    -c, --concurrent N      同時接続数（デフォルト: 10）
    -d, --duration SEC      テスト実行時間（秒、デフォルト: 60）
    -r, --requests N        総リクエスト数（デフォルト: 1000）
    --skip-load            ロードテストをスキップ
    --skip-lighthouse      Lighthouse テストをスキップ
    -v, --verbose          詳細ログを出力
    -h, --help             このヘルプを表示

例:
    $0 --url https://api.example.com --environment prod --concurrent 50
    $0 --skip-lighthouse --verbose
EOF
}

# デフォルト設定
BASE_URL="http://localhost:8000"
ENVIRONMENT="dev"
CONCURRENT_USERS=10
TEST_DURATION=60
TOTAL_REQUESTS=1000
SKIP_LOAD_TEST=false
SKIP_LIGHTHOUSE=false
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
        -c|--concurrent)
            CONCURRENT_USERS="$2"
            shift 2
            ;;
        -d|--duration)
            TEST_DURATION="$2"
            shift 2
            ;;
        -r|--requests)
            TOTAL_REQUESTS="$2"
            shift 2
            ;;
        --skip-load)
            SKIP_LOAD_TEST=true
            shift
            ;;
        --skip-lighthouse)
            SKIP_LIGHTHOUSE=true
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

log_info "パフォーマンステストを開始します"
log_info "対象URL: $BASE_URL"
log_info "環境: $ENVIRONMENT"
log_info "同時接続数: $CONCURRENT_USERS"
log_info "テスト時間: ${TEST_DURATION}秒"
log_info "レポート出力先: $REPORTS_DIR"

# 必要なツールの確認
check_dependencies() {
    log_info "依存関係を確認中..."
    
    local missing_tools=()
    
    # curl の確認
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    # Apache Bench (ab) の確認
    if ! command -v ab &> /dev/null && [[ "$SKIP_LOAD_TEST" == "false" ]]; then
        log_warning "Apache Bench (ab) が見つかりません。代替ツールを使用します"
    fi
    
    # wrk の確認（より高性能なロードテストツール）
    if ! command -v wrk &> /dev/null && [[ "$SKIP_LOAD_TEST" == "false" ]]; then
        log_info "wrk が見つかりません。Apache Bench を使用します"
    fi
    
    # Lighthouse の確認
    if ! command -v lighthouse &> /dev/null && [[ "$SKIP_LIGHTHOUSE" == "false" ]]; then
        log_warning "Lighthouse が見つかりません。npm install -g lighthouse でインストールしてください"
        SKIP_LIGHTHOUSE=true
    fi
    
    # Node.js の確認（フロントエンドテスト用）
    if ! command -v node &> /dev/null; then
        log_warning "Node.js が見つかりません。フロントエンドテストをスキップします"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "必要なツールが見つかりません: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "依存関係の確認が完了しました"
}

# 基本的な接続テスト
test_basic_connectivity() {
    log_info "基本的な接続テストを実行中..."
    
    local test_endpoints=(
        "/api/v1/health"
        "/api/v1/users"
    )
    
    local connectivity_report="$REPORTS_DIR/connectivity_test_$TIMESTAMP.txt"
    echo "基本接続テスト結果" > "$connectivity_report"
    echo "実行日時: $(date)" >> "$connectivity_report"
    echo "対象URL: $BASE_URL" >> "$connectivity_report"
    echo "" >> "$connectivity_report"
    
    local failed_tests=0
    
    for endpoint in "${test_endpoints[@]}"; do
        local url="$BASE_URL$endpoint"
        
        log_info "テスト中: $endpoint"
        
        # レスポンス時間とステータスコードを測定
        local response_time
        local status_code
        local content_length
        
        if response_time=$(curl -o /dev/null -s -w "%{time_total}" -m 10 "$url" 2>/dev/null); then
            status_code=$(curl -o /dev/null -s -w "%{http_code}" -m 10 "$url" 2>/dev/null)
            content_length=$(curl -o /dev/null -s -w "%{size_download}" -m 10 "$url" 2>/dev/null)
            
            echo "$endpoint: OK (${response_time}s, ${status_code}, ${content_length} bytes)" >> "$connectivity_report"
            
            if [[ "$VERBOSE" == "true" ]]; then
                log_info "$endpoint: ${response_time}s, HTTP $status_code, ${content_length} bytes"
            fi
            
            # 遅いレスポンスを警告
            if (( $(echo "$response_time > 2.0" | bc -l) )); then
                log_warning "$endpoint: 遅いレスポンス (${response_time}s)"
            fi
            
        else
            echo "$endpoint: FAILED" >> "$connectivity_report"
            log_error "$endpoint: 接続失敗"
            ((failed_tests++))
        fi
    done
    
    echo "" >> "$connectivity_report"
    echo "失敗したテスト: $failed_tests" >> "$connectivity_report"
    
    if [[ $failed_tests -eq 0 ]]; then
        log_success "基本接続テストが完了しました"
    else
        log_warning "基本接続テストで $failed_tests 件の失敗がありました"
    fi
    
    log_info "詳細レポート: $connectivity_report"
}

# ロードテスト（Apache Bench 使用）
run_load_test_ab() {
    log_info "Apache Bench を使用してロードテストを実行中..."
    
    local test_url="$BASE_URL/api/v1/health"
    local ab_report="$REPORTS_DIR/load_test_ab_$TIMESTAMP.txt"
    
    log_info "URL: $test_url"
    log_info "リクエスト数: $TOTAL_REQUESTS, 同時接続数: $CONCURRENT_USERS"
    
    if ab -n "$TOTAL_REQUESTS" -c "$CONCURRENT_USERS" -g "$REPORTS_DIR/ab_gnuplot_$TIMESTAMP.dat" "$test_url" > "$ab_report" 2>&1; then
        log_success "Apache Bench ロードテストが完了しました"
        
        # 結果の要約を表示
        if [[ "$VERBOSE" == "true" ]]; then
            grep -E "(Requests per second|Time per request|Transfer rate)" "$ab_report"
        fi
        
        # 重要な指標を抽出
        local rps=$(grep "Requests per second" "$ab_report" | awk '{print $4}')
        local mean_time=$(grep "Time per request" "$ab_report" | head -1 | awk '{print $4}')
        local failed_requests=$(grep "Failed requests" "$ab_report" | awk '{print $3}')
        
        log_info "RPS: $rps, 平均レスポンス時間: ${mean_time}ms, 失敗リクエスト: $failed_requests"
        
    else
        log_error "Apache Bench ロードテストが失敗しました"
        return 1
    fi
    
    log_info "詳細レポート: $ab_report"
}

# ロードテスト（wrk 使用）
run_load_test_wrk() {
    log_info "wrk を使用してロードテストを実行中..."
    
    local test_url="$BASE_URL/api/v1/health"
    local wrk_report="$REPORTS_DIR/load_test_wrk_$TIMESTAMP.txt"
    
    log_info "URL: $test_url"
    log_info "テスト時間: ${TEST_DURATION}秒, 同時接続数: $CONCURRENT_USERS"
    
    if wrk -t"$CONCURRENT_USERS" -c"$CONCURRENT_USERS" -d"${TEST_DURATION}s" --latency "$test_url" > "$wrk_report" 2>&1; then
        log_success "wrk ロードテストが完了しました"
        
        # 結果の要約を表示
        if [[ "$VERBOSE" == "true" ]]; then
            cat "$wrk_report"
        fi
        
        # 重要な指標を抽出
        local rps=$(grep "Requests/sec" "$wrk_report" | awk '{print $2}')
        local latency_avg=$(grep "Latency" "$wrk_report" | awk '{print $2}')
        
        log_info "RPS: $rps, 平均レイテンシ: $latency_avg"
        
    else
        log_error "wrk ロードテストが失敗しました"
        return 1
    fi
    
    log_info "詳細レポート: $wrk_report"
}

# ロードテストの実行
run_load_tests() {
    if [[ "$SKIP_LOAD_TEST" == "true" ]]; then
        log_info "ロードテストをスキップします"
        return 0
    fi
    
    log_info "ロードテストを実行中..."
    
    # wrk が利用可能な場合は wrk を使用、そうでなければ ab を使用
    if command -v wrk &> /dev/null; then
        run_load_test_wrk
    elif command -v ab &> /dev/null; then
        run_load_test_ab
    else
        log_warning "ロードテストツールが見つかりません（wrk または ab が必要）"
        return 1
    fi
}

# API エンドポイントのパフォーマンステスト
test_api_performance() {
    log_info "API エンドポイントのパフォーマンステストを実行中..."
    
    local api_endpoints=(
        "/api/v1/health"
        "/api/v1/users"
    )
    
    local api_report="$REPORTS_DIR/api_performance_$TIMESTAMP.csv"
    echo "endpoint,response_time,status_code,content_length,ttfb" > "$api_report"
    
    for endpoint in "${api_endpoints[@]}"; do
        local url="$BASE_URL$endpoint"
        
        log_info "API テスト中: $endpoint"
        
        # 複数回実行して平均を取る
        local total_time=0
        local successful_requests=0
        local iterations=5
        
        for ((i=1; i<=iterations; i++)); do
            local response_time
            local status_code
            local content_length
            local ttfb
            
            # 詳細なタイミング情報を取得
            local curl_output
            curl_output=$(curl -o /dev/null -s -w "%{time_total},%{http_code},%{size_download},%{time_starttransfer}" -m 10 "$url" 2>/dev/null)
            
            if [[ $? -eq 0 ]]; then
                IFS=',' read -r response_time status_code content_length ttfb <<< "$curl_output"
                
                echo "$endpoint,$response_time,$status_code,$content_length,$ttfb" >> "$api_report"
                
                total_time=$(echo "$total_time + $response_time" | bc -l)
                ((successful_requests++))
                
                if [[ "$VERBOSE" == "true" ]]; then
                    log_info "  試行 $i: ${response_time}s (HTTP $status_code)"
                fi
            else
                log_warning "  試行 $i: 失敗"
            fi
        done
        
        if [[ $successful_requests -gt 0 ]]; then
            local avg_time=$(echo "scale=3; $total_time / $successful_requests" | bc -l)
            log_info "$endpoint: 平均レスポンス時間 ${avg_time}s ($successful_requests/$iterations 成功)"
        else
            log_error "$endpoint: 全ての試行が失敗しました"
        fi
    done
    
    log_success "API パフォーマンステストが完了しました"
    log_info "詳細レポート: $api_report"
}

# Lighthouse パフォーマンステスト（フロントエンド）
run_lighthouse_test() {
    if [[ "$SKIP_LIGHTHOUSE" == "true" ]]; then
        log_info "Lighthouse テストをスキップします"
        return 0
    fi
    
    log_info "Lighthouse パフォーマンステストを実行中..."
    
    # フロントエンド URL を推定
    local frontend_url
    if [[ "$BASE_URL" == *"localhost"* ]]; then
        frontend_url="http://localhost:3000"
    else
        # API URL からフロントエンド URL を推定
        frontend_url=$(echo "$BASE_URL" | sed 's/api\.//' | sed 's/:8000/:3000/')
    fi
    
    log_info "フロントエンド URL: $frontend_url"
    
    local lighthouse_report="$REPORTS_DIR/lighthouse_$TIMESTAMP"
    
    # Lighthouse を実行
    if lighthouse "$frontend_url" \
        --output=html \
        --output=json \
        --output-path="$lighthouse_report" \
        --chrome-flags="--headless --no-sandbox --disable-gpu" \
        --quiet > /dev/null 2>&1; then
        
        log_success "Lighthouse テストが完了しました"
        
        # スコアを抽出して表示
        if [[ -f "${lighthouse_report}.report.json" ]]; then
            local performance_score
            local accessibility_score
            local best_practices_score
            local seo_score
            
            if command -v jq &> /dev/null; then
                performance_score=$(jq -r '.categories.performance.score * 100' "${lighthouse_report}.report.json" 2>/dev/null)
                accessibility_score=$(jq -r '.categories.accessibility.score * 100' "${lighthouse_report}.report.json" 2>/dev/null)
                best_practices_score=$(jq -r '.categories["best-practices"].score * 100' "${lighthouse_report}.report.json" 2>/dev/null)
                seo_score=$(jq -r '.categories.seo.score * 100' "${lighthouse_report}.report.json" 2>/dev/null)
                
                log_info "Lighthouse スコア:"
                log_info "  パフォーマンス: ${performance_score}%"
                log_info "  アクセシビリティ: ${accessibility_score}%"
                log_info "  ベストプラクティス: ${best_practices_score}%"
                log_info "  SEO: ${seo_score}%"
            fi
        fi
        
        log_info "詳細レポート: ${lighthouse_report}.report.html"
        
    else
        log_error "Lighthouse テストが失敗しました"
        return 1
    fi
}

# フロントエンドバンドルサイズの分析
analyze_bundle_size() {
    log_info "フロントエンドバンドルサイズを分析中..."
    
    local frontend_dir="$PROJECT_ROOT/frontend"
    if [[ ! -d "$frontend_dir" ]]; then
        log_warning "フロントエンドディレクトリが見つかりません"
        return 0
    fi
    
    cd "$frontend_dir"
    
    # ビルド出力ディレクトリを確認
    local build_dir="out"
    if [[ ! -d "$build_dir" ]]; then
        log_warning "ビルド出力ディレクトリが見つかりません。npm run build を実行してください"
        return 0
    fi
    
    local bundle_report="$REPORTS_DIR/bundle_analysis_$TIMESTAMP.txt"
    
    echo "フロントエンドバンドル分析" > "$bundle_report"
    echo "実行日時: $(date)" >> "$bundle_report"
    echo "" >> "$bundle_report"
    
    # ファイルサイズの分析
    echo "=== ファイルサイズ分析 ===" >> "$bundle_report"
    find "$build_dir" -type f -name "*.js" -o -name "*.css" -o -name "*.html" | while read -r file; do
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        local size_kb=$((size / 1024))
        echo "$(basename "$file"): ${size_kb}KB" >> "$bundle_report"
    done
    
    # 総サイズの計算
    local total_size=0
    while IFS= read -r -d '' file; do
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        total_size=$((total_size + size))
    done < <(find "$build_dir" -type f -print0)
    
    local total_size_mb=$((total_size / 1024 / 1024))
    
    echo "" >> "$bundle_report"
    echo "総サイズ: ${total_size_mb}MB" >> "$bundle_report"
    
    log_success "バンドルサイズ分析が完了しました"
    log_info "総サイズ: ${total_size_mb}MB"
    log_info "詳細レポート: $bundle_report"
    
    cd - > /dev/null
}

# パフォーマンスサマリーレポートの生成
generate_performance_summary() {
    log_info "パフォーマンスサマリーレポートを生成中..."
    
    local summary_report="$REPORTS_DIR/performance_summary_$TIMESTAMP.md"
    
    cat > "$summary_report" << EOF
# パフォーマンステストサマリーレポート

## 基本情報
- 実行日時: $(date)
- 対象URL: $BASE_URL
- 環境: $ENVIRONMENT
- 同時接続数: $CONCURRENT_USERS
- テスト時間: ${TEST_DURATION}秒

## テスト結果概要

### 実行されたテスト
EOF
    
    echo "- ✅ 基本接続テスト" >> "$summary_report"
    
    if [[ "$SKIP_LOAD_TEST" == "false" ]]; then
        echo "- ✅ ロードテスト" >> "$summary_report"
    else
        echo "- ⏭️ ロードテスト（スキップ）" >> "$summary_report"
    fi
    
    echo "- ✅ API パフォーマンステスト" >> "$summary_report"
    
    if [[ "$SKIP_LIGHTHOUSE" == "false" ]]; then
        echo "- ✅ Lighthouse テスト" >> "$summary_report"
    else
        echo "- ⏭️ Lighthouse テスト（スキップ）" >> "$summary_report"
    fi
    
    echo "- ✅ バンドルサイズ分析" >> "$summary_report"
    
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

### パフォーマンス改善の推奨事項
1. レスポンス時間が2秒を超えるエンドポイントを最適化する
2. バンドルサイズを削減するためにコード分割を実装する
3. 静的アセットに適切なキャッシュヘッダーを設定する
4. 画像を最適化し、WebP/AVIF 形式を使用する
5. CDN を使用してグローバル配信を最適化する
6. データベースクエリを最適化する
7. Lambda のプロビジョニング済み同時実行数を調整する

### 次のステップ
- パフォーマンスボトルネックの特定と修正
- 継続的なパフォーマンス監視の実装
- ユーザー体験の改善
EOF
    
    log_success "パフォーマンスサマリーレポートを生成しました: $summary_report"
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo
        cat "$summary_report"
    fi
}

# メイン実行フロー
main() {
    local exit_code=0
    
    # 依存関係の確認
    check_dependencies || exit_code=1
    
    # 基本接続テスト
    test_basic_connectivity || exit_code=1
    
    # ロードテスト
    run_load_tests || exit_code=1
    
    # API パフォーマンステスト
    test_api_performance || exit_code=1
    
    # Lighthouse テスト
    run_lighthouse_test || exit_code=1
    
    # バンドルサイズ分析
    analyze_bundle_size || exit_code=1
    
    # サマリーレポートの生成
    generate_performance_summary
    
    # 結果の表示
    echo
    if [[ $exit_code -eq 0 ]]; then
        log_success "すべてのパフォーマンステストが正常に完了しました"
        log_info "レポートディレクトリ: $REPORTS_DIR"
    else
        log_warning "パフォーマンステストで問題が検出されました"
        log_info "詳細はレポートを確認してください: $REPORTS_DIR"
    fi
    
    exit $exit_code
}

# スクリプトの実行
main "$@"