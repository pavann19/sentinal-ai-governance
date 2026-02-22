# core/threat_centroid.py
# Centroid-based malicious intent detection.
# Computes a single centroid vector from threat anchors at import time
# for efficient per-prompt similarity scoring.

import json
import os
from governance.embeddings import get_embedding, cosine_similarity


POLICY_FILE = "policies.json"


def load_threat_anchors():
    """Load threat anchor strings from policies.json."""
    if not os.path.exists(POLICY_FILE):
        print(f"WARNING: {POLICY_FILE} not found. Threat centroid disabled.")
        return []
    try:
        with open(POLICY_FILE, "r") as f:
            data = json.load(f)
            anchors = data.get("threat_anchors", [])
            print(f"Loaded {len(anchors)} threat anchors for centroid computation.")
            return anchors
    except Exception as e:
        print(f"WARNING: Failed to load threat anchors: {e}")
        return []


def build_malicious_centroid(anchors):
    """
    Compute the centroid (element-wise average) of all threat anchor embeddings.
    Returns the centroid vector, or None if no valid embeddings.
    """
    if not anchors:
        return None

    vectors = []
    for anchor in anchors:
        vec = get_embedding(anchor)
        if vec is not None:
            # Ensure plain list
            if hasattr(vec, "tolist"):
                vec = vec.tolist()
            vectors.append(vec)

    if not vectors:
        return None

    # Element-wise average
    dim = len(vectors[0])
    centroid = [0.0] * dim
    for vec in vectors:
        for i in range(dim):
            centroid[i] += vec[i]
    for i in range(dim):
        centroid[i] /= len(vectors)

    print(f"Malicious centroid built from {len(vectors)} vectors (dim={dim}).")
    return centroid


def compute_centroid_similarity(prompt_vec):
    """
    Compute cosine similarity between prompt and the malicious centroid.
    Returns 0.0 if centroid is unavailable.
    """
    if MALICIOUS_CENTROID is None:
        return 0.0
    if prompt_vec is None:
        return 0.0
    # Ensure plain list
    pv = prompt_vec.tolist() if hasattr(prompt_vec, "tolist") else prompt_vec
    return cosine_similarity(pv, MALICIOUS_CENTROID)


# --- MODULE-LEVEL PRECOMPUTATION (runs once at import) ---
_threat_anchors = load_threat_anchors()
MALICIOUS_CENTROID = build_malicious_centroid(_threat_anchors)
