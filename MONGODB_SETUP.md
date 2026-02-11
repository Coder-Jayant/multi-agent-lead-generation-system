# MongoDB Setup - Quick Guide

## ⚠️ Docker Not Available

Since Docker is not installed, we'll use **MongoDB Atlas** (cloud) - it's FREE and takes 2 minutes!

## Option 1: MongoDB Atlas (Recommended - 2 minutes) ☁️

### Step 1: Create Free Account
1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Sign up (free, no credit card needed)
3. Click "Create a FREE Cluster"

### Step 2: Create Cluster (Use defaults)
1. Choose **FREE** tier (M0)
2. Select provider: AWS
3. Region: Closest to you
4. Click "Create Cluster" (takes ~3 minutes)

### Step 3: Setup Access
1. **Database Access**: 
   - Click "Database Access" → "Add New Database User"
   - Username: `leadgen_user`
   - Password: `leadgen_pass123` (or auto-generate)
   - Database User Privileges: "Atlas admin"
   - Click "Add User"

2. **Network Access**:
   - Click "Network Access" → "Add IP Address"
   - Click "Allow Access from Anywhere" (for testing)
   - Click "Confirm"

### Step 4: Get Connection String
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Driver: Python, Version: 3.12 or later
4. Copy connection string, it looks like:
   ```
   mongodb+srv://leadgen_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

5. Replace `<password>` with your actual password

### Step 5: Configure App
Edit `LeadGenAgent/.env`:
```bash
MONGODB_URI=mongodb+srv://leadgen_user:leadgen_pass123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=leadgen
```

---

## Option 2: Local MongoDB (If you prefer local)

### Windows:
```powershell
# Download MongoDB Community Edition
# https://www.mongodb.com/try/download/community

# Or use Chocolatey
choco install mongodb

# Start MongoDB
mongod
```

### Configuration for local:
```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=leadgen
```

---

## Test Connection

Once configured, run:

```bash
cd LeadGenAgent
python -c "import asyncio; from db.mongodb import get_db_manager; asyncio.run(get_db_manager().configure('YOUR_URI', 'leadgen'))"
```

Or run the full test suite:

```bash
pytest tests/test_mongodb.py -v
```

---

## Quick MongoDB Atlas Setup (Complete Example)

**Example `.env`**:
```bash
# Replace with YOUR actual Atlas connection string
MONGODB_URI=mongodb+srv://leadgen_user:leadgen_pass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=leadgen

# Other services (keep existing)
SEARXNG_BASE_URL=http://49.50.117.66:8082
FIRECRAWL_BASE_URL=http://49.50.117.66:3002
OPENAI_BASE_URL=http://49.50.117.66:8000/v1
OPENAI_MODEL=/model
OPENAI_API_KEY=not-needed
```

---

## Verify It's Working ✅

```python
# test_connection.py
import asyncio
from db.mongodb import get_db_manager

async def test():
    mgr = get_db_manager()
    result = await mgr.configure(
        "YOUR_MONGODB_URI",
        "leadgen"
    )
    print("Config:", result)
    
    health = await mgr.health_check()
    print("Health:", health)

asyncio.run(test())
```

Should output:
```
Config: {'status': 'success', 'message': 'Connected to MongoDB database: leadgen', ...}
Health: {'status': 'healthy', ...}
```

---

## Next Steps After MongoDB is Ready

1. ✅ Configure connection string in `.env`
2. ✅ Run: `pytest tests/test_mongodb.py -v`
3. ✅ Continue with Phase 2 implementation (Agent Tools)
