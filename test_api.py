"""
API Endpoint Testing Script
Tests all MongoDB endpoints to ensure they're working correctly
"""

import requests
import json
from typing import Dict, Any

# Base URL
BASE_URL = "http://localhost:8000"

def print_response(name: str, response: requests.Response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")
    return response

def test_mongodb_health():
    """Test MongoDB health check"""
    response = requests.get(f"{BASE_URL}/api/config/mongodb/health")
    print_response("MongoDB Health Check", response)
    return response.status_code == 200

def test_create_product():
    """Test creating a product"""
    product_data = {
        "name": "AI Voicebot",
        "description": "Agentic voicebot for customer support with natural language processing and automated call handling",
        "target_personas": ["C-Level", "VP/Director", "IT Manager"],
        "industries": ["Technology", "Healthcare", "Finance"],
        "regions": ["North America", "Europe"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/products",
        json=product_data
    )
    result = print_response("Create Product", response)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('product_id')
    return None

def test_list_products():
    """Test listing all products"""
    response = requests.get(f"{BASE_URL}/api/products")
    print_response("List All Products", response)
    return response.json() if response.status_code == 200 else None

def test_get_product(product_id: str):
    """Test getting a single product"""
    response = requests.get(f"{BASE_URL}/api/products/{product_id}")
    print_response(f"Get Product {product_id}", response)
    return response.status_code == 200

def test_get_product_leads(product_id: str):
    """Test getting leads for a product"""
    response = requests.get(f"{BASE_URL}/api/products/{product_id}/leads")
    print_response(f"Get Leads for Product {product_id}", response)
    return response.status_code == 200

def test_filter_leads():
    """Test filtering leads"""
    # Test with no filters
    response = requests.get(f"{BASE_URL}/api/leads/filter")
    print_response("Filter Leads (No Filters)", response)
    
    # Test with min_score filter
    response = requests.get(f"{BASE_URL}/api/leads/filter?min_score=80")
    print_response("Filter Leads (min_score=80)", response)
    
    return response.status_code == 200

def test_general_health():
    """Test general health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("General Health Check", response)
    return response.status_code == 200

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print("🧪 Starting API Endpoint Tests")
    print("="*60)
    
    results = {}
    
    try:
        # Test 1: General Health
        print("\n📍 Test 1: General Health Check")
        results['health'] = test_general_health()
        
        # Test 2: MongoDB Health
        print("\n📍 Test 2: MongoDB Health")
        results['mongodb_health'] = test_mongodb_health()
        
        if not results['mongodb_health']:
            print("\n❌ MongoDB not healthy! Skipping remaining tests.")
            return results
        
        # Test 3: Create Product
        print("\n📍 Test 3: Create Product")
        product_id = test_create_product()
        results['create_product'] = product_id is not None
        
        if not product_id:
            print("\n⚠️ Failed to create product. Skipping product-specific tests.")
            return results
        
        # Test 4: List Products
        print("\n📍 Test 4: List Products")
        products_data = test_list_products()
        results['list_products'] = products_data is not None
        
        # Test 5: Get Single Product
        print("\n📍 Test 5: Get Single Product")
        results['get_product'] = test_get_product(product_id)
        
        # Test 6: Get Product Leads
        print("\n📍 Test 6: Get Product Leads")
        results['get_product_leads'] = test_get_product_leads(product_id)
        
        # Test 7: Filter Leads
        print("\n📍 Test 7: Filter Leads")
        results['filter_leads'] = test_filter_leads()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, passed_status in results.items():
            status = "✅ PASS" if passed_status else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! API is working correctly.")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed. Please check errors above.")
        
        print("="*60)
        
        return results
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server!")
        print("Make sure the server is running: python api/main.py")
        return {}
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    run_all_tests()
