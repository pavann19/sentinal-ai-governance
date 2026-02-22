# core/auth.py
import os
# We import the constants so we don't have typos
from governance.config import CAPABILITY_GENERAL, CAPABILITY_ELEVATED, CAPABILITY_INTERNAL

def get_capability(token=None):
    """
    Determines system capability based on the POSSESSION of a valid token.
    Default is GENERAL (Zero Trust).
    """
    # If no token passed, try getting from environment
    if not token:
        token = os.environ.get("CAPABILITY_TOKEN", "")

    # 1. Internal / Admin Tier
    if token == "ADM-112233-SUPER-USER":
        return CAPABILITY_INTERNAL
    
    # 2. Elevated / Researcher Tier
    if token == "RES-998877-SECRET-ACCESS":
        return CAPABILITY_ELEVATED

    # 3. Default Tier (The "Public" User)
    return CAPABILITY_GENERAL