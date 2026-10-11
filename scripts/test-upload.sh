#!/bin/bash
# Simple script to test PDF upload

if [ -z "$1" ]; then
    echo "Usage: ./test-upload.sh <pdf-file> <policy-name> <policy-id>"
    echo "Example: ./test-upload.sh hdfc.pdf 'HDFC Ergo Secure Plus' hdfc-ergo"
    exit 1
fi

PDF_FILE=$1
POLICY_NAME=${2:-"Test Policy"}
POLICY_ID=${3:-"test-policy"}

echo "Converting PDF to base64..."
PDF_BASE64=$(base64 -i "$PDF_FILE" | tr -d '\n')

echo "Uploading policy: $POLICY_NAME"

aws lambda invoke \
    --function-name upload-policy \
    --payload "{\"pdf_base64\":\"$PDF_BASE64\",\"policy_name\":\"$POLICY_NAME\",\"policy_id\":\"$POLICY_ID\"}" \
    response.json

echo ""
echo "Response:"
cat response.json
echo ""
