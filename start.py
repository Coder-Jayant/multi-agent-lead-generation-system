"""
Quick start script for Lead Generator AI Agent
Run this to start the FastAPI server
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check required configuration
from config.settings import print_config
print_config()

# Start FastAPI server
if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    print("\n🚀 Starting Lead Generator AI Agent...")
    print("📍 Access UI at: http://localhost:8000")
    print("📍 API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
