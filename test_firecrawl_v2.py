"""
Test Firecrawl v2 API format
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_BASE_URL = os.getenv("FIRECRAWL_BASE_URL", "")

print("Testing Firecrawl V2 API Format")
print("=" * 60)

# Test v2 scrape format
test_url = "https://www.cyfuture.com"

# Try different v2 formats
formats_to_try = [
    {
        "name": "V2 Format 1: Direct URL in body",
        "endpoint": "/v2/scrape",
        "body": {"url": test_url}
    },
    {
        "name": "V2 Format 2: Scrape without schema",
        "endpoint": "/scrape",
        "body": {"url": test_url}
    },
    {
        "name": "V2 Format 3: Just domain",
        "endpoint": "/v2/scrape",
        "body": {test_url}  # Just the URL string
    }
]

for test in formats_to_try:
    print(f"\n{test['name']}")
    print("-" * 60)
    try:
        response = requests.post(
            f"{FIRECRAWL_BASE_URL}{test['endpoint']}",
            json=test['body'],
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Keys: {list(data.keys())}")
            print(f"Data preview: {str(data)[:200]}...")
            break
        else:
            print(f"Response: {response.text[:300]}")
    except Exception as e:
        print(f"Error: {e}")

# Check documentation endpoint
print("\n" + "=" * 60)
print("Checking for API docs")
print("=" * 60)

doc_endpoints = ["/docs", "/api-docs", "/swagger", "/"]
for endpoint in doc_endpoints:
    try:
        response = requests.get(f"{FIRECRAWL_BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200 and len(response.text) > 100:
            print(f"✅ Found docs at: {endpoint}")
            print(f"Content preview: {response.text[:500]}...")
            break
    except:
        pass
