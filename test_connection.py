"""
Quick MongoDB connection test script
Run in LeadGenAgent directory after setting MONGODB_URI in .env
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_mongodb_connection():
    """Test MongoDB connection with current environment settings"""
    
    print("🧪 Testing MongoDB Connection...")
    print("=" * 60)
    
    # Get environment variables
    mongo_uri = os.getenv('MONGODB_URI', '')
    db_name = os.getenv('MONGODB_DATABASE', 'leadgen')
    
    if not mongo_uri:
        print("❌ ERROR: MONGODB_URI not set in .env file!")
        print("\n📝 Please add to .env:")
        print("   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/")
        print("   MONGODB_DATABASE=leadgen")
        return False
    
    # Mask password in URI for display
    display_uri = mongo_uri
    if '@' in display_uri:
        parts = display_uri.split('@')
        if '://' in parts[0]:
            protocol, creds = parts[0].split('://')
            display_uri = f"{protocol}://***:***@{parts[1]}"
    
    print(f"📍 MongoDB URI: {display_uri}")
    print(f"💾 Database: {db_name}")
    print()
    
    try:
        # Import database manager
        from db.mongodb import get_db_manager
        
        # Get manager instance
        manager = get_db_manager()
        
        # Configure connection
        print("⏳ Connecting to MongoDB...")
        result = await manager.configure(mongo_uri, db_name)
        
        if result['status'] == 'success':
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            return False
        
        # Run health check
        print("\n⏳ Running health check...")
        health = await manager.health_check()
        
        if health['status'] == 'healthy':
            print(f"✅ MongoDB is healthy!")
            print(f"   Server Version: {health.get('server_version', 'Unknown')}")
            print(f"   Database: {health.get('database', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {health.get('message', 'Unknown error')}")
            return False
        
        # Test basic operations
        print("\n⏳ Testing database operations...")
        db = manager.get_database()
        
        # Create a test collection and insert a document
        test_collection = db.test_connection
        test_doc = {'test': 'Hello from LeadGenAgent!', 'timestamp': 'now'}
        insert_result = await test_collection.insert_one(test_doc)
        print(f"✅ Test write successful (ID: {insert_result.inserted_id})")
        
        # Read it back
        found_doc = await test_collection.find_one({'_id': insert_result.inserted_id})
        if found_doc:
            print(f"✅ Test read successful")
        
        # Clean up
        await test_collection.delete_one({'_id': insert_result.inserted_id})
        print(f"✅ Test cleanup successful")
        
        # Close connection
        await manager.close()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! MongoDB is ready to use!")
        print("\n📝 Next steps:")
        print("   1. Run full test suite: pytest tests/test_mongodb.py -v")
        print("   2. Continue with Phase 2 implementation")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n📝 Make sure dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print("   - Check MongoDB URI is correct")
        print("   - Verify network access (IP whitelist for Atlas)")
        print("   - Ensure MongoDB server is running (if local)")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mongodb_connection())
    exit(0 if success else 1)
