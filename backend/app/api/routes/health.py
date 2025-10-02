from fastapi import APIRouter, Depends
from datetime import datetime
import logging
import psutil
import os
import time
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.config import settings
from app.dependencies import get_request_id, get_common_headers

router = APIRouter()
logger = logging.getLogger(__name__)

# CloudWatch client for metrics
_cloudwatch_client = None

def get_cloudwatch_client():
    """Get or create CloudWatch client"""
    global _cloudwatch_client
    if _cloudwatch_client is None:
        try:
            _cloudwatch_client = boto3.client('cloudwatch', region_name=settings.aws_region)
        except Exception as e:
            logger.warning(f"Failed to create CloudWatch client: {str(e)}")
            _cloudwatch_client = None
    return _cloudwatch_client


async def put_custom_metric(metric_name: str, value: float, unit: str = 'Count', dimensions: Dict[str, str] = None):
    """
    Put custom metric to CloudWatch
    CloudWatchにカスタムメトリクスを送信
    """
    try:
        cloudwatch = get_cloudwatch_client()
        if not cloudwatch:
            logger.warning("CloudWatch client not available, skipping metric")
            return False
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': key, 'Value': value} for key, value in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace='CSR-Lambda-API',
            MetricData=[metric_data]
        )
        
        logger.debug(f"Custom metric sent: {metric_name} = {value}")
        return True
        
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to put CloudWatch metric {metric_name}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error putting CloudWatch metric {metric_name}: {str(e)}")
        return False


async def collect_system_metrics() -> Dict[str, Any]:
    """
    Collect system metrics for monitoring
    システム監視用のメトリクスを収集
    """
    try:
        # Get process info
        process = psutil.Process()
        
        # Memory metrics
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        # CPU metrics
        cpu_percent = process.cpu_percent()
        system_cpu = psutil.cpu_percent(interval=0.1)
        
        # Disk metrics (if available)
        disk_usage = None
        try:
            disk_usage = psutil.disk_usage('/')
        except:
            pass  # Disk metrics might not be available in Lambda
        
        # Network metrics (if available)
        network_io = None
        try:
            network_io = psutil.net_io_counters()
        except:
            pass  # Network metrics might not be available in Lambda
        
        metrics = {
            "process": {
                "pid": process.pid,
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "memory_percent": process.memory_percent(),
                "cpu_percent": cpu_percent,
                "num_threads": process.num_threads(),
                "create_time": process.create_time()
            },
            "system": {
                "cpu_percent": system_cpu,
                "memory_total": system_memory.total,
                "memory_available": system_memory.available,
                "memory_percent": system_memory.percent,
                "memory_used": system_memory.used,
                "memory_free": system_memory.free
            },
            "environment": {
                "python_version": os.sys.version,
                "platform": os.name,
                "aws_lambda_function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME"),
                "aws_lambda_function_version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION"),
                "aws_region": os.environ.get("AWS_REGION"),
                "aws_execution_env": os.environ.get("AWS_EXECUTION_ENV")
            }
        }
        
        # Add disk metrics if available
        if disk_usage:
            metrics["system"]["disk_total"] = disk_usage.total
            metrics["system"]["disk_used"] = disk_usage.used
            metrics["system"]["disk_free"] = disk_usage.free
            metrics["system"]["disk_percent"] = (disk_usage.used / disk_usage.total) * 100
        
        # Add network metrics if available
        if network_io:
            metrics["system"]["network_bytes_sent"] = network_io.bytes_sent
            metrics["system"]["network_bytes_recv"] = network_io.bytes_recv
            metrics["system"]["network_packets_sent"] = network_io.packets_sent
            metrics["system"]["network_packets_recv"] = network_io.packets_recv
        
        # Send key metrics to CloudWatch (async, don't wait for completion)
        try:
            dimensions = {
                'Environment': settings.environment,
                'FunctionName': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'local')
            }
            
            # Send memory usage
            await put_custom_metric(
                'MemoryUsagePercent', 
                system_memory.percent, 
                'Percent', 
                dimensions
            )
            
            # Send CPU usage
            await put_custom_metric(
                'CPUUsagePercent', 
                system_cpu, 
                'Percent', 
                dimensions
            )
            
            # Send process memory
            await put_custom_metric(
                'ProcessMemoryMB', 
                memory_info.rss / 1024 / 1024, 
                'Count', 
                dimensions
            )
            
        except Exception as cw_error:
            logger.warning(f"Failed to send metrics to CloudWatch: {str(cw_error)}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {str(e)}")
        return {
            "error": str(e),
            "basic_info": {
                "timestamp": datetime.utcnow().isoformat(),
                "environment": settings.environment
            }
        }


