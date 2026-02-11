"""
settings.py
Configuration management using environment variables
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# ============= REQUIRED SERVICES =============

SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "")
FIRECRAWL_BASE_URL = os.getenv("FIRECRAWL_BASE_URL", "")

if not SEARXNG_BASE_URL:
    print("WARNING: SEARXNG_BASE_URL not set. SearxNG search will fail.")
if not FIRECRAWL_BASE_URL:
    print("WARNING: FIRECRAWL_BASE_URL not set. Firecrawl enrichment will fail.")

# ============= LLM CONFIGURATION =============

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set. LLM calls will fail.")

# ============= AGENT CONFIGURATION =============

MAX_SEARCH_ITERATIONS = int(os.getenv("MAX_SEARCH_ITERATIONS", "5"))
TARGET_LEAD_COUNT = int(os.getenv("TARGET_LEAD_COUNT", "30"))
FIRECRAWL_TIMEOUT = int(os.getenv("FIRECRAWL_TIMEOUT", "30"))

# ============= LOGGING =============

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def print_config():
    """Print current configuration (for debugging)"""
    print("\n===== Lead Generator Configuration =====")
    print(f"SEARXNG_BASE_URL: {SEARXNG_BASE_URL or '❌ NOT SET'}")
    print(f"FIRECRAWL_BASE_URL: {FIRECRAWL_BASE_URL or '❌ NOT SET'}")
    print(f"OPENAI_BASE_URL: {OPENAI_BASE_URL}")
    print(f"OPENAI_MODEL: {OPENAI_MODEL}")
    print(f"MAX_SEARCH_ITERATIONS: {MAX_SEARCH_ITERATIONS}")
    print(f"TARGET_LEAD_COUNT: {TARGET_LEAD_COUNT}")
    print("========================================\n")
