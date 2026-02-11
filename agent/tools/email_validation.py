"""
Email Validation Utilities
Provides DNS MX validation and optional SMTP verification with confidence scoring
"""

import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)


def validate_email_dns(email: str) -> bool:
    """
    Check if email domain has valid MX records (free, instant)
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if domain has MX records, False otherwise
    """
    try:
        import dns.resolver
        domain = email.split('@')[1]
        
        # Check MX records
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except Exception as e:
        logger.debug(f"DNS validation failed for {email}: {e}")
        return False


def validate_email_smtp(email: str, timeout: int = 5) -> Dict[str, any]:
    """
    Verify email exists via SMTP (free but can be slow/blocked)
    
    Args:
        email: Email address to validate
        timeout: Connection timeout in seconds
        
    Returns:
        Dict with 'valid' (bool or None) and 'reason' (str)
    """
    import smtplib
    import socket
    
    try:
        domain = email.split('@')[1]
        
        # Get MX record
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange).rstrip('.')
        
        # Connect to SMTP server
        server = smtplib.SMTP(timeout=timeout)
        server.connect(mx_host)
        server.helo('verification.test')
        server.mail('verify@test.com')
        code, message = server.rcpt(email)
        server.quit()
        
        # 250 = email exists, 550 = doesn't exist
        if code == 250:
            return {'valid': True, 'reason': 'SMTP verified'}
        else:
            return {'valid': False, 'reason': f'SMTP code {code}'}
    except socket.timeout:
        return {'valid': None, 'reason': 'Timeout (server slow)'}
    except Exception as e:
        return {'valid': None, 'reason': f'Cannot verify: {str(e)[:30]}'}


def quick_validate_emails(emails: List[str], verify_smtp: bool = False) -> List[Dict]:
    """
    Quickly validate emails using DNS MX (fast) and optionally SMTP (slow)
    
    Args:
        emails: List of email addresses to validate
        verify_smtp: If True, do full SMTP verification (slower but more accurate)
        
    Returns:
        List of dicts with email, confidence, status, has_mx, smtp_valid
        
    Confidence Scores:
        95: SMTP verified (mailbox confirmed exists)
        70: DNS validated + common pattern (sales@, info@, contact@)
        60: DNS validated only
        0: No MX records (invalid)
    """
    validated = []
    
    # Common business email patterns
    common_patterns = ['sales', 'info', 'contact', 'hello', 'support', 'business', 'inquiry']
    
    for email in emails:
        result = {
            'email': email,
            'has_mx': False,
            'smtp_valid': None,
            'confidence': 0,
            'status': 'unknown'
        }
        
        # Step 1: DNS MX check (fast, always done)
        result['has_mx'] = validate_email_dns(email)
        
        if not result['has_mx']:
            result['status'] = 'invalid'
            result['confidence'] = 0
        else:
            # Step 2: Check if common pattern
            email_prefix = email.split('@')[0].lower()
            is_common_pattern = email_prefix in common_patterns
            
            # Step 3: SMTP verification decision
            if verify_smtp:
                # Do full SMTP verification
                smtp_result = validate_email_smtp(email, timeout=3)
                result['smtp_valid'] = smtp_result['valid']
                
                if smtp_result['valid'] == True:
                    result['status'] = 'verified'
                    result['confidence'] = 95
                elif smtp_result['valid'] == False:
                    result['status'] = 'invalid'
                    result['confidence'] = 0
                else:
                    # Could not verify via SMTP, but MX exists
                    result['status'] = 'likely'
                    result['confidence'] = 60
            else:
                # Skip SMTP, use pattern-based confidence
                if is_common_pattern:
                    result['status'] = 'likely'
                    result['confidence'] = 70
                else:
                    result['status'] = 'likely'
                    result['confidence'] = 60
        
        # Only add if confidence > 0 (has valid MX records)
        if result['confidence'] > 0:
            validated.append(result)
    
    return validated


def generate_common_email_patterns(domain: str, common_names: Optional[List[str]] = None) -> List[str]:
    """
    Generate common business email patterns for a domain
    
    Args:
        domain: Company domain (e.g., "company.com")
        common_names: Optional list of common first names to try (e.g., ["john", "sarah"])
        
    Returns:
        List of generated email addresses
    """
    patterns = []
    
    # Standard business patterns
    standard = ['sales', 'info', 'contact', 'hello', 'support', 'business', 'inquiry', 'team']
    for prefix in standard:
        patterns.append(f'{prefix}@{domain}')
    
    # If common names provided, generate firstname@ patterns
    if common_names:
        for name in common_names[:3]:  # Max 3 names
            patterns.append(f'{name.lower()}@{domain}')
    
    return patterns


def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract email addresses from text using regex
    
    Args:
        text: Text content to search for emails
        
    Returns:
        List of unique email addresses found
    """
    if not text:
        return []
    
    # Email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Filter out noise
    filtered = []
    for email in emails:
        # Skip common placeholders and noise
        if any(skip in email.lower() for skip in [
            'example.com', 'test.', 'sample.', 'noreply', 'no-reply',
            'donotreply', 'mailer-daemon', '.png', '.jpg', '.gif'
        ]):
            continue
        filtered.append(email)
    
    # Remove duplicates, keep order
    seen = set()
    unique = []
    for email in filtered:
        if email.lower() not in seen:
            seen.add(email.lower())
            unique.append(email)
    
    return unique[:5]  # Max 5 emails
