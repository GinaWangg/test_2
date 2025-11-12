# Environment Setup Guide for AOCC Email Copilot

## Overview
This document describes the environment setup required to run the FastAPI application and test the `/v3/emailDetect` endpoint.

## Required Environment Variables

The application requires the following environment variables to be set:

### Core Variables
- `MYAPP_ENVIRONMENT`: Environment identifier (e.g., `-dev`, `-stage`, `-prod`)
- `MYAPP_AZURE_SUBSCRIPTION_ID`: Azure subscription ID for Application Insights

### API Integration Variables
- `MYAPP_VECTOR_API_URL`: URL for the vector search/Redis API service
- `MYAPP_GPT4O_RESOURCE_ENDPOINT`: Azure OpenAI GPT-4o endpoint URL
- `MYAPP_GPT4O_API_KEY`: Azure OpenAI GPT-4o API key
- `MYAPP_GPT4O_INTENTDETECT`: GPT-4o model deployment name
- `MYAPP_GEMINI_API_KEY`: Base64-encoded Google service account credentials for Gemini API
- `MYAPP_GOOGLE_GENIOTRANSLATE`: Base64-encoded Google service account credentials for Translation API

### Cosmos DB Variables (optional, used for logging)
- `MYAPP_COSMOS_URL`: Cosmos DB endpoint URL
- `MYAPP_COSMOS_KEY`: Cosmos DB access key
- `MYAPP_COSMOS_WRITE_DATABASE_NAME`: Cosmos DB database name for write operations

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Local Development
```bash
python -m main
```

The server will start on `http://127.0.0.1:8000`

### Testing the `/v3/emailDetect` Endpoint

Once the server is running, you can test the endpoint with:

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

Expected successful response (HTTP 200):
```json
{
  "status": 200,
  "message": "Success",
  "output": {
    "case_id": "AOCC_test",
    "gpt_extract": {
      "user_summary": "...",
      "type": "available",
      "email_split_sentence": [...]
    },
    "check_info": {
      "start_time_ts": 1234567890,
      "end_time_ts": 1234567890,
      "lang": "zh",
      "product_line": "...",
      "email_split_info": [...]
    }
  }
}
```

## Network Requirements

The application requires outbound HTTPS access to:
- `oauth2.googleapis.com` - Google OAuth2 authentication
- Azure OpenAI endpoints
- Vector search/Redis API endpoints
- Cosmos DB endpoints (if configured)

## Known Limitations in Sandboxed Environments

This application cannot run in environments with restricted internet access because it requires:
1. Real-time API calls to Google Cloud services (Gemini, Translation)
2. Real-time API calls to Azure OpenAI services
3. Real-time API calls to vector search databases

For testing in sandboxed/offline environments, consider:
- Mocking external API calls
- Using test fixtures instead of real API responses
- Running integration tests in an environment with proper network access
