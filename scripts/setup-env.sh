#!/bin/bash

# Environment setup script for CSR Lambda API System

set -e

ENVIRONMENT=${1:-dev}

echo "Setting up environment: $ENVIRONMENT"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "Error: Invalid environment. Use dev, staging, or prod"
    exit 1
fi

# Copy environment files
echo "Copying environment configuration files..."

# Backend environment
if [ -f "backend/.env.$ENVIRONMENT" ]; then
    cp "backend/.env.$ENVIRONMENT" "backend/.env"
    echo "✓ Backend environment file copied"
else
    echo "✗ Backend environment file not found: backend/.env.$ENVIRONMENT"
    exit 1
fi

# Frontend environment
if [ -f "frontend/.env.$ENVIRONMENT" ]; then
    cp "frontend/.env.$ENVIRONMENT" "frontend/.env.local"
    echo "✓ Frontend environment file copied"
else
    echo "✗ Frontend environment file not found: frontend/.env.$ENVIRONMENT"
    exit 1
fi

echo "Environment setup complete for: $ENVIRONMENT"
echo ""
echo "Next steps:"
echo "1. Update environment variables in the copied files"
echo "2. For development: docker-compose up -d"
echo "3. For other environments: Deploy using CI/CD pipeline"