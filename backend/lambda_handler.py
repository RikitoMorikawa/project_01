import logging
import os
from mangum import Mangum
from app.main import app

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configure Mangum for Lambda
handler = Mangum(
    app,
    lifespan="off",  # Disable lifespan for Lambda
    api_gateway_base_path="/v1" if os.getenv("ENVIRONMENT") != "dev" else None
)

# Lambda handler wrapper for additional logging
def lambda_handler(event, context):
    """
    AWS Lambda handler with enhanced logging and error handling
    """
    try:
        logger.info(f"Lambda invoked with event: {event.get('httpMethod', 'UNKNOWN')} {event.get('path', 'UNKNOWN')}")
        
        # Call the Mangum handler
        response = handler(event, context)
        
        logger.info(f"Lambda response status: {response.get('statusCode', 'UNKNOWN')}")
        return response
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", exc_info=True)
        
        # Return a proper error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            },
            "body": '{"error_code": "LAMBDA_ERROR", "message": "Internal server error"}'
        }