#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for verifying the email detection API endpoint.
This script tests the /v3/emailDetect endpoint with the payload specified in issue #1.

Usage:
    Ensure the server is running with TEST_MODE=true:
    $ export TEST_MODE=true
    $ python -m main

    Then in another terminal, run this test script:
    $ python test_api_endpoint.py
"""

import requests
import json
import sys
import time


def test_root_endpoint():
    """Test the root endpoint to verify server is running."""
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"✓ Root endpoint status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Server is not running at http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"✗ Error testing root endpoint: {e}")
        return False


def test_email_detect_endpoint():
    """Test the /v3/emailDetect endpoint with the payload from issue #1."""
    # Test payload from issue #1
    payload = {
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
    }

    try:
        print("\nTesting /v3/emailDetect endpoint...")
        response = requests.post(
            "http://127.0.0.1:8000/v3/emailDetect",
            json=payload,
            timeout=30
        )
        
        print(f"✓ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Message: {result.get('message', 'N/A')}")
            print(f"✓ Response structure is valid")
            print(f"\nFull Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"✗ Expected status code 200, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Request timeout - the endpoint took too long to respond")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Cannot connect to http://127.0.0.1:8000")
        print("  Make sure the server is running with: python -m main")
        return False
    except Exception as e:
        print(f"✗ Error testing /v3/emailDetect endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("=" * 70)
    print("API Endpoint Test - Issue #1 Verification")
    print("=" * 70)
    
    # Wait a bit for server to be ready
    print("\nWaiting for server to be ready...")
    time.sleep(2)
    
    # Test root endpoint
    root_ok = test_root_endpoint()
    if not root_ok:
        print("\n" + "=" * 70)
        print("FAILED: Server is not accessible")
        print("=" * 70)
        sys.exit(1)
    
    # Test emailDetect endpoint
    email_detect_ok = test_email_detect_endpoint()
    
    # Print summary
    print("\n" + "=" * 70)
    if root_ok and email_detect_ok:
        print("SUCCESS: All tests passed! ✓")
        print("The /v3/emailDetect endpoint returned status 200 as expected.")
    else:
        print("FAILED: Some tests failed ✗")
    print("=" * 70)
    
    sys.exit(0 if (root_ok and email_detect_ok) else 1)


if __name__ == "__main__":
    main()