async def check_database_connection_with_metrics() -> Dict[str, Any]:
    """
    Enhanced database health check with connection metrics
    """
    start_time = time.time()
    
    try:
        from app.database import check_database_health, get_db_connection
        
        # Basic health check
        health_result = await check_database_health()
        
        # Additional connection metrics
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Test query performance
                cursor.execute("SELECT COUNT(*) as user_count FROM users")
                user_count = cursor.fetchone()
                
                # Get database version
                cursor.execute("SELECT VERSION() as version")
                db_version = cursor.fetchone()
                
                # Get connection info
                cursor.execute("SELECT CONNECTION_ID() as connection_id")
                connection_info = cursor.fetchone()
        
        connection_time = time.time() - start_time
        
        # Send database metrics to CloudWatch
        try:
            dimensions = {
                'Environment': settings.environment,
                'Database': 'Aurora-MySQL'
            }
            
            # Send connection time
            await put_custom_metric(
                'DatabaseConnectionTime', 
                connection_time * 1000, 
                'Milliseconds', 
                dimensions
            )
            
            # Send user count
            user_count_value = user_count.get("user_count", 0) if user_count else 0
            await put_custom_metric(
                'DatabaseUserCount', 
                user_count_value, 
                'Count', 
                dimensions
            )
            
            # Send health status (1 for healthy, 0 for unhealthy)
            health_status = 1 if health_result.get("status") == "healthy" else 0
            await put_custom_metric(
                'DatabaseHealthStatus', 
                health_status, 
                'Count', 
                dimensions
            )
            
        except Exception as cw_error:
            logger.warning(f"Failed to send database metrics to CloudWatch: {str(cw_error)}")
        
        return {
            **health_result,
            "metrics": {
                "connection_time_ms": round(connection_time * 1000, 2),
                "user_count": user_count.get("user_count", 0) if user_count else 0,
                "database_version": db_version.get("version", "unknown") if db_version else "unknown",
                "connection_id": connection_info.get("connection_id") if connection_info else None
            }
        }
        
    except Exception as e:
        connection_time = time.time() - start_time
        logger.error(f"Enhanced database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "metrics": {
                "connection_time_ms": round(connection_time * 1000, 2),
                "error": str(e)
            }
        }


@router.get("/")
async def health_check(
    request_id: str = Depends(get_request_id)
):
    """
    Health check endpoint
    Returns system status and basic information
    """
    logger.info(f"Health check requested - Request ID: {request_id}")
    
    health_data = {
        "status": "healthy",
        "message": "CSR Lambda API is running",
        "version": settings.api_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }
    
    return health_data


