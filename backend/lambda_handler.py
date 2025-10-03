import logging
import os
import time
from mangum import Mangum
from app.main import app
from app.utils.performance import optimize_lambda_startup, warm_up_connections

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Lambda コールドスタート最適化
startup_start = time.time()
optimize_lambda_startup()
startup_time = time.time() - startup_start

logger.info(f"Lambda 初期化完了: {startup_time:.3f}秒")

# Configure Mangum for Lambda with performance optimizations
handler = Mangum(
    app,
    lifespan="off",  # Disable lifespan for Lambda
    api_gateway_base_path="/v1" if os.getenv("ENVIRONMENT") != "dev" else None,
    # パフォーマンス最適化設定
    text_mime_types=[
        "application/json",
        "application/javascript",
        "application/xml",
        "application/vnd.api+json",
        "text/plain",
        "text/html",
        "text/css",
        "text/javascript",
        "text/xml",
    ]
)

# 接続のウォームアップ（初回実行時のみ）
_connections_warmed = False

async def warm_connections_once():
    """接続を一度だけウォームアップ"""
    global _connections_warmed
    if not _connections_warmed:
        await warm_up_connections()
        _connections_warmed = True

# Lambda handler wrapper for additional logging and performance monitoring
def lambda_handler(event, context):
    """
    AWS Lambda handler with enhanced logging, error handling, and performance monitoring
    """
    request_start = time.time()
    
    try:
        # リクエスト情報をログ出力
        http_method = event.get('httpMethod', 'UNKNOWN')
        path = event.get('path', 'UNKNOWN')
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'UNKNOWN')
        
        logger.info(f"Lambda 呼び出し: {http_method} {path} from {source_ip}")
        
        # 接続のウォームアップ（非同期で実行）
        import asyncio
        try:
            asyncio.create_task(warm_connections_once())
        except Exception as e:
            logger.warning(f"接続ウォームアップエラー: {str(e)}")
        
        # Mangum ハンドラーを呼び出し
        response = handler(event, context)
        
        # レスポンス時間を計算
        request_time = time.time() - request_start
        status_code = response.get('statusCode', 'UNKNOWN')
        
        logger.info(f"Lambda レスポンス: {status_code} ({request_time:.3f}秒)")
        
        # パフォーマンスメトリクスを CloudWatch に送信
        try:
            from app.utils.metrics import metrics
            metrics.put_metric("lambda.request_duration", request_time, "Seconds")
            metrics.put_metric("lambda.requests", 1, "Count")
            
            if status_code >= 400:
                metrics.put_metric("lambda.errors", 1, "Count")
            
        except Exception as e:
            logger.warning(f"メトリクス送信エラー: {str(e)}")
        
        # レスポンスヘッダーにパフォーマンス情報を追加
        if isinstance(response, dict) and 'headers' in response:
            response['headers']['X-Response-Time'] = f"{request_time:.3f}s"
            response['headers']['X-Lambda-Request-Id'] = context.aws_request_id
        
        # 遅いリクエストを警告
        if request_time > 5.0:  # 5秒以上
            logger.warning(f"遅いリクエスト検出: {http_method} {path} - {request_time:.3f}秒")
        
        return response
        
    except Exception as e:
        request_time = time.time() - request_start
        logger.error(f"Lambda ハンドラーエラー: {str(e)} ({request_time:.3f}秒)", exc_info=True)
        
        # エラーメトリクスを送信
        try:
            from app.utils.metrics import metrics
            metrics.put_metric("lambda.handler_errors", 1, "Count")
            metrics.put_metric("lambda.request_duration", request_time, "Seconds")
        except Exception:
            pass
        
        # 適切なエラーレスポンスを返す
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "X-Response-Time": f"{request_time:.3f}s",
                "X-Lambda-Request-Id": context.aws_request_id,
                "X-Error": "LAMBDA_HANDLER_ERROR"
            },
            "body": '{"error_code": "LAMBDA_ERROR", "message": "Internal server error", "request_id": "' + context.aws_request_id + '"}'
        }