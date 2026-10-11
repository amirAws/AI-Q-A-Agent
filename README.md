# Health Insurance Policy RAG - Q&A Agent

**Simple AWS-native agentic RAG system for policy comparison**

## Architecture (SIMPLE)

```
PDF Upload → Lambda → DynamoDB (vectors) → Bedrock Agent → Chat UI
```

### Tech Stack
- **Agent**: Amazon Bedrock Agent (Claude 3 Haiku)
- **Vector Store**: DynamoDB (in-memory search)
- **Embeddings**: Bedrock Titan V2
- **Backend**: 3 Lambda functions
- **Frontend**: Next.js (static)

### Monthly Cost: ~$0.50 (100 queries/month)

## Project Structure

```
.
├── backend/
│   ├── lambdas/
│   │   ├── upload.py          # PDF → chunks → DynamoDB
│   │   ├── embed.py           # Generate Titan embeddings
│   │   └── search.py          # Cosine similarity search
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx       # Main chat UI
│   │   └── components/
│   │       └── Chat.tsx       # Chat component
│   └── package.json
├── scripts/
│   └── deploy.sh              # One-click deploy
└── .env.example
```

## Quick Start

See **[QUICKSTART.md](QUICKSTART.md)** for 5-minute setup guide.

```bash
# 1. Deploy
./scripts/deploy.sh

# 2. Enable Bedrock models (Console)
# 3. Create Bedrock Agent (Console - 2 min)

# 4. Upload policy
./scripts/test-upload.sh your-policy.pdf "Policy Name" policy-id

# 5. Run frontend
cd frontend && npm install && npm run dev
```

**Full details:** [DEPLOYMENT.md](DEPLOYMENT.md)

## How It Works

1. **Upload**: PDF → text → chunks (500 words) → Titan embeddings → DynamoDB
2. **Query**: User question → Bedrock Agent → Search Lambda → Top 5 chunks → Claude generates answer
3. **Agent**: Decides which policies to search, compares results, cites sources

## DynamoDB Schema

**Table: policy-chunks**
```
{
  "policy_id": "hdfc-ergo-secure",
  "chunk_id": "chunk_001",
  "text": "Maternity coverage...",
  "embedding": [0.123, 0.456, ...],  // 1024-dim vector
  "page": 12,
  "metadata": {...}
}
```

## License
MIT
