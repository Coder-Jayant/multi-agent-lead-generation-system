"""
firecrawl_tool.py
Self-hosted Firecrawl enrichment wrapper (deterministic HTTP tool)
"""

import requests
import json
import logging
from langchain_core.tools import tool
import os

logger = logging.getLogger(__name__)

FIRECRAWL_BASE_URL = os.getenv("FIRECRAWL_BASE_URL", "")

@tool
def firecrawl_enrich(domain: str) -> str:
    """
    Enrich company data using Firecrawl v2 API (scrape endpoint).
    Extracts company information from website content.
    
    Args:
        domain: Company domain (e.g., "example.com")
    
    Returns: JSON string with extracted company data (company_name, description, email, phone, linkedin_url, domain, homepage_url)
    """
    if not FIRECRAWL_BASE_URL:
        error_msg = "FIRECRAWL_BASE_URL not configured. Please set environment variable."
        logger.error(error_msg)
        return json.dumps({
            "domain": domain,
            "error": error_msg
        })
    
    url = f"https://{domain}" if not domain.startswith('http') else domain
    
    try:
        logger.info(f"Enriching domain via Firecrawl v2: {domain}")
        
        # Firecrawl v2 API format
        response = requests.post(
            f"{FIRECRAWL_BASE_URL}/v2/scrape",
            json={"url": url},
            timeout=45
        )
        
        if response.status_code != 200:
            error_msg = f"Firecrawl HTTP {response.status_code} for {domain}"
            logger.warning(error_msg)
            return json.dumps({
                "domain": domain,
                "homepage_url": url,
                "company_name": domain.split('.')[0].title(),
                "description": "",
                "email": None,
                "phone": None,
                "linkedin_url": None,
                "error": error_msg
            })
        
        data = response.json()
        
        # v2 returns: {'success': True, 'data': {'markdown': '...', 'html': '...', 'metadata': {...}}}
        if not data.get('success'):
            raise ValueError(f"Firecrawl returned success=false: {data}")
        
        scrape_data = data.get('data', {})
        markdown_content = scrape_data.get('markdown', '')
        metadata = scrape_data.get('metadata', {})
       
        # Extract information from markdown and metadata
        extracted = {
            'domain': domain,
            'homepage_url': url,
            'company_name': extract_company_name(markdown_content, metadata, domain),
            'description': extract_description(markdown_content, metadata),
            'phone': extract_phone(markdown_content),
            'linkedin_url': extract_linkedin(markdown_content)
        }
        
        # Enhanced email extraction with validation
        emails_data = extract_and_validate_emails(markdown_content, domain)
        extracted['emails'] = [e['email'] for e in emails_data]  # Simple list for backwards compat
        extracted['email_details'] = emails_data  # Full validation details
        extracted['email_source'] = 'scraped' if any(e.get('scraped') for e in emails_data) else 'generated'
        
        # Legacy single email field
        extracted['email'] = extracted['emails'][0] if extracted['emails'] else None
        
        logger.info(f"Enriched {domain} → {extracted.get('company_name', 'Unknown')}, {len(extracted['emails'])} emails")
        return json.dumps(extracted, indent=2)
    
    except requests.exceptions.Timeout:
        error_msg = f"Firecrawl timeout for {domain}"
        logger.warning(error_msg)
        return json.dumps({
            "domain": domain,
            "homepage_url": url,
            "company_name": domain.split('.')[0].title(),
            "description": "",
            "email": None,
            "phone": None,
            "linkedin_url": None,
            "error": error_msg
        })
    
    except Exception as e:
        error_msg = f"Firecrawl enrichment failed for {domain}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "domain": domain,
            "homepage_url": url,
            "company_name": domain.split('.')[0].title(),
            "description": "",
            "email": None,
            "phone": None,
            "linkedin_url": None,
            "error": error_msg
        })


# Helper functions to extract data from markdown content

def extract_company_name(markdown: str, metadata: dict, domain: str) -> str:
    """Extract company name from content"""
    # Try metadata title first
    if metadata.get('title'):
        title = metadata['title']
        # Clean common suffixes
        for suffix in [' | ', ' - ', ' – ']:
            if suffix in title:
                return title.split(suffix)[0].strip()
        return title
    
    # Try first heading in markdown
    lines = markdown.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if line.startswith('# ') or line.startswith('## '):
            return line.lstrip('#').strip()
    
    # Fallback to domain
    return domain.split('.')[0].title()


def extract_description(markdown: str, metadata: dict) -> str:
    """Extract company description"""
    # Try metadata description
    if metadata.get('description'):
        desc = metadata['description']
        if len(desc) > 200:
            desc = desc[:197] + '...'
        return desc
    
    # Try first paragraph from markdown
    lines = markdown.split('\n')
    paragraphs = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('!') and not line.startswith('['):
            if len(line) > 20:  # Meaningful paragraph
                paragraphs.append(line)
                break
    
    if paragraphs:
        desc = paragraphs[0]
        if len(desc) > 200:
            desc = desc[:197] + '...'
        return desc
    
    return ""


def extract_and_validate_emails(markdown: str, domain: str) -> list:
    """
    Extract emails from markdown, generate common patterns if none found,
    and validate all emails with confidence scores
    
    Returns list of dicts with: email, confidence, status, has_mx, smtp_valid, scraped
    """
    from .email_validation import extract_emails_from_text, generate_common_email_patterns, quick_validate_emails
    
    # Try to extract emails from scraped content
    scraped_emails = extract_emails_from_text(markdown)
    
    all_emails = []
    
    if scraped_emails:
        # Mark scraped emails
        all_emails = scraped_emails
        email_source = 'scraped'
    else:
        # No emails found - generate common patterns
        logger.info(f"No emails found in content for {domain}, generating common patterns")
        common_patterns = generate_common_email_patterns(domain)
        all_emails = common_patterns[:5]  # Max 5 patterns
        email_source = 'generated'
    
    # Validate all emails (DNS only by default, SMTP is slow)
    # To enable SMTP validation, set verify_smtp=True
    validated = quick_validate_emails(all_emails, verify_smtp=False)
    
    # Mark which were scraped vs generated
    for email_data in validated:
        email_data['scraped'] = (email_source == 'scraped')
    
    return validated


def extract_email(markdown: str) -> str:
    """Legacy function - extract single email address from markdown"""
    from .email_validation import extract_emails_from_text
    emails = extract_emails_from_text(markdown)
    return emails[0] if emails else None


def extract_phone(markdown: str) -> str:
    """Extract phone number from markdown"""
    import re
    # Match various phone formats
    phone_patterns = [
        r'\+\d{1,3}[-\s]?\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}',  # +91-1234-567-890
        r'\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}',  # (123) 456-7890
        r'\d{3}[-\s]?\d{3}[-\s]?\d{4}'  # 123-456-7890
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, markdown)
        if matches:
            return matches[0]
    
    return None


def extract_linkedin(markdown: str) -> str:
    """Extract LinkedIn URL from markdown"""
    import re
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/company/[A-Za-z0-9_-]+'
    matches = re.findall(linkedin_pattern, markdown)
    return matches[0] if matches else None