@router.get("/detailed")
async def detailed_health_check(
    request_id: str = Depends(get_request_id)
):
    """
    Detailed health check endpoint
    Returns comprehensive system status including dependencies and metrics
    """
    logger.info(f"Detailed health check requested - Request ID: {request_id}")
    
    # Import here to avoid circular imports
    from app.database import check_database_health
    
    # Basic health info
    health_data = {
        "status": "healthy",
        "message": "CSR Lambda API is running",
        "version": settings.api_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "checks": {
            "api": {"status": "healthy", "message": "API is responsive"}
        },
        "metrics": {}
    }
    
    # Collect system metrics
    try:
        health_data["metrics"] = await collect_system_metrics()
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {str(e)}")
        health_data["metrics"] = {"error": "Failed to collect metrics"}
    
    # Check database connectivity with metrics
    try:
        db_health = await check_database_connection_with_metrics()
        health_data["checks"]["database"] = db_health
        
        # Update overall status if database is unhealthy
        if db_health["status"] != "healthy":
            health_data["status"] = "degraded"
            health_data["message"] = "API is running but some services are degraded"
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database health check failed: {str(e)}"
        }
        health_data["status"] = "degraded"
        health_data["message"] = "API is running but some services are degraded"
    
    # Check Cognito service connectivity
    try:
        from app.auth.cognito import cognito_verifier
        cognito_health = await cognito_verifier.check_cognito_health()
        health_data["checks"]["cognito"] = cognito_health
        
        # Update overall status if Cognito is unhealthy
        if cognito_health["status"] != "healthy":
            health_data["status"] = "degraded"
            health_data["message"] = "API is running but some services are degraded"
            
    except Exception as e:
        logger.error(f"Cognito health check failed: {str(e)}")
        health_data["checks"]["cognito"] = {
            "status": "unhealthy",
            "message": f"Cognito health check failed: {str(e)}"
        }
        health_data["status"] = "degraded"
        health_data["message"] = "API is running but some services are degraded"
    
    # Check CloudWatch connectivity
    try:
        cloudwatch = get_cloudwatch_client()
        if cloudwatch:
            # Test CloudWatch by sending a health check metric
            test_metric_sent = await put_custom_metric(
                'HealthCheckDetailed', 
                1, 
                'Count', 
                {
                    'Environment': settings.environment,
                    'CheckType': 'detailed'
                }
            )
            
            health_data["checks"]["cloudwatch"] = {
                "status": "healthy" if test_metric_sent else "degraded",
                "message": "CloudWatch integration working" if test_metric_sent else "CloudWatch available but metric sending failed",
                "region": settings.aws_region,
                "namespace": "CSR-Lambda-API"
            }
        else:
            health_data["checks"]["cloudwatch"] = {
                "status": "unavailable",
                "message": "CloudWatch client not available"
            }
            
    except Exception as e:
        logger.error(f"CloudWatch health check failed: {str(e)}")
        health_data["checks"]["cloudwatch"] = {
            "status": "unhealthy",
            "message": f"CloudWatch health check failed: {str(e)}"
        }
    
    return health_data

@router.get("/metrics")
async def get_system_metrics(
    request_id: str = Depends(get_request_id)
):
    """
    Get system metrics for monitoring
    システム監視用のメトリクスを取得
    """
    logger.info(f"System metrics requested - Request ID: {request_id}")
    
    try:
        metrics = await collect_system_metrics()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)} - Request ID: {request_id}")
        return {
            "status": "error",
            "message": f"Failed to collect metrics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }


@router.get("/database")
async def check_database_status(
    request_id: str = Depends(get_request_id)
):
    """
    Dedicated database health check endpoint with detailed metrics
    詳細なメトリクス付きの専用データベースヘルスチェックエンドポイント
    """
    logger.info(f"Database health check requested - Request ID: {request_id}")
    
    try:
        db_status = await check_database_connection_with_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "database": db_status
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)} - Request ID: {request_id}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "database": {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            }
        }


@router.get("/cognito")
async def check_cognito_status(
    request_id: str = Depends(get_request_id)
):
    """
    Dedicated Cognito service health check endpoint
    専用のCognitoサービスヘルスチェックエンドポイント
    """
    logger.info(f"Cognito health check requested - Request ID: {request_id}")
    
    try:
        from app.auth.cognito import cognito_verifier
        
        start_time = time.time()
        cognito_health = await cognito_verifier.check_cognito_health()
        response_time = time.time() - start_time
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "cognito": {
                **cognito_health,
                "response_time_ms": round(response_time * 1000, 2),
                "region": cognito_verifier.region,
                "user_pool_id": cognito_verifier.user_pool_id
            }
        }
        
    except Exception as e:
        logger.error(f"Cognito health check failed: {str(e)} - Request ID: {request_id}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "cognito": {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            }
        }


