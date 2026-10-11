#!/bin/bash
set -e

echo "🚀 Deploying Insurance Policy RAG System..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

AWS_REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=${AWS_ACCOUNT_ID}

if [ -z "$ACCOUNT_ID" ]; then
    echo "Getting AWS Account ID..."
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

echo "Account ID: $ACCOUNT_ID"
echo "Region: $AWS_REGION"

# 1. Create DynamoDB Table
echo ""
echo "📦 Creating DynamoDB table..."
aws dynamodb create-table \
    --table-name policy-chunks \
    --attribute-definitions \
        AttributeName=policy_id,AttributeType=S \
        AttributeName=chunk_id,AttributeType=S \
    --key-schema \
        AttributeName=policy_id,KeyType=HASH \
        AttributeName=chunk_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION \
    2>/dev/null || echo "Table already exists"

# 2. Create IAM Role for Lambda
echo ""
echo "🔐 Creating IAM role for Lambda..."
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
    --role-name insurance-rag-lambda-role \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    2>/dev/null || echo "Role already exists"

# Attach policies
aws iam attach-role-policy \
    --role-name insurance-rag-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    2>/dev/null || true

aws iam attach-role-policy \
    --role-name insurance-rag-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess \
    2>/dev/null || true

aws iam attach-role-policy \
    --role-name insurance-rag-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess \
    2>/dev/null || true

# Wait for role to be ready
echo "Waiting for IAM role to propagate..."
sleep 10

# 3. Package and deploy Lambda functions
echo ""
echo "📦 Packaging Lambda functions..."

cd backend
python3 -m pip install -r requirements.txt -t package/ --quiet
cd package
cp ../lambdas/*.py .
zip -r ../../lambda-package.zip . -q
cd ../..

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/insurance-rag-lambda-role"

# Deploy upload function
echo ""
echo "🚀 Deploying upload-policy Lambda..."
aws lambda create-function \
    --function-name upload-policy \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler upload.lambda_handler \
    --zip-file fileb://lambda-package.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name upload-policy \
    --zip-file fileb://lambda-package.zip \
    --region $AWS_REGION

# Deploy search function
echo "🚀 Deploying search-policies Lambda..."
aws lambda create-function \
    --function-name search-policies \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler agent_router.lambda_handler \
    --zip-file fileb://lambda-package.zip \
    --timeout 60 \
    --memory-size 512 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name search-policies \
    --zip-file fileb://lambda-package.zip \
    --region $AWS_REGION

# Deploy list policies function
echo "🚀 Deploying list-policies Lambda..."
aws lambda create-function \
    --function-name list-policies \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler list_policies.lambda_handler \
    --zip-file fileb://lambda-package.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment "Variables={CHUNKS_TABLE=policy-chunks,AWS_REGION=$AWS_REGION}" \
    --region $AWS_REGION \
    2>/dev/null || aws lambda update-function-code \
    --function-name list-policies \
    --zip-file fileb://lambda-package.zip \
    --region $AWS_REGION

# 4. Create Bedrock Agent
echo ""
echo "🤖 Creating Bedrock Agent..."
echo "⚠️  Note: Bedrock Agent creation requires manual setup via AWS Console"
echo "   Follow the instructions in DEPLOYMENT.md"

# 5. Create API Gateway
echo ""
echo "🌐 Creating API Gateway..."
API_ID=$(aws apigatewayv2 create-api \
    --name insurance-policy-api \
    --protocol-type HTTP \
    --region $AWS_REGION \
    --query 'ApiId' \
    --output text 2>/dev/null || echo "exists")

if [ "$API_ID" != "exists" ]; then
    echo "API Gateway ID: $API_ID"
    
    # Create routes
    aws apigatewayv2 create-integration \
        --api-id $API_ID \
        --integration-type AWS_PROXY \
        --integration-uri "arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:list-policies" \
        --payload-format-version 2.0 \
        --region $AWS_REGION
    
    echo "API URL: https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com"
else
    echo "API Gateway already exists"
fi

# Cleanup
rm -f /tmp/trust-policy.json
rm -rf backend/package
rm -f lambda-package.zip

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Enable Bedrock model access in AWS Console (Claude 3 Haiku, Titan Embeddings)"
echo "2. Create Bedrock Agent manually (see DEPLOYMENT.md)"
echo "3. Update .env with BEDROCK_AGENT_ID"
echo "4. Deploy frontend: cd frontend && npm run build"
echo ""
