#!/bin/bash
# Upload a policy PDF via Lambda

if [ -z "$1" ]; then
    echo "Usage: ./upload-test.sh <pdf-file> <policy-name> <policy-id>"
    echo "Example: ./upload-test.sh policy.pdf 'Aditya Birla Activ Health' aditya-birla-activ"
    exit 1
fi

PDF_FILE="$1"
POLICY_NAME="${2:-Test Policy}"
POLICY_ID="${3:-test-policy}"

echo "📄 Uploading: $PDF_FILE"
echo "📝 Policy Name: $POLICY_NAME"
echo "🆔 Policy ID: $POLICY_ID"
echo ""

# Convert PDF to base64
echo "Converting PDF to base64..."
PDF_BASE64=$(base64 -i "$PDF_FILE" | tr -d '\n')

echo "Uploading to Lambda..."

# Invoke Lambda
aws lambda invoke \
    --function-name upload-policy \
    --payload "{\"pdf_base64\":\"$PDF_BASE64\",\"policy_name\":\"$POLICY_NAME\",\"policy_id\":\"$POLICY_ID\"}" \
    --region us-east-1 \
    /tmp/upload-response.json > /dev/null

echo ""
echo "✅ Response:"
cat /tmp/upload-response.json | python3 -m json.tool
echo ""
