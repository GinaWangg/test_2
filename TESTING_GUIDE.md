# Testing Guide for Issue #1

This guide explains how to verify that the environment is set up correctly and that the `/v3/emailDetect` API endpoint returns a 200 response.

## Quick Start (Test Mode)

For testing without Azure services, you can run the application in TEST_MODE:

### Step 1: Start the Server

```bash
# Set environment variables and start the server
export TEST_MODE=true
export MYAPP_ENVIRONMENT=-test
export APP_ENV=test
export MYAPP_AZURE_SUBSCRIPTION_ID=test-subscription-id
export MYAPP_GPT4O_RESOURCE_ENDPOINT=https://test.openai.azure.com/
export MYAPP_GPT4O_API_KEY=test-api-key
export MYAPP_GPT4O_INTENTDETECT=test-deployment
export MYAPP_VECTOR_API_URL=http://localhost:8001/api
export MYAPP_GOOGLE_GENIOTRANSLATE=test-translate-key
export MYAPP_GEMINI_API_KEY=test-gemini-key

python -m main
```

Or use the provided environment file:

```bash
export $(cat .env.test | xargs)
export TEST_MODE=true
python -m main
```

The server will start at `http://127.0.0.1:8000`

### Step 2: Run the Test Script

In a separate terminal:

```bash
python test_api_endpoint.py
```

This will test the endpoint with the exact payload specified in issue #1 and verify that it returns a 200 status code.

## Expected Output

When running in TEST_MODE, you should see:

```
======================================================================
API Endpoint Test - Issue #1 Verification
======================================================================

Waiting for server to be ready...
✓ Root endpoint status: 200
  Response: {'status': 'ok'}

Testing /v3/emailDetect endpoint...
✓ Status Code: 200
✓ Message: Success (Test Mode)
✓ Response structure is valid

======================================================================
SUCCESS: All tests passed! ✓
The /v3/emailDetect endpoint returned status 200 as expected.
======================================================================
```

## Manual Testing with curl

You can also test the endpoint manually:

```bash
curl -X POST http://127.0.0.1:8000/v3/emailDetect \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "AOCC_test",
    "email": "dawid@kaczmarski.pl",
    "phone": "555444333",
    "case_date": 1747825750000,
    "site": "uk",
    "product_type": "Graphic Card",
    "email_content": "你好",
    "product_model": "K3605VC",
    "product_sn": "S1N0CX065068038",
    "problem_description_content": "你好"
  }'
```

## Production Environment

For production use with actual Azure services, you need to:

1. Set up proper Azure credentials:
   - Azure OpenAI API key and endpoint
   - Cosmos DB connection details
   - Google Translate API credentials
   - Vector API endpoint

2. Configure environment variables:
   - `MYAPP_ENVIRONMENT`: `-prod` or `-stage`
   - `MYAPP_AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID
   - `MYAPP_GPT4O_RESOURCE_ENDPOINT`: Azure OpenAI endpoint
   - `MYAPP_GPT4O_API_KEY`: Azure OpenAI API key
   - `MYAPP_GPT4O_INTENTDETECT`: Deployment name
   - `MYAPP_COSMOS_URL`: Cosmos DB URL
   - `MYAPP_COSMOS_KEY`: Cosmos DB key
   - `MYAPP_COSMOS_WRITE_DATABASE_NAME`: Database name
   - `MYAPP_VECTOR_API_URL`: Vector search API URL
   - `MYAPP_GOOGLE_GENIOTRANSLATE`: Google Translate credentials
   - `MYAPP_GEMINI_API_KEY`: Gemini API key

3. Start the server without TEST_MODE:

```bash
python -m main
```

## Test Mode vs Production Mode

**Test Mode** (`TEST_MODE=true`):
- Returns mock responses without calling external services
- Useful for CI/CD, local development, and API structure verification
- No Azure credentials needed
- Fast response times

**Production Mode** (`TEST_MODE=false` or not set):
- Calls actual Azure OpenAI, Cosmos DB, and other services
- Requires valid Azure credentials
- Returns real AI-generated responses
- Requires all external services to be accessible

## Troubleshooting

### Server won't start
- Check that all required environment variables are set
- Verify Python version is 3.10+
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Connection errors
- Verify the server is running at `http://127.0.0.1:8000`
- Check if port 8000 is available
- Try accessing `http://127.0.0.1:8000/` in a browser

### 400/500 errors in production mode
- Verify Azure credentials are correct
- Check that all external services are accessible
- Review server logs for detailed error messages
- Consider using TEST_MODE for initial verification
