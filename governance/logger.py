# core/logger.py
import json
import hashlib
from datetime import datetime

# Changed argument name from 'user_role' to 'capability'
def log_event(capability, prompt, risk, decision, metadata=None):
    if metadata is None: metadata = {}
    
    timestamp = datetime.now().isoformat()
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    log_entry = {
        "timestamp": timestamp,
        "capability": capability,   # <--- RENAMED FIELD
        "risk": risk,
        "decision": decision,
        "prompt_hash": prompt_hash,
        "semantic_score": metadata.get("semantic_score", 0.0),
        "source": metadata.get("source", "unknown"),
        "educational_context": metadata.get("educational_context", False),
        "domain_score": metadata.get("domain_score", None),
        "symbolic_triggered": metadata.get("symbolic_triggered", False),
        "judge_invoked": metadata.get("judge_invoked", False),
        "dynamic_threat_score": metadata.get("dynamic_threat_score", None)
    }

    with open("audit.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")