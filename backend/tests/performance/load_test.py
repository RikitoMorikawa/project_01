"""
パフォーマンステストとロードテスト

本番環境のパフォーマンスとスケーラビリティを検証する
"""
import asyncio
import aiohttp
import time
import statistics
import json
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading


@dataclass
class LoadTestConfig:
    """ロードテスト設定"""
    base_url: str
    concurrent_users: int = 10
    requests_per_user: int = 100
    ramp_up_time: int = 30  # 秒
    test_duration: int = 300  # 秒
    api_key: str = None


@dataclass
class RequestResult:
    """リクエスト結果"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error: str = None
    timestamp: float = None


class LoadTester:
    """ロードテスタークラス"""
    
    def __init__(self, config: LoadTestConfig):
        """
        初期化
        
        Args:
            config: ロードテスト設定
        """
        self.config = config
        self.results: List[RequestResult] = []
        self.results_lock = threading.Lock()
        self.start_time = None
        self.end_time = None
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = 'GET', data: Dict = None) -> RequestResult:
        """
        HTTPリクエストを実行
        
        Args:
            session: aiohttp セッション
            endpoint: エンドポイントパス
            method: HTTPメソッド
            data: リクエストデータ
            
        Returns:
            RequestResult: リクエスト結果
        """
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            headers = {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            async with session.request(method, url, json=data, headers=headers) as response:
                await response.text()  # レスポンスボディを読み込み
                
                end_time = time.time()
                response_time = end_time - start_time
                
                return RequestResult(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status,
                    response_time=response_time,
                    success=200 <= response.status < 400,
                    timestamp=start_time
                )
                
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e),
                timestamp=start_time
            )
    
    async def user_simulation(self, user_id: int, session: aiohttp.ClientSession):
        """
        ユーザーの行動をシミュレート
        
        Args:
            user_id: ユーザーID
            session: aiohttp セッション
        """
        # ユーザーの典型的な行動パターン
        user_actions = [
            {'endpoint': '/api/v1/health', 'method': 'GET', 'weight': 0.1},
            {'endpoint': '/api/v1/users', 'method': 'GET', 'weight': 0.3},
            {'endpoint': '/api/v1/auth/login', 'method': 'POST', 'weight': 0.1, 'data': {'email': f'user{user_id}@example.com', 'password': 'testpass'}},
            {'endpoint': '/api/v1/users/1', 'method': 'GET', 'weight': 0.2},
            {'endpoint': '/api/v1/users', 'method': 'POST', 'weight': 0.1, 'data': {'email': f'newuser{user_id}@example.com', 'username': f'user{user_id}'}},
        ]
        
        for i in range(self.config.requests_per_user):
            # ランダムにアクションを選択（重み付き）
            import random
            action = random.choices(user_actions, weights=[a['weight'] for a in user_actions])[0]
            
            result = await self.make_request(
                session,
                action['endpoint'],
                action['method'],
                action.get('data')
            )
            
            with self.results_lock:
                self.results.append(result)
            
            # リクエスト間隔（1-3秒のランダム）
            await asyncio.sleep(random.uniform(1, 3))
    
    async def run_load_test(self) -> Dict[str, Any]:
        """
        ロードテストを実行
        
        Returns:
            Dict[str, Any]: テスト結果
        """
        print(f"ロードテストを開始します...")
        print(f"同時ユーザー数: {self.config.concurrent_users}")
        print(f"ユーザーあたりリクエスト数: {self.config.requests_per_user}")
        print(f"対象URL: {self.config.base_url}")
        
        self.start_time = time.time()
        
        # HTTPセッションの設定
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # 同時ユーザーのタスクを作成
            tasks = []
            for user_id in range(self.config.concurrent_users):
                task = asyncio.create_task(self.user_simulation(user_id, session))
                tasks.append(task)
                
                # ランプアップ時間に応じて段階的にユーザーを追加
                if self.config.ramp_up_time > 0:
                    await asyncio.sleep(self.config.ramp_up_time / self.config.concurrent_users)
            
            # すべてのタスクの完了を待機
            await asyncio.gather(*tasks)
        
        self.end_time = time.time()
        
        return self.analyze_results()
    
    def analyze_results(self) -> Dict[str, Any]:
        """
        テスト結果を分析
        
        Returns:
            Dict[str, Any]: 分析結果
        """
        if not self.results:
            return {'error': 'テスト結果がありません'}
        
        # 基本統計
        response_times = [r.response_time for r in self.results]
        successful_requests = [r for r in self.results if r.success]
        failed_requests = [r for r in self.results if not r.success]
        
        # エンドポイント別統計
        endpoint_stats = {}
        for result in self.results:
            key = f"{result.method} {result.endpoint}"
            if key not in endpoint_stats:
                endpoint_stats[key] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'response_times': [],
                    'status_codes': {}
                }
            
            stats = endpoint_stats[key]
            stats['total_requests'] += 1
            stats['response_times'].append(result.response_time)
            
            if result.success:
                stats['successful_requests'] += 1
            else:
                stats['failed_requests'] += 1
            
            # ステータスコード集計
            status_code = result.status_code
            if status_code not in stats['status_codes']:
                stats['status_codes'][status_code] = 0
            stats['status_codes'][status_code] += 1
        
        # エンドポイント別統計の計算
        for endpoint, stats in endpoint_stats.items():
            times = stats['response_times']
            if times:
                stats['avg_response_time'] = statistics.mean(times)
                stats['min_response_time'] = min(times)
                stats['max_response_time'] = max(times)
                stats['p95_response_time'] = statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
                stats['p99_response_time'] = statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times)
            
            stats['success_rate'] = (stats['successful_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
        
        # 全体統計
        total_duration = self.end_time - self.start_time
        total_requests = len(self.results)
        successful_count = len(successful_requests)
        failed_count = len(failed_requests)
        
        analysis = {
            'test_config': {
                'concurrent_users': self.config.concurrent_users,
                'requests_per_user': self.config.requests_per_user,
                'base_url': self.config.base_url
            },
            'summary': {
                'total_duration': total_duration,
                'total_requests': total_requests,
                'successful_requests': successful_count,
                'failed_requests': failed_count,
                'success_rate': (successful_count / total_requests * 100) if total_requests > 0 else 0,
                'requests_per_second': total_requests / total_duration if total_duration > 0 else 0
            },
            'response_time_stats': {
                'avg': statistics.mean(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'median': statistics.median(response_times),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                'p99': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
            },
            'endpoint_stats': endpoint_stats,
            'errors': [
                {
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'error': r.error,
                    'status_code': r.status_code,
                    'timestamp': r.timestamp
                }
                for r in failed_requests
            ]
        }
        
        return analysis
    
    def generate_report(self, results: Dict[str, Any], output_file: str = 'load_test_report.json'):
        """
        テストレポートを生成
        
        Args:
            results: テスト結果
            output_file: 出力ファイル名
        """
        # JSON形式で保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # コンソール出力
        print(f"\n=== ロードテスト結果 ===")
        print(f"テスト時間: {results['summary']['total_duration']:.2f}秒")
        print(f"総リクエスト数: {results['summary']['total_requests']}")
        print(f"成功リクエスト数: {results['summary']['successful_requests']}")
        print(f"失敗リクエスト数: {results['summary']['failed_requests']}")
        print(f"成功率: {results['summary']['success_rate']:.2f}%")
        print(f"スループット: {results['summary']['requests_per_second']:.2f} req/sec")
        
        print(f"\n=== レスポンス時間統計 ===")
        rt_stats = results['response_time_stats']
        print(f"平均: {rt_stats['avg']:.3f}秒")
        print(f"最小: {rt_stats['min']:.3f}秒")
        print(f"最大: {rt_stats['max']:.3f}秒")
        print(f"中央値: {rt_stats['median']:.3f}秒")
        print(f"95パーセンタイル: {rt_stats['p95']:.3f}秒")
        print(f"99パーセンタイル: {rt_stats['p99']:.3f}秒")
        
        print(f"\n=== エンドポイント別統計 ===")
        for endpoint, stats in results['endpoint_stats'].items():
            print(f"\n{endpoint}:")
            print(f"  リクエスト数: {stats['total_requests']}")
            print(f"  成功率: {stats['success_rate']:.2f}%")
            if 'avg_response_time' in stats:
                print(f"  平均レスポンス時間: {stats['avg_response_time']:.3f}秒")
                print(f"  95パーセンタイル: {stats['p95_response_time']:.3f}秒")
        
        if results['errors']:
            print(f"\n=== エラー詳細 (最初の10件) ===")
            for error in results['errors'][:10]:
                error_msg = error['error'] or f"HTTP {error['status_code']}"
                print(f"  {error['method']} {error['endpoint']}: {error_msg}")
        
        print(f"\n詳細レポートは {output_file} に保存されました。")


async def run_performance_test():
    """パフォーマンステストの実行"""
    # 環境変数から設定を取得
    base_url = os.getenv('PRODUCTION_API_URL', 'https://api.example.com')
    api_key = os.getenv('PRODUCTION_API_KEY')
    
    # テスト設定
    config = LoadTestConfig(
        base_url=base_url,
        concurrent_users=int(os.getenv('LOAD_TEST_USERS', '10')),
        requests_per_user=int(os.getenv('LOAD_TEST_REQUESTS_PER_USER', '50')),
        ramp_up_time=int(os.getenv('LOAD_TEST_RAMP_UP', '30')),
        api_key=api_key
    )
    
    # ロードテスト実行
    tester = LoadTester(config)
    results = await tester.run_load_test()
    
    # レポート生成
    tester.generate_report(results)
    
    return results


if __name__ == "__main__":
    # スタンドアロン実行用
    asyncio.run(run_performance_test())