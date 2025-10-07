#!/bin/bash

# Create test user in Cognito
set -e

USER_POOL_ID="ap-northeast-1_HluYCXwCo"
EMAIL="test@example.com"
TEMP_PASSWORD="TempPass123!"
FINAL_PASSWORD="Test123!@#"

echo "Creating test user: $EMAIL"

# Create user
aws cognito-idp admin-create-user \
    --user-pool-id "$USER_POOL_ID" \
    --username "$EMAIL" \
    --user-attributes Name=email,Value="$EMAIL" Name=email_verified,Value=true \
    --temporary-password "$TEMP_PASSWORD" \
    --message-action SUPPRESS

echo "Setting permanent password..."

# Set permanent password
aws cognito-idp admin-set-user-password \
    --user-pool-id "$USER_POOL_ID" \
    --username "$EMAIL" \
    --password "$FINAL_PASSWORD" \
    --permanent

echo "✅ Test user created successfully!"
echo "📧 Email: $EMAIL"
echo "🔑 Password: $FINAL_PASSWORD"