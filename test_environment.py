#!/usr/bin/env python3
"""
Environment Setup Verification Script

This script checks if all required environment variables are set and
verifies basic application setup without requiring external API access.
"""

import os
import sys


def check_env_var(var_name: str, required: bool = True) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    if value:
        print(f"✓ {var_name}: Set")
        return True
    else:
        status = "✗ MISSING (required)" if required else "- Not set (optional)"
        print(f"{status} {var_name}")
        return not required


def main():
    """Run environment verification checks."""
    print("=" * 60)
    print("AOCC Email Copilot - Environment Setup Verification")
    print("=" * 60)
    print()
    
    all_good = True
    
    print("Checking Core Environment Variables:")
    print("-" * 60)
    all_good &= check_env_var("MYAPP_ENVIRONMENT")
    all_good &= check_env_var("MYAPP_AZURE_SUBSCRIPTION_ID")
    print()
    
    print("Checking API Integration Variables:")
    print("-" * 60)
    all_good &= check_env_var("MYAPP_VECTOR_API_URL")
    all_good &= check_env_var("MYAPP_GPT4O_RESOURCE_ENDPOINT")
    all_good &= check_env_var("MYAPP_GPT4O_API_KEY")
    all_good &= check_env_var("MYAPP_GPT4O_INTENTDETECT")
    all_good &= check_env_var("MYAPP_GEMINI_API_KEY")
    all_good &= check_env_var("MYAPP_GOOGLE_GENIOTRANSLATE")
    print()
    
    print("Checking Optional Cosmos DB Variables:")
    print("-" * 60)
    check_env_var("MYAPP_COSMOS_URL", required=False)
    check_env_var("MYAPP_COSMOS_KEY", required=False)
    check_env_var("MYAPP_COSMOS_WRITE_DATABASE_NAME", required=False)
    print()
    
    print("Checking Python Dependencies:")
    print("-" * 60)
    try:
        import fastapi
        print(f"✓ fastapi: {fastapi.__version__}")
    except ImportError:
        print("✗ fastapi: Not installed")
        all_good = False
    
    try:
        import uvicorn
        print(f"✓ uvicorn: {uvicorn.__version__}")
    except ImportError:
        print("✗ uvicorn: Not installed")
        all_good = False
    
    try:
        from google import genai
        print("✓ google-genai: Installed")
    except ImportError:
        print("✗ google-genai: Not installed")
        all_good = False
    
    try:
        import openai
        print(f"✓ openai: {openai.__version__}")
    except ImportError:
        print("✗ openai: Not installed")
        all_good = False
    
    print()
    print("=" * 60)
    if all_good:
        print("✓ All required environment variables and dependencies are set!")
        print()
        print("You can now start the server with:")
        print("  python -m main")
        print()
        print("And test the endpoint with:")
        print("  curl -X POST http://127.0.0.1:8000/v3/emailDetect \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d @test_payload.json")
        return 0
    else:
        print("✗ Some required environment variables or dependencies are missing.")
        print("Please set the missing variables before starting the server.")
        print()
        print("See ENVIRONMENT_SETUP.md for more details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
