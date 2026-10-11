# Testing Your Insurance RAG System

## 🎉 System is Running!

### Frontend
**URL:** http://localhost:3000

The frontend is already running! Open it in your browser.

### Pages:
1. **Home (/)** - Chat interface
   - Select policies from dropdown
   - Ask questions
   - View responses with citations

2. **Upload (/upload)** - Upload policy PDFs
   - Drag & drop or select PDF
   - Enter policy name
   - Auto-generated policy ID
   - See upload progress

## Current Status

### ✅ Working:
- Frontend UI (Next.js)
- API Gateway endpoints
- Lambda functions deployed
- DynamoDB table created
- S3 bucket for uploads
- PDF extraction (PyPDF2)

### ⏳ Waiting for:
- **Bedrock verification** (~1-2 hours from AWS)
- Check your email for verification confirmation
- Or wait until Bedrock API starts working

### Error You'll See (Until Bedrock is Verified):
```
"Your account is currently being verified. Verification normally takes less than 2 hours."
```

This is normal! Once verified, everything will work automatically.

## Testing Steps

### 1. Test Frontend (Now)
```bash
# Frontend is already running at http://localhost:3000
open http://localhost:3000
```

### 2. Test Policy List API
```bash
curl https://xdaegx5zff.execute-api.us-east-1.amazonaws.com/prod/policies
```

Expected: `{"policies":[],"count":0}` (no policies yet)

### 3. Upload a Policy (After Bedrock Verified)

**Via Frontend:**
1. Go to http://localhost:3000/upload
2. Click "Choose File" and select a PDF
3. Enter policy name (e.g., "Aditya Birla Activ Health")
4. Click "Upload Policy"
5. Wait for processing (may take 1-2 minutes)

**Via Script:**
```bash
cd /Users/apple/Documents/amir/AI-Q-A-Agent
./scripts/upload-via-s3.sh sample_policies/aditya_birla_activ.pdf "Aditya Birla Activ Health" "aditya-birla-activ"
```

### 4. Test Chat (After Upload)

**Via Frontend:**
1. Go to http://localhost:3000
2. Select policy from dropdown
3. Ask: "What is maternity coverage?"
4. See response with page citations

**Via API:**
```bash
curl -X POST https://xdaegx5zff.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is maternity coverage?",
    "policy_ids": ["aditya-birla-activ"]
  }'
```

## Troubleshooting

### Bedrock Not Working
**Error:** "Your account is currently being verified"
**Solution:** Wait 1-2 hours, then try again

### Upload Fails
**Check:** Is Bedrock verified? (Embeddings need Bedrock)
**Check:** Is file a valid PDF?
**Check:** Is file size < 10MB?

### Chat Returns Empty
**Check:** Have you uploaded any policies?
**Check:** Did upload complete successfully?
**Check:** Try refreshing the policy list

### CORS Errors
**Check:** API Gateway CORS is configured (already done)
**Check:** Using correct API URL in .env.local

## Sample Questions to Ask

Once policies are uploaded:

1. "What is the maternity coverage limit?"
2. "Compare premium amounts between policies"
3. "What are the exclusions?"
4. "What is the waiting period for pre-existing conditions?"
5. "Does this cover pre-natal expenses?"

## Monitoring

### Check Lambda Logs
```bash
# Upload function
aws logs tail /aws/lambda/upload-policy --follow

# Chat function
aws logs tail /aws/lambda/chat-with-policies --follow

# Search function
aws logs tail /aws/lambda/search-policies --follow
```

### Check DynamoDB
```bash
# Count items in table
aws dynamodb scan --table-name policy-chunks --select COUNT
```

### Check API Gateway
```bash
# Test endpoints
curl https://xdaegx5zff.execute-api.us-east-1.amazonaws.com/prod/policies
```

## Next Steps

1. **Wait for Bedrock verification** (check email)
2. **Upload sample policies**
3. **Test question answering**
4. **Try multi-policy comparison**
5. **Deploy frontend to S3** (optional, for production)

## Production Deployment (Optional)

```bash
# Build frontend
cd frontend
npm run build

# Deploy to S3
aws s3 sync out/ s3://your-bucket-name --acl public-read

# Or use Vercel/Netlify for free hosting
```

## Cost Tracking

```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2026-10-01,End=2026-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

Expected: ~$0-5/month for development usage

---

## 🎉 Enjoy Your RAG System!

Questions? Check the main README.md or DEPLOYMENT.md
