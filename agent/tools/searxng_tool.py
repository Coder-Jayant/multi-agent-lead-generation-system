"""
searxng_tool.py
Self-hosted SearxNG search wrapper (deterministic HTTP tool)
"""

import requests
import json
import logging
from langchain_core.tools import tool
import os

logger = logging.getLogger(__name__)

SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "")

@tool
def searxng_search(query: str, num_results: int = 10) -> str:
    """
    Search using self-hosted SearxNG instance.
    Pure HTTP tool, no LLM involved.
    
    Args:
        query: Search query string
        num_results: Maximum number of results to return (default: 10)
    
    Returns: JSON string with list of {url, title, snippet}
    """
    if not SEARXNG_BASE_URL:
        error_msg = "SEARXNG_BASE_URL not configured. Please set environment variable."
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
    
    try:
        logger.info(f"Searching SearxNG: '{query}' (max {num_results} results)")
        
        response = requests.get(
            f"{SEARXNG_BASE_URL}/search",
            params={
                "q": query,
                "format": "json",
                "pageno": 1,
                "safesearch": 0,
                "language": "en"
            },
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get("results", [])[:num_results]:
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": item.get("content", "")
            })
        
        logger.info(f"SearxNG returned {len(results)} results for query: '{query}'")
        return json.dumps(results, indent=2)
    
    except requests.exceptions.Timeout:
        error_msg = f"SearxNG search timed out for query: {query}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
    
    except requests.exceptions.RequestException as e:
        error_msg = f"SearxNG request failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
    
    except Exception as e:
        error_msg = f"Unexpected error in SearxNG search: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
