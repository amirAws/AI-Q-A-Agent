"""
Router Lambda for Bedrock Agent action groups
Routes agent requests to appropriate functions
"""
import json
from search import lambda_handler as search_handler
from list_policies import lambda_handler as list_handler


def lambda_handler(event, context):
    """
    Route Bedrock Agent requests to appropriate handlers
    
    Bedrock Agent sends events in this format:
    {
        "actionGroup": "policy-search-actions",
        "apiPath": "/search",
        "httpMethod": "POST",
        "requestBody": {...}
    }
    """
    try:
        print(f"Agent event: {json.dumps(event)}")
        
        # Extract request details
        api_path = event.get('apiPath', '')
        http_method = event.get('httpMethod', 'GET')
        request_body = event.get('requestBody', {})
        
        # Route to appropriate handler
        if api_path == '/search' and http_method == 'POST':
            # Call search handler
            result = search_handler({'body': json.dumps(request_body.get('content', {}))}, context)
            response_body = json.loads(result['body'])
            
        elif api_path == '/list-policies' and http_method == 'GET':
            # Call list handler
            result = list_handler({}, context)
            response_body = json.loads(result['body'])
            
        else:
            response_body = {'error': f'Unknown path: {api_path}'}
        
        # Return in Bedrock Agent format
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup'),
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(response_body)
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error in router: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }
