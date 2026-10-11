"""
List all available policies (for dropdown)
"""
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
CHUNKS_TABLE = os.environ.get('CHUNKS_TABLE', 'policy-chunks')


def lambda_handler(event, context):
    """
    Get list of all policies
    
    Returns:
    {
        "policies": [
            {"policy_id": "hdfc-ergo-secure", "policy_name": "HDFC Ergo Secure Plus"},
            ...
        ]
    }
    """
    try:
        table = dynamodb.Table(CHUNKS_TABLE)
        
        # Scan and get unique policies
        response = table.scan(
            ProjectionExpression='policy_id, policy_name'
        )
        
        items = response.get('Items', [])
        
        # Get unique policies
        policies = {}
        for item in items:
            policy_id = item['policy_id']
            if policy_id not in policies:
                policies[policy_id] = {
                    'policy_id': policy_id,
                    'policy_name': item['policy_name']
                }
        
        policy_list = list(policies.values())
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'policies': policy_list,
                'count': len(policy_list)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
