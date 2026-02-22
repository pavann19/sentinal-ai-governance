# core/cache.py
import json
import os
import math
import hashlib
from datetime import datetime, timezone
from governance.config import CACHE_SIMILARITY_THRESHOLD

CACHE_FILE = "semantic_cache.json"
CACHE_DATA = []

def load_cache():
    """Loads the cache from disk into memory on startup."""
    global CACHE_DATA
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                CACHE_DATA = json.load(f)
            print(f"🔹 Semantic Cache Loaded ({len(CACHE_DATA)} entries)")
        except Exception as e:
            print(f"⚠️ Cache Load Error: {e}")
            CACHE_DATA = []
    else:
        print("🔹 Semantic Cache Initialized (Empty)")

def save_cache_entry(prompt, vector, risk, score, source="unknown"):
    """Saves a new decision to the cache with metadata."""
    # Convert Tensor to list for JSON serialization
    if hasattr(vector, 'tolist'): vector = vector.tolist()
    
    entry = {
        "prompt": prompt,           # Store text for debugging
        "vector": vector,           # Store the math meaning
        "risk": risk,               # Store the final decision
        "score": score,             # Store the semantic score
        "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source            # Decision source for audit trail
    }
    CACHE_DATA.append(entry)
    
    # Save to disk so it remembers after restart
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(CACHE_DATA, f)
    except Exception as e:
        print(f"⚠️ Cache Save Error: {e}")

def cosine_similarity(vec1, vec2):
    """Calculates similarity between two vectors."""
    if vec1 is None or vec2 is None: return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0: return 0.0
    return dot_product / (norm_a * norm_b)

def lookup_cache(new_vector):
    """
    Checks if a similar prompt exists in history.
    Returns: (FoundRisk, FoundScore) or (None, None)
    """
    if hasattr(new_vector, 'tolist'): new_vector = new_vector.tolist()
    
    for entry in CACHE_DATA:
        cached_vector = entry.get("vector")
        score = cosine_similarity(new_vector, cached_vector)
        
        if score > CACHE_SIMILARITY_THRESHOLD:
            return entry.get("risk"), entry.get("score")
            
    return None, None

# Load immediately when imported
load_cache()

def flush_cache():
    """Clears the in-memory and on-disk cache."""
    global CACHE_DATA
    CACHE_DATA = []
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump([], f)
        print("🧹 Cache Flushed.")
    except Exception as e:
        print(f"⚠️ Cache Flush Error: {e}")
