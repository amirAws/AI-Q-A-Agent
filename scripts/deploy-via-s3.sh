#!/bin/bash
set -e

echo "🚀 Deploying via S3..."

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

AWS_REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=${AWS_ACCOUNT_ID}
S3_BUCKET="lambda-deploy-${ACCOUNT_ID}"

echo "Creating S3 bucket for Lambda code..."
aws s3 mb s3://$S3_BUCKET --region $AWS_REGION 2>/dev/null || echo "Bucket exists"

echo "Uploading Lambda package to S3..."
aws s3 cp lambda-light.zip s3://$S3_BUCKET/lambda-light.zip

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/insurance-rag-lambda-role"

echo "Deploying Lambda functions from S3..."

# Upload function
aws lambda create-function \
    --function-name upload-policy \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler upload.lambda_handler \
    --code S3Bucket=$S3_BUCKET,S3Key=lambda-light.zip \
    --timeout 300 \
    --memory-size 1024 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name upload-policy \
    --s3-bucket $S3_BUCKET \
    --s3-key lambda-light.zip \
    --region $AWS_REGION

echo "✅ upload-policy"

# Search function
aws lambda create-function \
    --function-name search-policies \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler agent_router.lambda_handler \
    --code S3Bucket=$S3_BUCKET,S3Key=lambda-light.zip \
    --timeout 60 \
    --memory-size 512 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name search-policies \
    --s3-bucket $S3_BUCKET \
    --s3-key lambda-light.zip \
    --region $AWS_REGION

echo "✅ search-policies"

# List function
aws lambda create-function \
    --function-name list-policies \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler list_policies.lambda_handler \
    --code S3Bucket=$S3_BUCKET,S3Key=lambda-light.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name list-policies \
    --s3-bucket $S3_BUCKET \
    --s3-key lambda-light.zip \
    --region $AWS_REGION

echo "✅ list-policies"

echo ""
echo "✅ All Lambda functions deployed!"
echo ""
