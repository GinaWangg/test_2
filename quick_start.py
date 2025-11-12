#!/usr/bin/env python3
"""
Quick Start Guide - AOCC Email Copilot

This script demonstrates the minimum setup required to test the
/v3/emailDetect endpoint in a working environment.
"""

import os
import sys

def print_section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")

def main():
    print_section("AOCC Email Copilot - Quick Start Guide")
    
    print("This application is a FastAPI microservice that processes customer")
    print("support emails using AI models (GPT-4, Gemini) for intent detection")
    print("and knowledge base matching.\n")
    
    print_section("STEP 1: Set Required Environment Variables")
    
    print("Before starting the server, ensure these environment variables are set:\n")
    
    env_vars = {
        "Core Variables": {
            "MYAPP_ENVIRONMENT": "Environment identifier (e.g., -dev, -stage, -prod)",
            "MYAPP_AZURE_SUBSCRIPTION_ID": "Azure subscription ID for monitoring",
        },
        "API Integration": {
            "MYAPP_VECTOR_API_URL": "Vector search API endpoint",
            "MYAPP_GPT4O_RESOURCE_ENDPOINT": "Azure OpenAI endpoint",
            "MYAPP_GPT4O_API_KEY": "Azure OpenAI API key",
            "MYAPP_GPT4O_INTENTDETECT": "GPT-4o deployment name",
            "MYAPP_GEMINI_API_KEY": "Base64-encoded Google service account (Gemini)",
            "MYAPP_GOOGLE_GENIOTRANSLATE": "Base64-encoded Google service account (Translate)",
        }
    }
    
    for category, vars_dict in env_vars.items():
        print(f"{category}:")
        for var, desc in vars_dict.items():
            status = "✓" if os.getenv(var) else "✗"
            print(f"  {status} {var}")
            print(f"     {desc}")
        print()
    
    print_section("STEP 2: Check Current Environment Status")
    
    print("Run the environment verification script:")
    print("  $ python test_environment.py\n")
    
    print_section("STEP 3: Start the Server")
    
    print("Once all environment variables are set:")
    print("  $ python -m main\n")
    print("The server will start on: http://127.0.0.1:8000\n")
    print("You can access the API documentation at: http://127.0.0.1:8000/docs")
    print("(Note: docs are disabled in production environment)\n")
    
    print_section("STEP 4: Test the /v3/emailDetect Endpoint")
    
    print("Use the provided test script:")
    print("  $ bash test_endpoint.sh\n")
    
    print("Or test manually with curl:")
    print("  $ curl -X POST http://127.0.0.1:8000/v3/emailDetect \\")
    print("      -H 'Content-Type: application/json' \\")
    print("      -d @test_payload.json\n")
    
    print_section("Expected Response")
    
    print("On success (HTTP 200), you should receive:")
    print('''{
  "status": 200,
  "message": "Success",
  "output": {
    "case_id": "AOCC_test",
    "gpt_extract": {
      "user_summary": "Greeting message",
      "type": "unclear_description",
      "email_split_sentence": [...]
    },
    "check_info": {
      "start_time_ts": 1234567890,
      "end_time_ts": 1234567891,
      "lang": "zh",
      "product_line": "graphic_card",
      "email_split_info": [...]
    }
  }
}\n''')
    
    print_section("Troubleshooting")
    
    print("Common Issues:\n")
    print("1. HTTP 400 - Bad Request")
    print("   - Check if all required environment variables are set")
    print("   - Verify network connectivity to external APIs")
    print("   - Check API credentials are valid\n")
    
    print("2. Server Won't Start")
    print("   - Verify MYAPP_AZURE_SUBSCRIPTION_ID is set")
    print("   - Verify MYAPP_VECTOR_API_URL is set")
    print("   - Check if port 8000 is already in use\n")
    
    print("3. Connection Errors to External APIs")
    print("   - Ensure outbound HTTPS is allowed to:")
    print("     - oauth2.googleapis.com")
    print("     - Azure OpenAI endpoints")
    print("     - Vector search API endpoint\n")
    
    print_section("Additional Resources")
    
    print("- ENVIRONMENT_SETUP.md - Detailed setup instructions")
    print("- VERIFICATION_SUMMARY.md - Environment verification results")
    print("- test_environment.py - Environment verification script")
    print("- test_endpoint.sh - Automated endpoint testing script")
    print("- test_payload.json - Sample request payload\n")
    
    print_section("Current Status")
    
    missing_vars = []
    for category, vars_dict in env_vars.items():
        for var in vars_dict.keys():
            if not os.getenv(var):
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  {len(missing_vars)} required environment variable(s) are not set:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables before starting the server.")
        return 1
    else:
        print("✓ All required environment variables are set!")
        print("\nYou're ready to start the server with: python -m main")
        return 0

if __name__ == "__main__":
    sys.exit(main())
