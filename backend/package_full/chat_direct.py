"""
Direct chat with Claude (without Bedrock Agent)
Simple RAG: search → retrieve context → send to Claude
"""
import json
import boto3
import os
from search import lambda_handler as search_handler, cosine_similarity, get_embedding

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    """
    Direct chat endpoint
    
    Input:
    {
        "message": "What is maternity coverage?",
        "policy_ids": ["hdfc-ergo", "aditya-birla"],  # optional
        "session_id": "user-123"
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        message = body['message']
        policy_ids = body.get('policy_ids', [])
        
        print(f"Question: {message}")
        print(f"Policies: {policy_ids}")
        
        # Step 1: Search for relevant chunks
        search_event = {
            'body': json.dumps({
                'question': message,
                'policy_ids': policy_ids,
                'top_k': 5
            })
        }
        
        search_response = search_handler(search_event, context)
        search_body = json.loads(search_response['body'])
        results = search_body.get('results', [])
        
        print(f"Found {len(results)} relevant chunks")
        
        # Step 2: Build context from search results
        context_parts = []
        for idx, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {idx}: {result['policy_name']}, Page {result['page']}]\n"
                f"{result['text']}\n"
            )
        
        context = "\n".join(context_parts)
        
        # Step 3: Build prompt for Claude
        system_prompt = """You are a helpful insurance policy advisor. Answer questions based ONLY on the provided policy documents. 
Always cite the source and page number. If the answer is not in the documents, say so clearly.
Be concise and factual."""
        
        user_prompt = f"""Based on the following insurance policy information, please answer the question.

POLICY INFORMATION:
{context}

QUESTION: {message}

Please provide a clear answer with citations (policy name and page number)."""
        
        # Step 4: Call Amazon Nova (AWS's own model - no payment method required)
        converse_request = {
            "modelId": "amazon.nova-lite-v1:0",
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": user_prompt}]
                }
            ],
            "system": [{"text": system_prompt}],
            "inferenceConfig": {
                "maxTokens": 2000,
                "temperature": 0.3
            }
        }
        
        try:
            response = bedrock.converse(**converse_request)
            answer = response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Converse API failed: {e}")
            raise e
        
        print(f"Answer: {answer[:100]}...")
        
        # Step 5: Return response with sources
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'response': answer,
                'sources': [
                    {
                        'policy_name': r['policy_name'],
                        'page': r['page'],
                        'similarity': round(r['similarity'], 3)
                    }
                    for r in results
                ],
                'policy_ids': policy_ids
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process question'
            })
        }
