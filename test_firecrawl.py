"""
Test Firecrawl API endpoints
Run this to verify Firecrawl is working correctly
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

FIRECRAWL_BASE_URL = os.getenv("FIRECRAWL_BASE_URL", "")

print("=" * 60)
print("Firecrawl API Test Suite")
print("=" * 60)
print(f"\nFirecrawl Base URL: {FIRECRAWL_BASE_URL}")

if not FIRECRAWL_BASE_URL:
    print("❌ ERROR: FIRECRAWL_BASE_URL not set in .env")
    exit(1)

# Test 1: Health Check
print("\n" + "=" * 60)
print("Test 1: Health Check")
print("=" * 60)

try:
    response = requests.get(f"{FIRECRAWL_BASE_URL}/health", timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print("⚠️ Unexpected status code")
except Exception as e:
    print(f"❌ Health check failed: {e}")

# Test 2: Scrape endpoint (simple)
print("\n" + "=" * 60)
print("Test 2: Simple Scrape (if supported)")
print("=" * 60)

test_url = "https://example.com"
try:
    response = requests.post(
        f"{FIRECRAWL_BASE_URL}/v1/scrape",
        json={"url": test_url},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print("✅ Scrape endpoint working")
    else:
        print(f"Response: {response.text[:500]}")
        print("⚠️ Scrape endpoint may not be available or has different format")
except Exception as e:
    print(f"❌ Scrape test failed: {e}")

# Test 3: Extract endpoint (structured extraction)
print("\n" + "=" * 60)
print("Test 3: Extract Endpoint (Structured)")
print("=" * 60)

schema = {
    "company_name": "string - company name",
    "description": "string - company description"
}

try:
    response = requests.post(
        f"{FIRECRAWL_BASE_URL}/v1/extract",
        json={
            "url": test_url,
            "schema": schema,
            "timeout": 15000
        },
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Extracted data: {json.dumps(data.get('data', {}), indent=2)}")
        print("✅ Extract endpoint working")
    elif response.status_code == 402:
        print("⚠️ Payment required - Firecrawl may need API key or credits")
        print(f"Response: {response.text}")
    elif response.status_code == 404:
        print("❌ Extract endpoint not found")
        print(f"Response: {response.text}")
        print("\nTrying alternative endpoint: /v0/extract")
        
        # Try v0
        response_v0 = requests.post(
            f"{FIRECRAWL_BASE_URL}/v0/extract",
            json={
                "url": test_url,
                "schema": schema
            },
            timeout=30
        )
        print(f"V0 Status Code: {response_v0.status_code}")
        print(f"V0 Response: {response_v0.text[:500]}")
    else:
        print(f"Response: {response.text[:500]}")
        print("⚠️ Unexpected response")
        
except Exception as e:
    print(f"❌ Extract test failed: {e}")

# Test 4: Check available endpoints
print("\n" + "=" * 60)
print("Test 4: Discover Available Endpoints")
print("=" * 60)

endpoints_to_test = [
    "/",
    "/v0/scrape",
    "/v1/scrape",
    "/v0/extract",
    "/v1/extract",
    "/api/scrape",
    "/scrape"
]

print("Testing common endpoints...")
for endpoint in endpoints_to_test:
    try:
        url = f"{FIRECRAWL_BASE_URL}{endpoint}"
        response = requests.get(url, timeout=5)
        if response.status_code != 404:
            print(f"✅ {endpoint:20s} - Status: {response.status_code}")
    except:
        pass

# Test 5: Try with actual company domain
print("\n" + "=" * 60)
print("Test 5: Real Company Test")
print("=" * 60)

real_test_url = "https://www.cyfuture.com"
schema_full = {
    "company_name": "string - official company name",
    "description": "string - company description (max 200 chars)",
    "email": "string - contact email",
    "phone": "string - contact phone"
}

print(f"Testing URL: {real_test_url}")

try:
    response = requests.post(
        f"{FIRECRAWL_BASE_URL}/v1/extract",
        json={
            "url": real_test_url,
            "schema": schema_full,
            "timeout": 20000
        },
        timeout=35
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        extracted = data.get('data', {})
        print("\n📊 Extracted Data:")
        print(json.dumps(extracted, indent=2))
        print("\n✅ Successfully extracted company data!")
    else:
        print(f"Response: {response.text[:1000]}")
        
except Exception as e:
    print(f"❌ Real test failed: {e}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("\nIf errors occurred, possible issues:")
print("1. Firecrawl not running - check docker containers")
print("2. Wrong port - verify FIRECRAWL_BASE_URL")
print("3. API key required - some Firecrawl versions need authentication")
print("4. Different API version - try v0 instead of v1")
print("\nTo start Firecrawl:")
print("  git clone https://github.com/mendableai/firecrawl")
print("  cd firecrawl")
print("  docker-compose up -d")
print("=" * 60)
