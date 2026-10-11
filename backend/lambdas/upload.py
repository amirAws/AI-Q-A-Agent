"""
Simple PDF uploader - extracts text, chunks, and stores in DynamoDB
Uses PyPDF2 (pure Python, no binary dependencies)
"""
import json
import boto3
import base64
import os
from datetime import datetime
from io import BytesIO
from decimal import Decimal

try:
    from PyPDF2 import PdfReader
except ImportError:
    # Fallback message
    print("PyPDF2 not available")

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
s3 = boto3.client('s3')

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


def extract_pdf_from_bytes(pdf_bytes):
    """Extract text from PDF bytes using PyPDF2"""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        pages.append({
            'page': page_num,
            'text': text
        })
    
    return pages


def lambda_handler(event, context):
    """
    Upload PDF policy document
    
    Input Option 1 (base64):
    {
        "pdf_base64": "base64_encoded_pdf",
        "policy_name": "HDFC Ergo Secure Plus",
        "policy_id": "hdfc-ergo-secure"
    }
    
    Input Option 2 (S3):
    {
        "s3_bucket": "bucket-name",
        "s3_key": "path/to/file.pdf",
        "policy_name": "HDFC Ergo Secure Plus",
        "policy_id": "hdfc-ergo-secure"
    }
    """
    try:
        body = json.loads(event.get('body', json.dumps(event)))
        
        policy_name = body['policy_name']
        policy_id = body.get('policy_id', policy_name.lower().replace(' ', '-'))
        
        # Extract PDF based on input type
        if 'pdf_base64' in body:
            pdf_bytes = base64.b64decode(body['pdf_base64'])
            pages = extract_pdf_from_bytes(pdf_bytes)
        elif 's3_bucket' in body and 's3_key' in body:
            # Download from S3
            s3_bucket = body['s3_bucket']
            s3_key = body['s3_key']
            
            print(f"Downloading from S3: s3://{s3_bucket}/{s3_key}")
            s3_obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
            pdf_bytes = s3_obj['Body'].read()
            pages = extract_pdf_from_bytes(pdf_bytes)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Must provide either pdf_base64 or s3_bucket+s3_key'})
            }
        
        # Combine all text and chunk
        full_text = '\n\n'.join([p['text'] for p in pages])
        chunks = chunk_text(full_text)
        
        print(f"Extracted {len(pages)} pages, created {len(chunks)} chunks")
        
        # Store chunks with embeddings in DynamoDB
        table = dynamodb.Table(CHUNKS_TABLE)
        stored_count = 0
        
        for idx, chunk_content in enumerate(chunks):
            # Get embedding
            embedding = get_embedding(chunk_content)
            
            # Find which page this chunk belongs to
            page_num = min((idx * CHUNK_SIZE) // len(full_text.split()) + 1, len(pages))
            
            # Store in DynamoDB (convert floats to Decimal for DynamoDB)
            item = {
                'policy_id': policy_id,
                'chunk_id': f"{policy_id}#chunk_{idx:04d}",
                'text': chunk_content,
                'embedding': [Decimal(str(x)) for x in embedding],
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
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
