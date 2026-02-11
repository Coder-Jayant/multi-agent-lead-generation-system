"""
Quick Test Script - MongoDB API
Tests MongoDB configuration and basic operations
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("🧪 MongoDB API Quick Test")
print("="*60)

# Step 1: Configure MongoDB
print("\n1. Configuring MongoDB...")
config_data = {
    "mongo_uri": "mongodb://leadgen_admin:LeadGen%402026Secure@49.50.117.66:27017/",
    "database_name": "leadgen"
}

response = requests.post(f"{BASE_URL}/api/config/mongodb", json=config_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 2: Check MongoDB health
print("\n2. Checking MongoDB health...")
response = requests.get(f"{BASE_URL}/api/config/mongodb/health")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 3: Create a test product
print("\n3. Creating test product...")
product_data = {
    "name": "AI Voicebot Platform",
    "description": "Advanced voice AI platform for customer service automation with natural language processing",
    "target_personas": ["C-Level", "VP/Director", "IT Manager"],
    "industries": ["Technology", "Healthcare", "Finance"],
    "regions": ["North America", "Europe", "Asia"]
}

response = requests.post(f"{BASE_URL}/api/products", json=product_data)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Response: {json.dumps(result, indent=2)}")

if result.get('status') == 'success':
    product_id = result['product_id']
    print(f"\n✅ Product created with ID: {product_id}")
    
    # Step 4: Get product details
    print("\n4. Getting product details...")
    response = requests.get(f"{BASE_URL}/api/products/{product_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Step 5: List all products
    print("\n5. Listing all products...")
    response = requests.get(f"{BASE_URL}/api/products")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {data.get('count', 0)} products")
    print(f"Response: {json.dumps(data, indent=2)}")

print("\n" + "="*60)
print("✅ Quick test complete!")
print("="*60 + "\n")
