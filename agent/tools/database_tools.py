"""
Agent Tools for MongoDB Database Operations
Tools that the ReAct agent can use to interact with the database
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from bson import ObjectId
from langchain_core.tools import tool

from db.mongodb import get_db_manager
from db.models import (
    Product, Lead, EmailDetail, LeadQualification,
    product_to_dict, lead_to_dict, dict_to_product, dict_to_lead
)

# Import POC enhancement tools
from agent.tools.persona_filter import filter_emails_by_persona
from agent.tools.lead_qualifier import qualify_lead

logger = logging.getLogger(__name__)


@tool
def save_lead_tool(
    domain: str,
    name: str,
    description: str,
    url: str,
    emails: Union[List[str], List[Dict[str, Any]]],  # Accept both formats!
    qualification: Optional[Dict[str, Any]] = None,
    email_source: str = "scraped",
    product_id: str = "default",
    product_name: Optional[str] = None  # NEW: Product name for better filtering
) -> Dict[str, Any]:
    """
    Tool for agent to save a lead to MongoDB (SYNCHRONOUS VERSION)
    
    Args:
        domain: Company domain
        name: Company name
        description: Company description
        url: Company website URL
        emails: List of emails (can be strings OR dicts with validation details)
        qualification: Optional qualification dict with {score, reasoning, fit}
        email_source: Source of emails ('scraped' or 'inferred')
        product_id: Product ID this lead is for (defaults to 'default')
        product_name: Product name for easier filtering
        
    Returns:
        Dict with status and lead_id
    """
    try:
        from pymongo import MongoClient
        import os
        
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGODB_URI")
        mongo_db = os.getenv("MONGODB_DATABASE", "leadgen")
        
        if not mongo_uri:
            return {'status': 'error', 'message': 'MongoDB not configured (no MONGODB_URI in .env)'}
        
        # Create SYNC MongoDB client
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        leads_collection = db.leads
        
        # Check for duplicate
        existing_lead = leads_collection.find_one({'domain': domain})
        if existing_lead:
            client.close()
            return {
                'status': 'duplicate',
                'message': f'Lead for domain {domain} already exists',
                'lead_id': str(existing_lead['_id'])
            }
        
        # Build lead document
        lead_doc = {
            'domain': domain,
            'name': name,
            'description': description,
            'url': url,
            'emails': emails,  # Simple list for backwards compatibility
            'email_source': email_source,
            'product_id': product_id,  # CRITICAL: Save product association
            'product_name': product_name,  # Save product name for easier filtering
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Add email validation details if provided (from enrichment)
        # emails parameter can be either List[str] or List[Dict]
        if emails and isinstance(emails[0], dict):
            # emails is actually email_details with full validation info
            lead_doc['email_details'] = emails
            lead_doc['emails'] = [e['email'] for e in emails]  # Extract simple list
        
        # Add qualification if provided
        if qualification:
            lead_doc['qualification'] = {
                'score': qualification.get('score', 0),
                'reasoning': qualification.get('reasoning', ''),
                'fit': qualification.get('fit', 'low'),
                'qualified_at': datetime.utcnow()
            }
        
        # Insert lead
        result = leads_collection.insert_one(lead_doc)
        client.close()
        
        logger.info(f"✅ Saved lead: {name} (domain: {domain}, score: {qualification.get('score') if qualification else 'N/A'})")
        
        return {
            'status': 'success',
            'message': f'Lead {name} saved successfully',
            'lead_id': str(result.inserted_id),
            'domain': domain
        }
        
    except Exception as e:
        logger.exception(f"Failed to save lead {domain}")
        return {'status': 'error', 'message': f'Failed to save lead: {str(e)}'}



async def check_duplicate_lead(product_id: str, domain: str) -> Dict[str, Any]:
    """
    Tool to check if a lead already exists for a product
    
    Args:
        product_id: Product ID
        domain: Company domain to check
        
    Returns:
        Dict with is_duplicate boolean and existing lead info if duplicate
    """
    try:
        manager = get_db_manager()
        if not manager.is_configured():
            return {
                'status': 'error',
                'message': 'MongoDB not configured'
            }
        
        db = manager.get_database()
        leads_collection = db.leads
        
        product_oid = ObjectId(product_id)
        
        existing_lead = await leads_collection.find_one({
            'product_id': product_oid,
            'domain': domain
        })
        
        if existing_lead:
            return {
                'is_duplicate': True,
                'lead_id': str(existing_lead['_id']),
                'name': existing_lead.get('name'),
                'domain': existing_lead.get('domain')
            }
        else:
            return {
                'is_duplicate': False
            }
            
    except Exception as e:
        logger.error(f"[CheckDuplicate] Error: {e}")
        return {
            'status': 'error',
            'message': f'Error checking duplicate: {str(e)}'
        }


async def get_existing_domains(product_id: str) -> List[str]:
    """
    Get list of all existing domains for a product
    Useful for the agent to avoid duplicates during search
    
    Args:
        product_id: Product ID
        
    Returns:
        List of existing domains
    """
    try:
        manager = get_db_manager()
        if not manager.is_configured():
            return []
        
        db = manager.get_database()
        leads_collection = db.leads
        
        product_oid = ObjectId(product_id)
        
        # Get all leads for this product, only return domains
        leads = await leads_collection.find(
            {'product_id': product_oid},
            {'domain': 1}
        ).to_list(length=None)
        
        domains = [lead['domain'] for lead in leads if 'domain' in lead]
        
        return domains
        
    except Exception as e:
        logger.error(f"[GetExistingDomains] Error: {e}")
        return []


async def create_product_tool(
    name: str,
    description: str,
    target_personas: Optional[List[str]] = None,
    industries: Optional[List[str]] = None,
    regions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Tool to create a new product
    
    Args:
        name: Product name
        description: Product description
        target_personas: List of target personas (e.g., ['C-Level', 'VP/Director'])
        industries: List of target industries
        regions: List of target regions
        
    Returns:
        Dict with status and product_id
    """
    try:
        manager = get_db_manager()
        if not manager.is_configured():
            return {
                'status': 'error',
                'message': 'MongoDB not configured'
            }
        
        db = manager.get_database()
        products_collection = db.products
        
        # Create product
        from db.models import ProductMetadata
        metadata = ProductMetadata(
            target_personas=target_personas or [],
            industries=industries or [],
            regions=regions or []
        )
        
        product = Product(
            name=name,
            description=description,
            metadata=metadata
        )
        
        # Insert to database
        product_dict = product_to_dict(product)
        result = await products_collection.insert_one(product_dict)
        
        logger.info(f"[CreateProduct] Created product: {name}, ID: {result.inserted_id}")
        
        return {
            'status': 'success',
            'message': f'Product "{name}" created successfully',
            'product_id': str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"[CreateProduct] Error: {e}")
        return {
            'status': 'error',
            'message': f'Failed to create product: {str(e)}'
        }


# Export tools for agent
__all__ = [
    'save_lead_tool',
    'check_duplicate_lead',
    'get_existing_domains',
    'create_product_tool'
]
