# MongoDB Database Layer - Quick Test Guide

## Setup

### 1. Install MongoDB

**Option A: Local MongoDB (Recommended for testing)**
```bash
# Windows (using Chocolatey)
choco install mongodb

# Or download from: https://www.mongodb.com/try/download/community
```

**Option B: MongoDB Atlas (Cloud)**
- Sign up at https://www.mongodb.com/cloud/atlas
- Create free cluster
- Get connection string

### 2. Install Dependencies

```bash
cd LeadGenAgent
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env`:
```bash
# For local MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=leadgen

# For MongoDB Atlas
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

## Running Tests

### Quick Test (requires MongoDB running)

```bash
# Start MongoDB (if local)
# mongod

# Run all tests
pytest tests/test_mongodb.py -v

# Run specific test
pytest tests/test_mongodb.py::test_mongodb_configuration -v
```

### Expected Output

```
tests/test_mongodb.py::test_mongodb_configuration PASSED
tests/test_mongodb.py::test_product_creation PASSED
tests/test_mongodb.py::test_lead_creation_with_qualification PASSED
tests/test_mongodb.py::test_duplicate_detection PASSED
tests/test_mongodb.py::test_get_leads_by_product PASSED
tests/test_mongodb.py::test_filter_leads_by_score PASSED

====== 6 passed in 2.34s ======
```

## Manual Testing with Python

```python
import asyncio
from db.mongodb import get_db_manager
from db.models import Product, Lead, EmailDetail, LeadQualification

async def test_connection():
    # Get manager
    manager = get_db_manager()
    
    # Configure
    result = await manager.configure(
        "mongodb://localhost:27017",
        "leadgen"
    )
    print(result)
    
    # Health check
    health = await manager.health_check()
    print(health)

# Run
asyncio.run(test_connection())
```

## What's Tested

✅ MongoDB connection and configuration
✅ Product creation with metadata  
✅ Lead creation with emails and qualification
✅ Duplicate detection by domain
✅ Querying leads by product
✅ Filtering leads by qualification score

## Next Steps

Once tests pass, we'll:
1. Create agent tools for database operations
2. Build API endpoints
3. Integrate with ReAct agent
