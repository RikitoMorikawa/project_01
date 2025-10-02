"""
ヘルスチェックエンドポイントの単体テスト
Unit tests for health check endpoints
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """ヘルスチェックエンドポイントのテストクラス / Health check endpoints test class"""
    
    def test_basic_health_check(self, client: TestClient, mock_request_id):
        """基本ヘルスチェックのテスト / Test basic health check"""
        response = client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "CSR Lambda API is running"
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
    
    def test_detailed_health_check_all_healthy(self, client: TestClient, mock_request_id):
        """全サービス正常時の詳細ヘルスチェックテスト / Test detailed health check with all services healthy"""
        with patch('app.database.check_database_health') as mock_db_health, \
             patch('app.api.routes.health.check_database_connection_with_metrics') as mock_db_metrics, \
             patch('app.auth.cognito.cognito_verifier.check_cognito_health') as mock_cognito_health, \
             patch('app.api.routes.health.collect_system_metrics') as mock_system_metrics, \
             patch('app.api.routes.health.put_custom_metric') as mock_put_metric:
            
            # モック設定 / Mock setup
            mock_db_metrics.return_value = {
                "status": "healthy",
                "message": "Database connection successful",
                "metrics": {"connection_time_ms": 50.0}
            }
            
            mock_cognito_health.return_value = {
                "status": "healthy",
                "message": "Cognito service is accessible"
            }
            
            mock_system_metrics.return_value = {
                "process": {"memory_rss": 1024000, "cpu_percent": 5.0},
                "system": {"memory_percent": 60.0, "cpu_percent": 10.0}
            }
            
            mock_put_metric.return_value = True
            
            response = client.get("/api/v1/health/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "checks" in data
            assert data["checks"]["database"]["status"] == "healthy"
            assert data["checks"]["cognito"]["status"] == "healthy"
            assert data["checks"]["cloudwatch"]["status"] == "healthy"
    
    def test_detailed_health_check_database_unhealthy(self, client: TestClient, mock_request_id):
        """データベース異常時の詳細ヘルスチェックテスト / Test detailed health check with unhealthy database"""
        with patch('app.api.routes.health.check_database_connection_with_metrics') as mock_db_metrics, \
             patch('app.auth.cognito.cognito_verifier.check_cognito_health') as mock_cognito_health, \
             patch('app.api.routes.health.collect_system_metrics') as mock_system_metrics, \
             patch('app.api.routes.health.put_custom_metric') as mock_put_metric:
            
            # データベース異常を設定 / Setup database unhealthy
            mock_db_metrics.return_value = {
                "status": "unhealthy",
                "message": "Database connection failed",
                "metrics": {"error": "Connection timeout"}
            }
            
            mock_cognito_health.return_value = {
                "status": "healthy",
                "message": "Cognito service is accessible"
            }
            
            mock_system_metrics.return_value = {
                "process": {"memory_rss": 1024000},
                "system": {"memory_percent": 60.0}
            }
            
            mock_put_metric.return_value = True
            
            response = client.get("/api/v1/health/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["message"] == "API is running but some services are degraded"
            assert data["checks"]["database"]["status"] == "unhealthy"
    
    def test_detailed_health_check_cognito_unhealthy(self, client: TestClient, mock_request_id):
        """Cognito異常時の詳細ヘルスチェックテスト / Test detailed health check with unhealthy Cognito"""
        with patch('app.api.routes.health.check_database_connection_with_metrics') as mock_db_metrics, \
             patch('app.auth.cognito.cognito_verifier.check_cognito_health') as mock_cognito_health, \
             patch('app.api.routes.health.collect_system_metrics') as mock_system_metrics:
            
            mock_db_metrics.return_value = {
                "status": "healthy",
                "message": "Database connection successful"
            }
            
            # Cognito異常を設定 / Setup Cognito unhealthy
            mock_cognito_health.return_value = {
                "status": "unhealthy",
                "message": "Cognito service error: AccessDenied"
            }
            
            mock_system_metrics.return_value = {
                "process": {"memory_rss": 1024000},
                "system": {"memory_percent": 60.0}
            }
            
            response = client.get("/api/v1/health/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["checks"]["cognito"]["status"] == "unhealthy"
    
    def test_system_metrics_endpoint(self, client: TestClient, mock_request_id):
        """システムメトリクスエンドポイントのテスト / Test system metrics endpoint"""
        with patch('app.api.routes.health.collect_system_metrics') as mock_collect_metrics:
            mock_collect_metrics.return_value = {
                "process": {
                    "pid": 12345,
                    "memory_rss": 1024000,
                    "memory_percent": 5.0,
                    "cpu_percent": 10.0,
                    "num_threads": 4
                },
                "system": {
                    "cpu_percent": 15.0,
                    "memory_total": 8589934592,
                    "memory_available": 4294967296,
                    "memory_percent": 50.0
                },
                "environment": {
                    "python_version": "3.11.0",
                    "aws_lambda_function_name": "test-function"
                }
            }
            
            response = client.get("/api/v1/health/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "metrics" in data
            assert "process" in data["metrics"]
            assert "system" in data["metrics"]
            assert data["metrics"]["process"]["pid"] == 12345
    
    def test_system_metrics_collection_error(self, client: TestClient, mock_request_id):
        """システムメトリクス収集エラーのテスト / Test system metrics collection error"""
        with patch('app.api.routes.health.collect_system_metrics') as mock_collect_metrics:
            mock_collect_metrics.side_effect = Exception("Failed to collect metrics")
            
            response = client.get("/api/v1/health/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to collect metrics" in data["message"]
    
    def test_database_health_check_endpoint(self, client: TestClient, mock_request_id):
        """データベースヘルスチェックエンドポイントのテスト / Test database health check endpoint"""
        with patch('app.api.routes.health.check_database_connection_with_metrics') as mock_db_check:
            mock_db_check.return_value = {
                "status": "healthy",
                "message": "Database connection successful",
                "metrics": {
                    "connection_time_ms": 45.2,
                    "user_count": 10,
                    "database_version": "8.0.35",
                    "connection_id": 12345
                }
            }
            
            response = client.get("/api/v1/health/database")
            
            assert response.status_code == 200
            data = response.json()
            assert "database" in data
            assert data["database"]["status"] == "healthy"
            assert data["database"]["metrics"]["user_count"] == 10
    
    def test_cognito_health_check_endpoint(self, client: TestClient, mock_request_id):
        """Cognitoヘルスチェックエンドポイントのテスト / Test Cognito health check endpoint"""
        with patch('app.auth.cognito.cognito_verifier.check_cognito_health') as mock_cognito_check:
            mock_cognito_check.return_value = {
                "status": "healthy",
                "message": "Cognito service is accessible"
            }
            
            response = client.get("/api/v1/health/cognito")
            
            assert response.status_code == 200
            data = response.json()
            assert "cognito" in data
            assert data["cognito"]["status"] == "healthy"
            assert "response_time_ms" in data["cognito"]
    
    def test_readiness_probe_ready(self, client: TestClient, mock_request_id):
        """準備完了プローブのテスト / Test readiness probe when ready"""
        with patch('app.database.check_database_health') as mock_db_health:
            mock_db_health.return_value = {"status": "healthy"}
            
            response = client.get("/api/v1/health/readiness")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["message"] == "Application is ready to serve traffic"
    
    def test_readiness_probe_not_ready(self, client: TestClient, mock_request_id):
        """準備未完了プローブのテスト / Test readiness probe when not ready"""
        with patch('app.database.check_database_health') as mock_db_health:
            mock_db_health.return_value = {"status": "unhealthy"}
            
            response = client.get("/api/v1/health/readiness")
            
            # FastAPIのテストクライアントは503ステータスでも例外を投げない
            # FastAPI test client doesn't throw exception for 503 status
            data = response.json()
            assert data["status"] == "not_ready"
            assert "not ready" in data["message"]
    
    def test_liveness_probe(self, client: TestClient, mock_request_id):
        """生存プローブのテスト / Test liveness probe"""
        response = client.get("/api/v1/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["message"] == "Application is alive"
        assert "uptime_seconds" in data
    
    def test_cloudwatch_status_healthy(self, client: TestClient, mock_request_id):
        """CloudWatchステータス正常のテスト / Test CloudWatch status healthy"""
        with patch('app.api.routes.health.get_cloudwatch_client') as mock_get_client, \
             patch('app.api.routes.health.put_custom_metric') as mock_put_metric:
            
            mock_get_client.return_value = Mock()  # CloudWatchクライアントが利用可能
            mock_put_metric.return_value = True
            
            response = client.get("/api/v1/health/cloudwatch")
            
            assert response.status_code == 200
            data = response.json()
            assert data["cloudwatch"]["status"] == "healthy"
            assert data["cloudwatch"]["test_metric_sent"] is True
    
    def test_cloudwatch_status_unavailable(self, client: TestClient, mock_request_id):
        """CloudWatchステータス利用不可のテスト / Test CloudWatch status unavailable"""
        with patch('app.api.routes.health.get_cloudwatch_client') as mock_get_client:
            mock_get_client.return_value = None  # CloudWatchクライアントが利用不可
            
            response = client.get("/api/v1/health/cloudwatch")
            
            assert response.status_code == 200
            data = response.json()
            assert data["cloudwatch"]["status"] == "unavailable"
    
    def test_send_custom_metrics_success(self, client: TestClient, mock_request_id):
        """カスタムメトリクス送信成功のテスト / Test successful custom metrics sending"""
        with patch('app.api.routes.health.collect_system_metrics') as mock_collect_metrics, \
             patch('app.api.routes.health.put_custom_metric') as mock_put_metric:
            
            mock_collect_metrics.return_value = {
                "system": {
                    "memory_percent": 60.0,
                    "cpu_percent": 15.0
                },
                "process": {
                    "memory_rss": 1024000
                }
            }
            
            mock_put_metric.return_value = True
            
            response = client.post("/api/v1/health/metrics/send")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["sent_metrics"]) > 0
            assert len(data["failed_metrics"]) == 0
    
    def test_send_custom_metrics_partial_failure(self, client: TestClient, mock_request_id):
        """カスタムメトリクス送信部分失敗のテスト / Test partial failure in custom metrics sending"""
        with patch('app.api.routes.health.collect_system_metrics') as mock_collect_metrics, \
             patch('app.api.routes.health.put_custom_metric') as mock_put_metric:
            
            mock_collect_metrics.return_value = {
                "system": {
                    "memory_percent": 60.0,
                    "cpu_percent": 15.0
                },
                "process": {
                    "memory_rss": 1024000
                }
            }
            
            # 一部のメトリクス送信が失敗 / Some metrics fail to send
            mock_put_metric.side_effect = [True, False, True]
            
            response = client.post("/api/v1/health/metrics/send")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "partial"
            assert len(data["sent_metrics"]) > 0
            assert len(data["failed_metrics"]) > 0
    
    def test_send_custom_metrics_collection_error(self, client: TestClient, mock_request_id):
        """カスタムメトリクス収集エラーのテスト / Test custom metrics collection error"""
        with patch('app.api.routes.health.collect_system_metrics') as mock_collect_metrics:
            mock_collect_metrics.return_value = {"error": "Failed to collect metrics"}
            
            response = client.post("/api/v1/health/metrics/send")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to collect metrics" in data["message"]
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_function(self):
        """システムメトリクス収集関数のテスト / Test system metrics collection function"""
        from app.api.routes.health import collect_system_metrics
        
        with patch('psutil.Process') as mock_process, \
             patch('psutil.virtual_memory') as mock_virtual_memory, \
             patch('psutil.cpu_percent') as mock_cpu_percent:
            
            # モックプロセス情報 / Mock process info
            mock_process_instance = Mock()
            mock_process_instance.pid = 12345
            mock_process_instance.memory_info.return_value = Mock(rss=1024000, vms=2048000)
            mock_process_instance.memory_percent.return_value = 5.0
            mock_process_instance.cpu_percent.return_value = 10.0
            mock_process_instance.num_threads.return_value = 4
            mock_process_instance.create_time.return_value = 1704063600
            mock_process.return_value = mock_process_instance
            
            # モックシステム情報 / Mock system info
            mock_virtual_memory.return_value = Mock(
                total=8589934592,
                available=4294967296,
                percent=50.0,
                used=4294967296,
                free=4294967296
            )
            mock_cpu_percent.return_value = 15.0
            
            metrics = await collect_system_metrics()
            
            assert "process" in metrics
            assert "system" in metrics
            assert "environment" in metrics
            assert metrics["process"]["pid"] == 12345
            assert metrics["system"]["memory_percent"] == 50.0
    
    @pytest.mark.asyncio
    async def test_put_custom_metric_function(self):
        """カスタムメトリクス送信関数のテスト / Test put custom metric function"""
        from app.api.routes.health import put_custom_metric
        
        with patch('app.api.routes.health.get_cloudwatch_client') as mock_get_client:
            mock_cloudwatch = Mock()
            mock_get_client.return_value = mock_cloudwatch
            
            result = await put_custom_metric("TestMetric", 100.0, "Count", {"Environment": "test"})
            
            assert result is True
            mock_cloudwatch.put_metric_data.assert_called_once()
            
            # 呼び出し引数の検証 / Verify call arguments
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "CSR-Lambda-API"
            assert call_args[1]["MetricData"][0]["MetricName"] == "TestMetric"
            assert call_args[1]["MetricData"][0]["Value"] == 100.0