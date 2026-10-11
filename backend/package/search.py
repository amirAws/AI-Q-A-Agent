"""
Simple vector search with cosine similarity
"""
import json
import boto3
import os
import numpy as np
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

CHUNKS_TABLE = os.environ.get('CHUNKS_TABLE', 'policy-chunks')


def get_embedding(text):
    """Get Titan embedding from Bedrock"""
    body = json.dumps({"inputText": text})
    
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['embedding']


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1, dtype=np.float32)
    vec2 = np.array(vec2, dtype=np.float32)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    return float(dot_product / (norm1 * norm2))


def convert_decimals(obj):
    """Convert DynamoDB Decimal to float"""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def lambda_handler(event, context):
    """
    Search for relevant chunks
    
    Input:
    {
        "question": "What is maternity coverage?",
        "policy_ids": ["hdfc-ergo-secure", "aditya-birla-max"],  # optional
        "top_k": 5
    }
    """
    try:
        body = json.loads(event.get('body', event))
        
        question = body['question']
        policy_ids = body.get('policy_ids', [])
        top_k = body.get('top_k', 5)
        
        # Get question embedding
        query_embedding = get_embedding(question)
        
        # Fetch chunks from DynamoDB
        table = dynamodb.Table(CHUNKS_TABLE)
        
        if policy_ids:
            # Scan specific policies
            all_chunks = []
            for policy_id in policy_ids:
                response = table.query(
                    KeyConditionExpression='policy_id = :pid',
                    ExpressionAttributeValues={':pid': policy_id}
                )
                all_chunks.extend(response.get('Items', []))
        else:
            # Scan all policies
            response = table.scan()
            all_chunks = response.get('Items', [])
        
        print(f"Found {len(all_chunks)} chunks to search")
        
        # Calculate similarities
        results = []
        for chunk in all_chunks:
            chunk = convert_decimals(chunk)
            embedding = chunk.get('embedding', [])
            
            if embedding:
                similarity = cosine_similarity(query_embedding, embedding)
                results.append({
                    'policy_id': chunk['policy_id'],
                    'policy_name': chunk['policy_name'],
                    'text': chunk['text'],
                    'page': chunk['page'],
                    'similarity': similarity
                })
        
        # Sort by similarity and get top K
        results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = results[:top_k]
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': top_results,
                'total_searched': len(all_chunks)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
