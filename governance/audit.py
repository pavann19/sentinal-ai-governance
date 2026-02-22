# core/audit.py
import json
import hashlib
from datetime import datetime

def log_interaction(prompt, decision, risk, metadata, latency=0.0):
    """
    Logs a system interaction to the audit trail.
    
    Args:
        prompt (str): The user query (sanitized).
        decision (str): ALLOW, BLOCK, or RESTRICT.
        risk (str): HIGH, MEDIUM, LOW.
        metadata (dict): Additional context (score, source, etc).
        latency (float): Processing time in milliseconds.
    """
    timestamp = datetime.now().isoformat()
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    log_entry = {
        "timestamp": timestamp,
        "prompt_hash": prompt_hash,
        "risk": risk,
        "decision": decision,
        "latency_ms": round(latency, 2),
        "source": metadata.get("source", "unknown"),
        "semantic_score": metadata.get("semantic_score", 0.0),
        "metadata": metadata
    }

    try:
        with open("audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"⚠️ Audit Log Error: {e}")
