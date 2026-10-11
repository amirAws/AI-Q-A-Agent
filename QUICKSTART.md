# Quick Start Guide

Get the system running in **5 minutes**.

## Step 1: Prerequisites (2 min)

```bash
# Ensure AWS CLI is configured
aws sts get-caller-identity

# Enable Bedrock models (AWS Console)
# Go to: Bedrock → Model access → Request access
# Enable: Claude 3 Haiku + Titan Embeddings V2
```

## Step 2: Deploy Backend (1 min)

```bash
# Clone/navigate to project
cd AI-Q-A-Agent

# Setup environment
cp .env.example .env
# Edit .env and add your AWS_ACCOUNT_ID

# Deploy everything
./scripts/deploy.sh
```

## Step 3: Create Bedrock Agent (2 min)

**Via AWS Console:**
1. Go to: Bedrock → Agents → Create Agent
2. Name: `insurance-policy-advisor`
3. Model: Claude 3 Haiku
4. Instructions: (copy from DEPLOYMENT.md)
5. Add Action Group:
   - Name: `policy-search-actions`
   - Lambda: `search-policies`
   - Define 2 operations:
     - `searchPolicies`: POST /search
     - `listPolicies`: GET /list-policies
6. Create & note Agent ID

## Step 4: Test Upload

```bash
# Upload a sample policy PDF
./scripts/test-upload.sh your-policy.pdf "HDFC Ergo" hdfc-ergo
```

## Step 5: Run Frontend (Local)

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:3000

## Usage

1. **Upload policies** using test-upload.sh
2. **Select policies** from dropdown
3. **Ask questions**:
   - "What is maternity coverage?"
   - "Compare premium amounts"
   - "What are exclusions?"

## Quick Test Commands

```bash
# List all policies
aws lambda invoke \
    --function-name list-policies \
    --payload '{}' \
    output.json && cat output.json

# Search
aws lambda invoke \
    --function-name search-policies \
    --payload '{"apiPath":"/search","httpMethod":"POST","requestBody":{"content":{"question":"maternity coverage"}}}' \
    output.json && cat output.json
```

## Cost

**For 100 queries/month:** ~$2-5/month

## Need Help?

- Check `DEPLOYMENT.md` for detailed instructions
- View logs: `aws logs tail /aws/lambda/upload-policy --follow`
- Issues? Open GitHub issue
