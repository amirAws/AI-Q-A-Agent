"""
Chat endpoint - invokes Bedrock Agent
"""
import json
import boto3
import os

bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

AGENT_ID = os.environ.get('BEDROCK_AGENT_ID')
AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')


def lambda_handler(event, context):
    """
    Chat with Bedrock Agent
    
    Input:
    {
        "message": "Compare maternity coverage in HDFC vs Aditya Birla",
        "session_id": "user-123",  # optional
        "policy_ids": ["hdfc-ergo-secure", "aditya-birla-max"]  # optional context
    }
    """
    try:
        body = json.loads(event.get('body', event))
        
        message = body['message']
        session_id = body.get('session_id', 'default-session')
        policy_ids = body.get('policy_ids', [])
        
        # Add policy context to message if provided
        if policy_ids:
            message = f"[Selected policies: {', '.join(policy_ids)}] {message}"
        
        # Invoke Bedrock Agent
        response = bedrock_agent.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message
        )
        
        # Stream response chunks
        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'response': completion,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
