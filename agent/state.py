"""
state.py
State management with lead persistence and deduplication
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, TypedDict
from datetime import datetime

logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

LEADS_FILE = DATA_DIR / "leads.json"
STATE_FILE = DATA_DIR / "state.json"

class CompanyLead(TypedDict):
    """Single lead structure"""
    company_name: str
    homepage_url: str
    domain: str
    short_company_description: str
    extracted_emails: List[str]
    extracted_phone: Optional[str]
    linkedin_url: Optional[str]
    relevance_score: int  # 0-100
    fit_label: str  # high / medium / low
    short_reason_for_score: str
    source_urls: List[str]
    discovered_at: str  # ISO timestamp
    product_context: str  # What product was this lead generated for

class ICP(TypedDict):
    """Ideal Customer Profile"""
    industries: List[str]
    regions: List[str]
    company_size: str
    buyer_roles: List[str]
    pain_points: List[str]
    solution_summary: str

# ============= STATE PERSISTENCE =============

def load_leads() -> List[CompanyLead]:
    """Load all persisted leads from JSON"""
    if not LEADS_FILE.exists():
        return []
    try:
        with open(LEADS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load leads: {e}")
        return []

def save_leads(leads: List[CompanyLead]):
    """Persist leads to JSON"""
    try:
        with open(LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(leads)} leads to {LEADS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save leads: {e}")

def add_lead(lead: CompanyLead, product_description: str) -> bool:
    """
    Add lead with deduplication by domain.
    Returns True if added, False if duplicate.
    """
    existing_leads = load_leads()
    
    # Check for duplicate domain
    for existing in existing_leads:
        if existing['domain'].lower() == lead['domain'].lower():
            logger.info(f"Duplicate lead skipped: {lead['domain']}")
            return False
    
    # Add timestamp and product context
    lead['discovered_at'] = datetime.utcnow().isoformat()
    lead['product_context'] = product_description[:200]  # First 200 chars
    
    existing_leads.append(lead)
    save_leads(existing_leads)
    logger.info(f"Added new lead: {lead['company_name']} ({lead['domain']})")
    return True

def get_leads_by_product(product_description: str) -> List[CompanyLead]:
    """Filter leads by product context (fuzzy match)"""
    all_leads = load_leads()
    # Simple substring match - can enhance with embeddings later
    return [
        lead for lead in all_leads
        if product_description.lower()[:50] in lead.get('product_context', '').lower()
    ]

def clear_all_leads():
    """Clear all persisted leads (for testing)"""
    save_leads([])
    logger.warning("All leads cleared")

# ============= AGENT STATE =============

def load_agent_state() -> Dict:
    """Load agent state from JSON"""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load agent state: {e}")
        return {}

def save_agent_state(state: Dict):
    """Persist agent state to JSON"""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save agent state: {e}")
