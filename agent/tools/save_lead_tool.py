"""
save_lead_tool.py
Tool for saving scored companies as leads to MongoDB via API
"""

import json
import logging
import requests
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# API endpoint for saving leads to MongoDB
LEAD_API_URL = "http://localhost:8001/api/mongodb/leads"


@tool
def save_lead(
    company_data_json: str,
    score_data_json: str,
    product_description: str
) -> str:
    """
    Save a scored company as a lead to MongoDB via REST API.
    MUST be called after score_company to persist the lead.
    
    Args:
        company_data_json: JSON string from firecrawl_enrich (company data)
        score_data_json: JSON string from score_company (score and reasoning)
        product_description: Original product description for context
    
    Returns: JSON string with save status (success/duplicate/error)
    """
    try:
        company_data = json.loads(company_data_json)
        score_data = json.loads(score_data_json)
        
        # Prepare lead payload for MongoDB API
        lead_payload = {
            "domain": company_data.get('domain', ''),
            "name": company_data.get('company_name', 'Unknown'),
            "description": company_data.get('description', '') or '',
            "url": company_data.get('homepage_url', ''),
            "emails": [],
            "phones": [company_data.get('phone')] if company_data.get('phone') else [],
            "linkedin_url": company_data.get('linkedin_url'),
            "qualification": {
                "score": score_data.get('relevance_score', 0),
                "reasoning": score_data.get('short_reason', ''),
                "fit": score_data.get('fit_label', 'low'),
                "qualified_at": None  # API will set timestamp
            },
            "product_context": product_description
        }
        
        # Call MongoDB API to save lead
        response = requests.post(
            LEAD_API_URL,
            json=lead_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                logger.info(f"✅ Saved lead to MongoDB: {lead_payload['name']} (score: {score_data.get('relevance_score')})")
                return json.dumps({
                    "status": "saved",
                    "message": f"Lead saved successfully: {lead_payload['name']}",
                    "domain": lead_payload['domain'],
                    "score": score_data.get('relevance_score', 0),
                    "lead_id": result.get('lead_id')
                })
            elif result.get('status') == 'duplicate':
                logger.info(f"⚠️ Duplicate lead skipped: {lead_payload['domain']}")
                return json.dumps({
                    "status": "duplicate",
                    "message": f"Lead already exists: {lead_payload['domain']}",
                    "domain": lead_payload['domain']
                })
        
        # Handle error responses
        error_msg = f"API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to save lead (API unreachable): {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    
    except Exception as e:
        error_msg = f"Failed to save lead: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
