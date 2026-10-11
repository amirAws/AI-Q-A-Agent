# Deployment Guide

Simple step-by-step guide to deploy the Insurance Policy RAG system on AWS.

## Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws configure
   ```

2. **Enable Bedrock Models** (IMPORTANT!)
   - Go to AWS Console → Bedrock → Model access
   - Request access to:
     - `Claude 3 Haiku` (for agent responses)
     - `Titan Embeddings V2` (for vector generation)
   - Wait for approval (~2 minutes)

3. **Set up environment**
   ```bash
   cp .env.example .env
   nano .env  # Add your AWS_ACCOUNT_ID
   ```

## One-Command Deploy

```bash
./scripts/deploy.sh
```

This creates:
- DynamoDB table (`policy-chunks`)
- IAM role with required permissions
- 3 Lambda functions (upload, search, list)
- API Gateway (HTTP API)

## Manual Steps

### 1. Create Bedrock Agent (AWS Console)

Since agent creation via CLI is complex, use the console:

**Step 1: Go to Bedrock Console**
- Navigate to: AWS Console → Bedrock → Agents
- Click "Create Agent"

**Step 2: Agent Details**
- Name: `insurance-policy-advisor`
- Description: `Health insurance policy Q&A assistant`
- Model: `Claude 3 Haiku`
- Instructions:
  ```
  You are a helpful assistant that answers questions about health insurance policies. 
  Use the search tool to find relevant information from policy documents. 
  When comparing policies, search each policy separately and provide a clear comparison. 
  Always cite the policy name and page number for your answers.
  ```

**Step 3: Add Action Group**
- Action group name: `policy-search-actions`
- Lambda function: Select `search-policies`
- API Schema: Upload `backend/agent-config.json` (use the schema section)
- Or manually define:
  - Operation: `searchPolicies` - POST /search
  - Operation: `listPolicies` - GET /list-policies

**Step 4: Test & Create Alias**
- Test the agent in console
- Create alias: `production` (or use test alias `TSTALIASID`)
- Note the Agent ID and Alias ID

**Step 5: Update Environment**
```bash
# Update .env with:
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
```

### 2. Deploy Chat Lambda

```bash
cd backend/lambdas

# Create chat function
aws lambda create-function \
    --function-name chat-with-agent \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/insurance-rag-lambda-role \
    --handler chat.lambda_handler \
    --zip-file fileb://../../lambda-package.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment "Variables={BEDROCK_AGENT_ID=your-agent-id,BEDROCK_AGENT_ALIAS_ID=your-alias-id,AWS_REGION=us-east-1}"
```

### 3. Setup API Gateway Routes

```bash
# Get your API ID
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='insurance-policy-api'].ApiId" --output text)

# Add chat route
aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key "POST /chat" \
    --target "integrations/your-integration-id"

# Add policies route
aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key "GET /policies" \
    --target "integrations/your-integration-id"

# Deploy stage
aws apigatewayv2 create-stage \
    --api-id $API_ID \
    --stage-name prod \
    --auto-deploy
```

Your API URL: `https://{API_ID}.execute-api.us-east-1.amazonaws.com/prod`

### 4. Deploy Frontend

```bash
cd frontend

# Install dependencies
npm install

# Update environment
cp .env.local.example .env.local
nano .env.local  # Add your API Gateway URL

# Build
npm run build

# Deploy to S3 + CloudFront (simple option)
aws s3 mb s3://insurance-rag-frontend
aws s3 sync out/ s3://insurance-rag-frontend --acl public-read
aws s3 website s3://insurance-rag-frontend --index-document index.html
```

Frontend URL: `http://insurance-rag-frontend.s3-website-us-east-1.amazonaws.com`

## Test the System

### 1. Upload a Policy

```bash
# Convert PDF to base64
PDF_BASE64=$(base64 -i your-policy.pdf)

# Upload
aws lambda invoke \
    --function-name upload-policy \
    --payload "{\"pdf_base64\":\"$PDF_BASE64\",\"policy_name\":\"HDFC Ergo Secure Plus\",\"policy_id\":\"hdfc-ergo\"}" \
    response.json

cat response.json
```

### 2. Test Search

```bash
aws lambda invoke \
    --function-name search-policies \
    --payload '{"apiPath":"/search","httpMethod":"POST","requestBody":{"content":{"question":"What is maternity coverage?","policy_ids":["hdfc-ergo"],"top_k":3}}}' \
    search-response.json

cat search-response.json
```

### 3. Test Agent Chat

```bash
aws lambda invoke \
    --function-name chat-with-agent \
    --payload '{"message":"What is the maternity coverage in HDFC policy?","policy_ids":["hdfc-ergo"]}' \
    chat-response.json

cat chat-response.json
```

### 4. Test Frontend

Open the frontend URL in browser, select policies, and ask questions!

## Cost Monitoring

Check your costs:
```bash
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=SERVICE
```

Expected: ~$0.50-5/month for 100 queries

## Troubleshooting

**Lambda errors:**
```bash
aws logs tail /aws/lambda/upload-policy --follow
```

**Bedrock Agent not working:**
- Check model access is enabled
- Verify Lambda permissions include Bedrock
- Test Lambda function directly first

**DynamoDB issues:**
```bash
aws dynamodb describe-table --table-name policy-chunks
```

**Frontend can't connect:**
- Check API Gateway CORS settings
- Verify API URL in .env.local
- Check browser console for errors

## Clean Up

To delete everything:
```bash
./scripts/cleanup.sh  # Coming soon
```

Or manually:
- Delete Bedrock Agent
- Delete Lambda functions
- Delete DynamoDB table
- Delete API Gateway
- Empty and delete S3 bucket
