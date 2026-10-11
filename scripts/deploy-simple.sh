#!/bin/bash
set -e

echo "🚀 Simple Deployment for Insurance Policy RAG..."

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

AWS_REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=${AWS_ACCOUNT_ID}

echo "Account ID: $ACCOUNT_ID"
echo "Region: $AWS_REGION"

# Create smaller Lambda package (without numpy - we'll use layers)
echo ""
echo "📦 Creating lightweight Lambda package..."

cd backend
mkdir -p package_light
python3 -m pip install boto3 PyMuPDF -t package_light/ --quiet

cd package_light
cp ../lambdas/*.py .

# Create small zip
zip -r ../../lambda-light.zip . -q -x "*.pyc" -x "*/__pycache__/*"
cd ../..

echo "Package size: $(ls -lh lambda-light.zip | awk '{print $5}')"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/insurance-rag-lambda-role"

# Deploy Lambda functions
echo ""
echo "🚀 Deploying Lambda functions..."

# Upload function
aws lambda create-function \
    --function-name upload-policy \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler upload.lambda_handler \
    --zip-file fileb://lambda-light.zip \
    --timeout 300 \
    --memory-size 1024 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name upload-policy \
    --zip-file fileb://lambda-light.zip \
    --region $AWS_REGION

echo "✅ upload-policy deployed"

# Search function  
aws lambda create-function \
    --function-name search-policies \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler agent_router.lambda_handler \
    --zip-file fileb://lambda-light.zip \
    --timeout 60 \
    --memory-size 512 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name search-policies \
    --zip-file fileb://lambda-light.zip \
    --region $AWS_REGION

echo "✅ search-policies deployed"

# List policies function
aws lambda create-function \
    --function-name list-policies \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler list_policies.lambda_handler \
    --zip-file fileb://lambda-light.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name list-policies \
    --zip-file fileb://lambda-light.zip \
    --region $AWS_REGION

echo "✅ list-policies deployed"

# Chat function (will be deployed after agent creation)
echo "⏭️  chat-with-agent will be deployed after Bedrock Agent is created"

# Cleanup
rm -rf backend/package_light
rm -f lambda-light.zip

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to AWS Console → Bedrock → Agents"
echo "2. Create agent (see DEPLOYMENT.md)"
echo "3. Come back here with Agent ID"
echo ""
