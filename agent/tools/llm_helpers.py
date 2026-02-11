"""
llm_helpers.py
Simple LLM helper functions (NOT ReAct agents - just one-shot LLM calls)
Registered as tools for the controller to use
"""

import json
import logging
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# LLM instance for helper functions
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
    temperature=0.3,
    max_tokens=2000
)

@tool
def extract_icp(product_description: str) -> str:
    """
    Extract Ideal Customer Profile from product description.
    Simple one-shot LLM call, no tool loop.
    
    Returns: JSON string with ICP fields (industries, regions, company_size, buyer_roles, pain_points, solution_summary)
    """
    prompt = f"""Extract the Ideal Customer Profile (ICP) from this product description.

Product: {product_description}

Identify:
- Target industries (list of strings, e.g., ["Software", "E-commerce"])
- Geographic regions (list of strings, e.g., ["North America", "Europe"])
- Company size (one of: "startup", "SMB", "mid-market", "enterprise")
- Buyer personas/roles (list of strings, e.g., ["CTO", "VP Engineering"])
- Pain points this solves (list of strings)
- Solution summary (2-3 sentences describing what this product does)

Return ONLY valid JSON in this exact format:
{{
  "industries": ["Software", "E-commerce"],
  "regions": ["North America", "Europe"],
  "company_size": "SMB",
  "buyer_roles": ["CTO", "VP Engineering"],
  "pain_points": ["High customer churn", "Poor user onboarding"],
  "solution_summary": "Brief description of what the product does and how it helps."
}}

Do NOT include any markdown formatting or code blocks. Return ONLY the JSON object."""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result [4:]
            result = result.strip()
        
        # Validate JSON
        parsed = json.loads(result)
        
        logger.info(f"ICP extracted: industries={parsed.get('industries', [])}")
        return result
    
    except Exception as e:
        logger.error(f"ICP extraction failed: {e}")
        # Return minimal fallback ICP
        fallback = {
            "industries": ["Technology"],
            "regions": ["Global"],
            "company_size": "SMB",
            "buyer_roles": ["Business Owner"],
            "pain_points": ["Operational efficiency"],
            "solution_summary": product_description[:200]
        }
        return json.dumps(fallback)


@tool
def generate_search_queries(icp_json: str, current_lead_count: int, target_count: int) -> str:
    """
    Generate targeted search queries based on ICP and current progress.
    Simple one-shot LLM call, no tool loop.
    
    Args:
        icp_json: ICP as JSON string
        current_lead_count: How many quality leads found so far
        target_count: Target number of leads
    
    Returns: JSON array of search query strings
    """
    try:
        icp = json.loads(icp_json)
    except:
        icp = {}
    
    remaining = max(1, target_count - current_lead_count)
    num_queries = min(6, remaining + 2)  # Generate 2 extra queries to ensure coverage
    
    prompt = f"""Generate {num_queries} diverse web search queries to find companies matching this Ideal Customer Profile:

**ICP:**
- Industries: {icp.get('industries', [])}
- Regions: {icp.get('regions', [])}
- Company Size: {icp.get('company_size', '')}
- Buyer Roles: {icp.get('buyer_roles', [])}
- Pain Points: {icp.get('pain_points', [])}

**Current Progress:** {current_lead_count}/{target_count} quality leads found (need {remaining} more)

**Query Strategy:**
- Target company directories and listings
- Search for industry-specific associations and member lists
- Look for review sites (G2, Capterra, TrustRadius) with relevant companies
- Find technology stack databases (BuiltWith, StackShare)
- Search for companies using location + industry keywords

**Requirements:**
- Queries should be specific enough to find relevant companies
- Vary query structure for better coverage
- Include industry terms and location when relevant
- Avoid overly broad queries

Return ONLY a JSON array of query strings:
["specific query 1", "specific query 2", "specific query 3", ...]

Do NOT include any markdown formatting. Return ONLY the JSON array."""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        
        # Validate JSON array
        queries = json.loads(result)
        if not isinstance(queries, list):
            raise ValueError("Result is not a list")
        
        logger.info(f"Generated {len(queries)} search queries")
        return result
    
    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        # Fallback queries
        fallback_queries = [
            f"{' '.join(icp.get('industries', ['business'])[:2])} companies {' '.join(icp.get('regions', [''])[:1])}",
            f"top {icp.get('company_size', 'SMB')} companies in {' '.join(icp.get('industries', ['technology'])[:1])}"
        ]
        return json.dumps(fallback_queries)


@tool
def score_company(company_data_json: str, icp_json: str) -> str:
    """
    Score a single company against the ICP.
    Simple one-shot LLM call, no tool loop.
    
    Args:
        company_data_json: Company info from Firecrawl (JSON string)
        icp_json: ICP criteria (JSON string)
    
    Returns: JSON with relevance_score (0-100), fit_label (high/medium/low), short_reason
    """
    try:
        company_data = json.loads(company_data_json)
        icp = json.loads(icp_json)
    except Exception as e:
        logger.error(f"Failed to parse inputs for scoring: {e}")
        return json.dumps({
            "relevance_score": 0,
            "fit_label": "low",
            "short_reason": "Invalid data format"
        })
    
    prompt = f"""Score this company against the Ideal Customer Profile on a scale of 0-100.

**ICP (Ideal Customer Profile):**
- Target Industries: {icp.get('industries', [])}
- Company Size Preference: {icp.get('company_size', '')}
- Pain Points to Address: {icp.get('pain_points', [])}
- Solution: {icp.get('solution_summary', '')}

**Company to Evaluate:**
- Name: {company_data.get('company_name', 'Unknown')}
- Description: {company_data.get('description', 'No description available')}
- Domain: {company_data.get('domain', '')}
- Homepage: {company_data.get('homepage_url', '')}

**Scoring Criteria:**
1. Industry Match (0-30 points): Does the company operate in target industries?
2. Company Size Fit (0-20 points): Does size match preference?
3. Pain Point Relevance (0-30 points): Do they likely experience the pain points?
4. Buying Signals (0-20 points): Evidence they might be interested (tech stack, growth, etc.)

**Instructions:**
- Assign a total relevance_score from 0-100
- Determine fit_label: "high" (65-100), "medium" (40-64), "low" (0-39)
- Provide short_reason (max 150 characters) explaining the score

Return ONLY valid JSON:
{{
  "relevance_score": 75,
  "fit_label": "high",
  "short_reason": "Strong industry match and relevant pain points"
}}

Do NOT include any markdown formatting. Return ONLY the JSON object."""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        
        # Validate JSON
        score_data = json.loads(result)
        
        # Ensure required fields exist
        required = ['relevance_score', 'fit_label', 'short_reason']
        if not all(k in score_data for k in required):
            raise ValueError("Missing required fields in score result")
        
        # Validate fit_label
        if score_data['fit_label'] not in ['high', 'medium', 'low']:
            score = score_data['relevance_score']
            if score >= 65:
                score_data['fit_label'] = 'high'
            elif score >= 40:
                score_data['fit_label'] = 'medium'
            else:
                score_data['fit_label'] = 'low'
        
        logger.info(f"Scored {company_data.get('company_name', 'Unknown')}: {score_data['relevance_score']}/100 ({score_data['fit_label']})")
        return json.dumps(score_data)
    
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        return json.dumps({
            "relevance_score": 25,
            "fit_label": "low",
            "short_reason": f"Scoring error: {str(e)[:100]}"
        })
