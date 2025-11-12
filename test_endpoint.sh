#!/bin/bash
# 
# Test script for AOCC Email Copilot endpoint
# This script demonstrates how to test the /v3/emailDetect endpoint
# when all environment variables are properly configured.
#

set -e

echo "=========================================="
echo "AOCC Email Copilot Endpoint Test Script"
echo "=========================================="
echo ""

# Step 1: Verify environment
echo "Step 1: Verifying environment setup..."
if ! python test_environment.py; then
    echo ""
    echo "ERROR: Environment verification failed."
    echo "Please set the missing environment variables before running this script."
    exit 1
fi

echo ""
echo "Step 2: Starting the FastAPI server..."
echo "Note: This will start the server in the background."
echo ""

# Start server in background
python -m main &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "ERROR: Server failed to start. Check the logs above for errors."
    exit 1
fi

echo "Server started successfully (PID: $SERVER_PID)"
echo ""

# Step 3: Test health endpoint
echo "Step 3: Testing health endpoint..."
if curl -s http://127.0.0.1:8000/ | grep -q "ok"; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo ""

# Step 4: Test the emailDetect endpoint
echo "Step 4: Testing /v3/emailDetect endpoint..."
echo "Sending POST request with test payload..."
echo ""

HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" \
    -X POST http://127.0.0.1:8000/v3/emailDetect \
    -H "Content-Type: application/json" \
    -d @test_payload.json)

echo "HTTP Status Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ SUCCESS: Received HTTP 200 response"
    echo ""
    echo "Response body:"
    cat /tmp/response.json | python -m json.tool
    echo ""
    RESULT=0
elif [ "$HTTP_CODE" = "400" ]; then
    echo "✗ FAILED: Received HTTP 400 Bad Request"
    echo ""
    echo "Response body:"
    cat /tmp/response.json | python -m json.tool
    echo ""
    echo "This typically means:"
    echo "  - Input validation failed, or"
    echo "  - External API calls failed (check network connectivity)"
    RESULT=1
else
    echo "✗ FAILED: Received unexpected HTTP status code: $HTTP_CODE"
    echo ""
    echo "Response body:"
    cat /tmp/response.json
    echo ""
    RESULT=1
fi

# Cleanup
echo ""
echo "Step 5: Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
rm -f /tmp/response.json
echo "Server stopped."

echo ""
echo "=========================================="
if [ $RESULT -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed. See output above for details."
fi
echo "=========================================="

exit $RESULT
