"""
Persona Filter - Email role classification
Enhances existing email extraction with persona detection
"""

from typing import List, Dict, Optional

# Persona pattern definitions
PERSONA_PATTERNS = {
    "C-Level": [
        'ceo@', 'cto@', 'cfo@', 'cmo@', 'coo@', 'chief@', 
        'president@', 'executive@', 'exec@'
    ],
    "VP/Director": [
        'vp@', 'director@', 'head@', 'lead@', 'vice@'
    ],
    "IT Manager": [
        'manager@', 'mgr@', 'it@', 'tech@'
    ],
    "Founder": [
        'founder@', 'owner@', 'admin@'
    ]
}


def detect_persona(email: str) -> Optional[str]:
    """
    Detect persona from email address
    Returns persona label or None if generic
    """
    email_lower = email.lower()
    email_prefix = email_lower.split('@')[0] if '@' in email_lower else email_lower
    
    for persona, patterns in PERSONA_PATTERNS.items():
        for pattern in patterns:
            pattern_clean = pattern.rstrip('@')
            if pattern_clean in email_prefix or email_prefix == pattern_clean:
                return persona
    
    return None


def filter_emails_by_persona(
    emails: List[str], 
    target_personas: Optional[List[str]] = None
) -> List[Dict[str, any]]:
    """
    Filter emails by persona and add persona labels
    
    Args:
        emails: List of email addresses
        target_personas: List of desired personas (e.g., ["C-Level", "VP/Director"])
                        If None or empty, return all emails with detected personas
    
    Returns:
        List of dicts: [{'email': 'ceo@company.com', 'persona': 'C-Level', 'confidence': 95}, ...]
    """
    if not emails:
        return []
    
    # If no filtering requested, detect and label all
    if not target_personas:
        result = []
        for email in emails:
            persona = detect_persona(email)
            result.append({
                'email': email,
                'persona': persona,
                'confidence': 95 if persona else 70  # Higher confidence for pattern-matched
            })
        return result
    
    # STRICT FILTERING: Only return emails matching target personas
    filtered = []
    for email in emails:
        persona = detect_persona(email)
        if persona and persona in target_personas:
            filtered.append({
                'email': email,
                'persona': persona,
                'confidence': 95
            })
    
    return filtered


def get_persona_patterns() -> Dict[str, List[str]]:
    """Return all persona patterns for reference"""
    return PERSONA_PATTERNS.copy()
