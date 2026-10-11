"""
Simple PDF uploader - extracts text, chunks, and stores in DynamoDB
"""
import json
import boto3
import fitz  # PyMuPDF
import base64
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

CHUNKS_TABLE = os.environ.get('CHUNKS_TABLE', 'policy-chunks')
CHUNK_SIZE = 500  # words per chunk
OVERLAP = 50      # word overlap


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), size - overlap):
        chunk = ' '.join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def get_embedding(text):
    """Get Titan embedding from Bedrock"""
    body = json.dumps({"inputText": text})
    
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['embedding']


def extract_pdf_text(pdf_base64):
    """Extract text from base64 PDF"""
    pdf_bytes = base64.b64decode(pdf_base64)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append({
            'page': page_num,
            'text': text
        })
    
    return pages


def lambda_handler(event, context):
    """
    Upload PDF policy document
    
    Input:
    {
        "pdf_base64": "base64_encoded_pdf",
        "policy_name": "HDFC Ergo Secure Plus",
        "policy_id": "hdfc-ergo-secure"  # optional, auto-generated if missing
    }
    """
    try:
        body = json.loads(event.get('body', event))
        
        pdf_base64 = body['pdf_base64']
        policy_name = body['policy_name']
        policy_id = body.get('policy_id', policy_name.lower().replace(' ', '-'))
        
        # Extract text from PDF
        pages = extract_pdf_text(pdf_base64)
        
        # Combine all text and chunk
        full_text = '\n\n'.join([p['text'] for p in pages])
        chunks = chunk_text(full_text)
        
        print(f"Extracted {len(pages)} pages, created {len(chunks)} chunks")
        
        # Store chunks with embeddings in DynamoDB
        table = dynamodb.Table(CHUNKS_TABLE)
        stored_count = 0
        
        for idx, chunk_text in enumerate(chunks):
            # Get embedding
            embedding = get_embedding(chunk_text)
            
            # Find which page this chunk belongs to
            page_num = (idx * CHUNK_SIZE) // len(full_text.split()) + 1
            page_num = min(page_num, len(pages))
            
            # Store in DynamoDB
            item = {
                'policy_id': policy_id,
                'chunk_id': f"{policy_id}#chunk_{idx:04d}",
                'text': chunk_text,
                'embedding': embedding,
                'page': page_num,
                'policy_name': policy_name,
                'created_at': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=item)
            stored_count += 1
            
            if stored_count % 10 == 0:
                print(f"Stored {stored_count}/{len(chunks)} chunks")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Policy uploaded successfully',
                'policy_id': policy_id,
                'policy_name': policy_name,
                'chunks_created': len(chunks),
                'pages': len(pages)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
