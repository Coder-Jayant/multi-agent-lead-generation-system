"""
normalize_tool.py
Domain extraction and candidate normalization (deterministic logic)
"""

import json
import logging
from langchain_core.tools import tool
from urllib.parse import urlparse
import tldextract

logger = logging.getLogger(__name__)

@tool
def normalize_candidates(search_results_json: str) -> str:
    """
    Extract and deduplicate company domains from search results.
    Filters out blogs, job boards, news sites, and directories.
    Pure deterministic logic, no LLM.
    
    Args:
        search_results_json: List of search results as JSON string
    
    Returns: JSON array of unique valid domains
    """
    try:
        search_results = json.loads(search_results_json)
        
        if isinstance(search_results, dict) and "error" in search_results:
            logger.warning(f"Received error in search results: {search_results['error']}")
            return json.dumps([])
        
        if not isinstance(search_results, list):
            logger.error(f"Invalid search results format: expected list, got {type(search_results)}")
            return json.dumps([])
        
        seen_domains = set()
        valid_domains = []
        
        for result in search_results:
            if not isinstance(result, dict):
                continue
            
            url = result.get('url', '')
            if not url:
                continue
            
            # Filter invalid sources
            if is_invalid_source(url):
                logger.debug(f"Filtered invalid source: {url}")
                continue
            
            domain = extract_domain(url)
            
            if domain and domain not in seen_domains and len(domain) > 3:
                seen_domains.add(domain)
                valid_domains.append(domain)
        
        logger.info(f"Normalized {len(search_results)} results → {len(valid_domains)} unique valid domains")
        return json.dumps(valid_domains)
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse search results JSON: {e}")
        return json.dumps([])
    
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        return json.dumps([])


def extract_domain(url: str) -> str:
    """Extract clean domain (e.g., 'example.com') from URL"""
    try:
        parsed = tldextract.extract(url)
        if parsed.domain and parsed.suffix:
            domain = f"{parsed.domain}.{parsed.suffix}"
            # Filter out generic domains
            if parsed.domain.lower() in ['google', 'facebook', 'twitter', 'linkedin', 'youtube']:
                return ""
            return domain
        return ""
    except Exception as e:
        logger.debug(f"Domain extraction failed for {url}: {e}")
        return ""


def is_invalid_source(url: str) -> bool:
    """
    Filter out non-company pages (blogs, job boards, news, directories).
    Returns True if source should be filtered out.
    """
    url_lower = url.lower()
    
    invalid_patterns = [
        # Blogs & news
        'blog.', '/blog/', '/news/', '/press/',
        'medium.com', 'substack.com', 'wordpress.com', 'blogspot.com',
        'reuters.com', 'bloomberg.com', 'techcrunch.com', 'forbes.com',
        'venturebeat.com', 'theverge.com', 'wired.com',
        
        # Job boards
        'indeed.com', 'glassdoor.com', 'monster.com', 'ziprecruiter.com',
        'linkedin.com/jobs', '/careers', '/job',
        
        # Directories & aggregators
        'crunchbase.com', 'yellowpages', 'yelp.com', 'trustpilot.com',
        'g2.com/products/', 'capterra.com', 'softwareadvice.com',
        
        # Social media profiles (not company pages)
        'linkedin.com/in/', 'twitter.com', 'facebook.com/people',
        'instagram.com', 'tiktok.com',
        
        # Forums & Q&A
        'reddit.com', 'quora.com', 'stackoverflow.com',
        
        # Generic & government
        'wikipedia.org', 'gov', 'edu',
        
        # PDFs and documents
        '.pdf', '.doc', '.ppt'
    ]
    
    return any(pattern in url_lower for pattern in invalid_patterns)
