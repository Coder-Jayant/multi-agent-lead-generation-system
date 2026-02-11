"""
Lead Qualifier - LLM-based lead scoring
Adds intelligent qualification to existing scoring
"""

import os
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
)


def qualify_lead(
    company_name: str,
    company_description: str,
    product_description: str
) -> Dict[str, Any]:
    """
    Use LLM to score and qualify a lead
    
    Args:
        company_name: Name of the company
        company_description: What the company does
        product_description: Your product/service description
    
    Returns:
        {
            'score': 0-100,
            'reasoning': 'Why this company is (or isn't) a good fit',
            'fit': 'high' | 'medium' | 'low'
        }
    """
    prompt = f"""You are a B2B sales qualification expert. Score this company as a potential customer.

**Product/Service:**
{product_description}

**Company Information:**
- Name: {company_name}
- Description: {company_description[:300]}

**Task:**
1. Score this company as a potential customer (0-100)
2. Explain WHY they would (or wouldn't) need this product

**Scoring Guidelines:**
- 80-100: Perfect fit, clear need
- 60-79: Good fit, likely to benefit
- 40-59: Medium fit, possible interest
- 0-39: Poor fit, unlikely customer

**Response Format (STRICT):**
Score: [number]
Reasoning: [2-3 sentences explaining the fit]"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse response
        score = 50  # Default
        reasoning = "Unable to determine fit."
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('Score:'):
                try:
                    score = int(line.replace('Score:', '').strip())
                    score = max(0, min(100, score))  # Clamp 0-100
                except:
                    pass
            elif line.startswith('Reasoning:'):
                reasoning = line.replace('Reasoning:', '').strip()
        
        # Determine fit level
        if score >= 80:
            fit = 'high'
        elif score >= 60:
            fit = 'medium'
        else:
            fit = 'low'
        
        return {
            'score': score,
            'reasoning': reasoning,
            'fit': fit
        }
        
    except Exception as e:
        logger.error(f"Lead qualification failed: {e}")
        return {
            'score': 50,
            'reasoning': f'Qualification failed: {str(e)[:50]}',
            'fit': 'medium'
        }


# Quick test function
if __name__ == "__main__":
    result = qualify_lead(
        company_name="Acme Corp",
        company_description="AI-powered customer service automation platform for enterprises",
        product_description="Voice AI chatbot for customer support"
    )
    print(f"Score: {result['score']}")
    print(f"Fit: {result['fit']}")
    print(f"Reasoning: {result['reasoning']}")
