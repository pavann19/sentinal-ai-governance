# core/intent.py
from governance.policy_loader import get_suspicious_phrases

# Load from centralized policy loader
_SUSPICIOUS_PHRASES = get_suspicious_phrases()

def semantic_intent(prompt: str) -> str:
    """
    Classifies intent at high level.
    Returns: LOW, MEDIUM, HIGH
    """

    prompt = prompt.lower()

    for phrase in _SUSPICIOUS_PHRASES:
        if phrase in prompt:
            return "HIGH"

    # If asking for steps or instructions, increase caution
    if "how to" in prompt or "steps" in prompt:
        return "MEDIUM"

    return "LOW"

