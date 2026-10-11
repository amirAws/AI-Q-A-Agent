# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER / ASSOCIATE                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js on S3)                      │
│  - Policy multi-selector dropdown                               │
│  - Chat interface                                               │
│  - Displays citations with page numbers                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   API GATEWAY (HTTP API)                         │
│  Routes:                                                         │
│  - POST /chat        → chat-with-agent Lambda                   │
│  - GET  /policies    → list-policies Lambda                     │
│  - POST /upload      → upload-policy Lambda (admin)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ↓            ↓            ↓
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  upload-policy   │ │  list-policies   │ │ chat-with-agent  │
│     Lambda       │ │     Lambda       │ │     Lambda       │
│                  │ │                  │ │                  │
│ - Extract PDF    │ │ - Scan DynamoDB  │ │ - Invoke Agent   │
│ - Chunk text     │ │ - Return list    │ │ - Stream output  │
│ - Get embeddings │ │                  │ │                  │
│ - Store DynamoDB │ │                  │ │                  │
└────────┬─────────┘ └─────────┬────────┘ └────────┬─────────┘
         │                     │                    │
         │                     │                    ↓
         │                     │         ┌────────────────────┐
         │                     │         │  BEDROCK AGENT     │
         │                     │         │  (Orchestrator)    │
         │                     │         │                    │
         │                     │         │ - Claude 3 Haiku   │
         │                     │         │ - Action Groups    │
         │                     │         │ - Tool Calling     │
         │                     │         └─────────┬──────────┘
         │                     │                   │
         │                     │                   ↓
         │                     │         ┌────────────────────┐
         │                     │         │ search-policies    │
         │                     │         │    Lambda          │
         │                     │         │  (Agent Router)    │
         │                     │         │                    │
         │                     │         │ - Vector search    │
         │                     │         │ - Cosine similarity│
         │                     │         └─────────┬──────────┘
         │                     │                   │
         └─────────────────────┴───────────────────┘
                               │
                               ↓
                    ┌──────────────────────┐
                    │  DynamoDB             │
                    │  Table: policy-chunks │
                    │                       │
                    │  - policy_id (PK)     │
                    │  - chunk_id (SK)      │
                    │  - text               │
                    │  - embedding [1024]   │
                    │  - page               │
                    │  - policy_name        │
                    └──────────────────────┘
                               ↑
                               │
                    ┌──────────┴──────────┐
                    │  Amazon Bedrock      │
                    │                      │
                    │  - Titan Embeddings  │
                    │    (generate vectors)│
                    │                      │
                    │  - Claude 3 Haiku    │
                    │    (LLM responses)   │
                    └──────────────────────┘
```

## Data Flow

### 1. Upload Policy Flow
```
PDF File → upload-policy Lambda
    ↓
Extract text with PyMuPDF (page by page)
    ↓
Chunk text (500 words, 50 overlap)
    ↓
For each chunk:
    - Call Bedrock Titan → get embedding [1024 dims]
    - Store in DynamoDB: {policy_id, chunk_id, text, embedding, page}
    ↓
Return success
```

### 2. Query Flow (Agentic)
```
User question + selected policies → chat-with-agent Lambda
    ↓
Invoke Bedrock Agent with question
    ↓
Agent decides: "I need to search policies"
    ↓
Agent calls searchPolicies tool (action group)
    ↓
search-policies Lambda triggered:
    - Get question embedding from Titan
    - Scan DynamoDB for selected policies
    - Calculate cosine similarity for each chunk
    - Return top-5 most similar chunks
    ↓
Agent receives chunks with citations
    ↓
Claude 3 Haiku generates answer with sources
    ↓
Stream response back to user
    ↓
Frontend displays with policy name + page number
```

### 3. Comparison Flow
```
User: "Compare maternity in HDFC vs Aditya Birla"
    ↓
Agent reasoning:
    1. List available policies
    2. Search "maternity coverage" in HDFC
    3. Search "maternity coverage" in Aditya Birla
    4. Compare results
    5. Generate structured comparison
    ↓
Response: "HDFC offers ₹50K (page 12), Aditya offers ₹1L (page 8)"
```

## Components

### Backend (Python)
- **upload.py** (180 lines) - PDF processing
- **search.py** (120 lines) - Vector similarity search
- **list_policies.py** (60 lines) - Get policy list
- **agent_router.py** (80 lines) - Route agent requests
- **chat.py** (70 lines) - Bedrock Agent invocation

**Total: ~500 lines of Python**

### Frontend (TypeScript/React)
- **page.tsx** (150 lines) - Main UI
- **layout.tsx** (20 lines) - HTML wrapper

**Total: ~170 lines of TypeScript**

### Infrastructure (Shell)
- **deploy.sh** (150 lines) - Automated deployment
- **test-upload.sh** (20 lines) - Test helper

**Total: ~170 lines of Bash**

## Why This Architecture?

### ✅ Pros
1. **Fully Serverless** - No servers to manage
2. **AWS-Native** - Uses $100 credits
3. **Agentic** - Agent decides when to search, compare
4. **Simple** - <1000 lines total code
5. **Cheap** - ~$2-5/month for 100 queries
6. **Scalable** - Can handle 1000s of queries if needed
7. **No External Dependencies** - No OpenAI, Pinecone, etc.

### ⚠️ Tradeoffs
1. **In-Memory Search** - Not ideal for 1000+ policies
2. **Cold Starts** - Lambda warmup ~1-2s
3. **Manual Agent Setup** - AWS Console required for Bedrock Agent
4. **DynamoDB Scan** - Not optimized for large datasets

### 🚀 Future Optimizations (if needed)
1. Replace DynamoDB with Aurora Serverless + pgvector
2. Add Redis/ElastiCache for embedding cache
3. Use Lambda SnapStart for instant warmup
4. Add CloudFront CDN for frontend
5. Implement streaming responses in UI

## Security

- **IAM Roles**: Lambda has minimal required permissions
- **API Gateway**: Can add API keys, Cognito auth
- **S3**: Frontend can be behind CloudFront with OAI
- **Bedrock**: Managed service, no data retention
- **DynamoDB**: Encrypted at rest

## Monitoring

- **CloudWatch Logs**: All Lambda logs
- **CloudWatch Metrics**: Invocations, errors, duration
- **X-Ray**: Can enable for distributed tracing
- **Cost Explorer**: Track spending

## Cost Breakdown (100 queries/month)

| Service | Cost |
|---------|------|
| Bedrock (Claude + Titan) | $0.40 |
| DynamoDB | $0.00 (free tier) |
| Lambda | $0.00 (free tier) |
| API Gateway | $0.00 (free tier) |
| S3 | $0.00 (free tier) |
| **Total** | **$0.40/month** |

**With $100 credit:** Runs for ~250 months (20+ years)! 🎉
