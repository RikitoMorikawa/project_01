from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import auth, users, health
from app.middleware import (
    request_id_middleware,
    timing_middleware,
    error_handling_middleware,
    security_headers_middleware
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting CSR Lambda API...")
    yield
    # Shutdown
    logger.info("Shutting down CSR Lambda API...")

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Serverless API backend for CSR application with AWS Lambda",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "prod" else None,
    redoc_url="/redoc" if settings.environment != "prod" else None,
)

# Security middleware - Trusted Host
if settings.environment == "prod":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*.execute-api.ap-northeast-1.amazonaws.com", "*.cloudfront.net"]
    )

# Add custom middleware (order matters - first added is outermost)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(error_handling_middleware)
app.middleware("http")(timing_middleware)
app.middleware("http")(request_id_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(users.router, prefix="/api/v1/users", tags=["ユーザー"])
app.include_router(health.router, prefix="/api/v1/health", tags=["ヘルスチェック"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CSR Lambda API is running",
        "version": settings.api_version,
        "environment": settings.environment
    }