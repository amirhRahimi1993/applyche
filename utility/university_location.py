"""
Utility module for detecting country and city from university email domains
"""
import re
from typing import Optional, Tuple


# Mapping of university domain patterns to (country, city) tuples
# This is a basic mapping - can be extended with more universities
UNIVERSITY_LOCATION_MAP = {
    # Iran universities
    'ut.ac.ir': ('iran', 'tehran'),  # University of Tehran
    'ut.com': ('iran', 'tehran'),  # University of Tehran (alternative)
    'sharif.edu': ('iran', 'tehran'),  # Sharif University
    'iust.ac.ir': ('iran', 'tehran'),  # Iran University of Science and Technology
    'aut.ac.ir': ('iran', 'tehran'),  # Amirkabir University of Technology
    'um.ac.ir': ('iran', 'mashhad'),  # Ferdowsi University of Mashhad
    'shirazu.ac.ir': ('iran', 'shiraz'),  # Shiraz University
    'tabrizu.ac.ir': ('iran', 'tabriz'),  # University of Tabriz
    
    # US universities (examples)
    'mit.edu': ('usa', 'cambridge'),
    'harvard.edu': ('usa', 'cambridge'),
    'stanford.edu': ('usa', 'stanford'),
    'berkeley.edu': ('usa', 'berkeley'),
    'caltech.edu': ('usa', 'pasadena'),
    'cmu.edu': ('usa', 'pittsburgh'),
    'umich.edu': ('usa', 'ann arbor'),
    'uiuc.edu': ('usa', 'urbana-champaign'),
    'gatech.edu': ('usa', 'atlanta'),
    'nyu.edu': ('usa', 'new york'),
    'columbia.edu': ('usa', 'new york'),
    'princeton.edu': ('usa', 'princeton'),
    
    # UK universities
    'ox.ac.uk': ('uk', 'oxford'),
    'cam.ac.uk': ('uk', 'cambridge'),
    'imperial.ac.uk': ('uk', 'london'),
    'ucl.ac.uk': ('uk', 'london'),
    'ed.ac.uk': ('uk', 'edinburgh'),
    'manchester.ac.uk': ('uk', 'manchester'),
    
    # Canadian universities
    'utoronto.ca': ('canada', 'toronto'),
    'ubc.ca': ('canada', 'vancouver'),
    'mcgill.ca': ('canada', 'montreal'),
    'waterloo.ca': ('canada', 'waterloo'),
    
    # European universities
    'ethz.ch': ('switzerland', 'zurich'),
    'epfl.ch': ('switzerland', 'lausanne'),
    'tum.de': ('germany', 'munich'),
    'tu-berlin.de': ('germany', 'berlin'),
    'rwth-aachen.de': ('germany', 'aachen'),
    
    # Asian universities
    'nus.edu.sg': ('singapore', 'singapore'),
    'ntu.edu.sg': ('singapore', 'singapore'),
    'tsinghua.edu.cn': ('china', 'beijing'),
    'pku.edu.cn': ('china', 'beijing'),
    'ust.hk': ('hong kong', 'hong kong'),
    'u-tokyo.ac.jp': ('japan', 'tokyo'),
    'kaist.ac.kr': ('south korea', 'daejeon'),
}


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address string
        
    Returns:
        Domain string or None if invalid
    """
    if not email or not isinstance(email, str):
        return None
    
    email = email.strip().lower()
    
    # Basic email validation
    if '@' not in email:
        return None
    
    try:
        domain = email.split('@')[1]
        return domain
    except (IndexError, AttributeError):
        return None


def detect_university_location(email: str) -> Optional[Tuple[str, str]]:
    """
    Detect country and city from university email domain.
    
    Args:
        email: Professor email address
        
    Returns:
        Tuple of (country, city) or None if not found
    """
    domain = extract_domain_from_email(email)
    if not domain:
        return None
    
    # Direct lookup in mapping
    if domain in UNIVERSITY_LOCATION_MAP:
        return UNIVERSITY_LOCATION_MAP[domain]
    
    # Try to match patterns (e.g., *.edu, *.ac.uk, etc.)
    # Check for common patterns
    for pattern, location in UNIVERSITY_LOCATION_MAP.items():
        if domain.endswith('.' + pattern) or pattern in domain:
            return location
    
    # Try to infer from TLD
    tld_patterns = {
        '.ir': ('iran', 'unknown'),
        '.edu': ('usa', 'unknown'),
        '.ac.uk': ('uk', 'unknown'),
        '.ca': ('canada', 'unknown'),
        '.de': ('germany', 'unknown'),
        '.fr': ('france', 'unknown'),
        '.it': ('italy', 'unknown'),
        '.nl': ('netherlands', 'unknown'),
        '.se': ('sweden', 'unknown'),
        '.ch': ('switzerland', 'unknown'),
        '.au': ('australia', 'unknown'),
        '.jp': ('japan', 'unknown'),
        '.cn': ('china', 'unknown'),
        '.kr': ('south korea', 'unknown'),
        '.sg': ('singapore', 'unknown'),
        '.hk': ('hong kong', 'unknown'),
    }
    
    for tld, location in tld_patterns.items():
        if domain.endswith(tld):
            return location
    
    return None


def get_country_city_string(email: str) -> str:
    """
    Get country/city string in format "country/city" from email.
    
    Args:
        email: Professor email address
        
    Returns:
        String in format "country/city" or empty string if not found
    """
    location = detect_university_location(email)
    if location:
        country, city = location
        return f"{country}/{city}"
    return ""

