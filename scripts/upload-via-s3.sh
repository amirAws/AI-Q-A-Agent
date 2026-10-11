#!/bin/bash
# Upload policy via S3 (for large PDFs)

if [ -z "$1" ]; then
    echo "Usage: ./upload-via-s3.sh <pdf-file> <policy-name> <policy-id>"
    exit 1
fi

PDF_FILE="$1"
POLICY_NAME="${2:-Test Policy}"
POLICY_ID="${3:-test-policy}"
S3_BUCKET="lambda-deploy-498283326819"

echo "📄 Uploading: $PDF_FILE"
echo "📝 Policy Name: $POLICY_NAME"
echo "🆔 Policy ID: $POLICY_ID"
echo ""

# Upload PDF to S3
echo "Uploading PDF to S3..."
aws s3 cp "$PDF_FILE" "s3://$S3_BUCKET/uploads/${POLICY_ID}.pdf"

# Trigger Lambda with S3 path
echo ""
echo "Processing PDF..."
cat > /tmp/upload-payload.json <<EOF
{
  "s3_bucket": "$S3_BUCKET",
  "s3_key": "uploads/${POLICY_ID}.pdf",
  "policy_name": "$POLICY_NAME",
  "policy_id": "$POLICY_ID"
}
EOF

aws lambda invoke \
    --function-name upload-policy \
    --payload file:///tmp/upload-payload.json \
    --region us-east-1 \
    /tmp/upload-response.json

echo ""
echo "✅ Response:"
cat /tmp/upload-response.json | python3 -m json.tool 2>/dev/null || cat /tmp/upload-response.json
echo ""