@router.get("/readiness")
async def readiness_check(
    request_id: str = Depends(get_request_id)
):
    """
    Kubernetes-style readiness probe
    Application is ready to serve traffic
    """
    logger.info(f"Readiness check requested - Request ID: {request_id}")
    
    try:
        # Check critical dependencies
        from app.database import check_database_health
        
        db_health = await check_database_health()
        
        if db_health["status"] == "healthy":
            return {
                "status": "ready",
                "message": "Application is ready to serve traffic",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        else:
            return {
                "status": "not_ready",
                "message": "Application is not ready - database unavailable",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }, 503
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)} - Request ID: {request_id}")
        return {
            "status": "not_ready",
            "message": f"Readiness check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }, 503


@router.get("/liveness")
async def liveness_check(
    request_id: str = Depends(get_request_id)
):
    """
    Kubernetes-style liveness probe
    Application is alive and should not be restarted
    """
    logger.info(f"Liveness check requested - Request ID: {request_id}")
    
    # Simple check - if we can respond, we're alive
    return {
        "status": "alive",
        "message": "Application is alive",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "uptime_seconds": time.time() - psutil.Process().create_time()
    }


@router.get("/cloudwatch")
async def get_cloudwatch_status(
    request_id: str = Depends(get_request_id)
):
    """
    Check CloudWatch integration status and send test metrics
    CloudWatch統合ステータスをチェックしてテストメトリクスを送信
    """
    logger.info(f"CloudWatch status check requested - Request ID: {request_id}")
    
    try:
        cloudwatch = get_cloudwatch_client()
        
        if not cloudwatch:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "cloudwatch": {
                    "status": "unavailable",
                    "message": "CloudWatch client not available"
                }
            }
        
        # Test CloudWatch connectivity by sending a test metric
        test_metric_sent = await put_custom_metric(
            'HealthCheckTest', 
            1, 
            'Count', 
            {
                'Environment': settings.environment,
                'TestType': 'connectivity'
            }
        )
        
        if test_metric_sent:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "cloudwatch": {
                    "status": "healthy",
                    "message": "CloudWatch integration is working",
                    "region": settings.aws_region,
                    "namespace": "CSR-Lambda-API",
                    "test_metric_sent": True
                }
            }
        else:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "cloudwatch": {
                    "status": "degraded",
                    "message": "CloudWatch client available but metric sending failed",
                    "region": settings.aws_region,
                    "test_metric_sent": False
                }
            }
            
    except Exception as e:
        logger.error(f"CloudWatch status check failed: {str(e)} - Request ID: {request_id}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "cloudwatch": {
                "status": "unhealthy",
                "message": f"CloudWatch check failed: {str(e)}"
            }
        }


@router.post("/metrics/send")
async def send_custom_metrics(
    request_id: str = Depends(get_request_id)
):
    """
    Manually trigger sending of current system metrics to CloudWatch
    現在のシステムメトリクスをCloudWatchに手動送信
    """
    logger.info(f"Manual metrics send requested - Request ID: {request_id}")
    
    try:
        # Collect current metrics
        metrics = await collect_system_metrics()
        
        if "error" in metrics:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "status": "error",
                "message": "Failed to collect metrics",
                "details": metrics
            }
        
        # Send metrics to CloudWatch
        dimensions = {
            'Environment': settings.environment,
            'FunctionName': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'local'),
            'ManualTrigger': 'true'
        }
        
        sent_metrics = []
        failed_metrics = []
        
        # Send system metrics
        system_metrics = metrics.get('system', {})
        if 'memory_percent' in system_metrics:
            success = await put_custom_metric(
                'SystemMemoryPercent', 
                system_metrics['memory_percent'], 
                'Percent', 
                dimensions
            )
            if success:
                sent_metrics.append('SystemMemoryPercent')
            else:
                failed_metrics.append('SystemMemoryPercent')
        
        if 'cpu_percent' in system_metrics:
            success = await put_custom_metric(
                'SystemCPUPercent', 
                system_metrics['cpu_percent'], 
                'Percent', 
                dimensions
            )
            if success:
                sent_metrics.append('SystemCPUPercent')
            else:
                failed_metrics.append('SystemCPUPercent')
        
        # Send process metrics
        process_metrics = metrics.get('process', {})
        if 'memory_rss' in process_metrics:
            success = await put_custom_metric(
                'ProcessMemoryRSS', 
                process_metrics['memory_rss'] / 1024 / 1024,  # Convert to MB
                'Count', 
                dimensions
            )
            if success:
                sent_metrics.append('ProcessMemoryRSS')
            else:
                failed_metrics.append('ProcessMemoryRSS')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "status": "success" if not failed_metrics else "partial",
            "message": f"Sent {len(sent_metrics)} metrics to CloudWatch",
            "sent_metrics": sent_metrics,
            "failed_metrics": failed_metrics,
            "cloudwatch_namespace": "CSR-Lambda-API"
        }
        
    except Exception as e:
        logger.error(f"Manual metrics send failed: {str(e)} - Request ID: {request_id}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "status": "error",
            "message": f"Failed to send metrics: {str(e)}"
        }