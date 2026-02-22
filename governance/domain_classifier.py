# core/domain_classifier.py
import json
import os
from governance.embeddings import get_embedding, cosine_similarity
from governance.config import DOMAIN_THRESHOLD

DOMAIN_CORPUS_FILE = "schema/domain_corpus.json"

def _load_domain_corpus():
    """Loads domain corpus documents from external JSON file.
    Returns list of document strings, or empty list if file missing/invalid."""
    if not os.path.exists(DOMAIN_CORPUS_FILE):
        print(f"WARNING: {DOMAIN_CORPUS_FILE} not found. Domain guardrail will default to allow.")
        return []
    try:
        with open(DOMAIN_CORPUS_FILE, "r") as f:
            data = json.load(f)
            return data.get("documents", [])
    except Exception as e:
        print(f"WARNING: Failed to load domain corpus: {e}")
        return []

def _compute_centroid(documents):
    """Computes the average embedding (centroid) from a list of documents.
    Returns the centroid vector, or None if no documents provided."""
    if not documents:
        return None
    embeddings = []
    for doc in documents:
        vec = get_embedding(doc)
        if vec is not None:
            # Convert tensor to list if needed
            if hasattr(vec, 'tolist'):
                vec = vec.tolist()
            embeddings.append(vec)
    if not embeddings:
        return None
    # Compute element-wise average
    dim = len(embeddings[0])
    centroid = [0.0] * dim
    for vec in embeddings:
        for i in range(dim):
            centroid[i] += vec[i]
    for i in range(dim):
        centroid[i] /= len(embeddings)
    return centroid

# --- Precompute centroid at module import ---
_corpus_documents = _load_domain_corpus()
DOMAIN_CENTROID = _compute_centroid(_corpus_documents)

if DOMAIN_CENTROID is None:
    print("WARNING: Domain centroid not computed. Domain check will default to allow.")

def is_domain_aligned(prompt: str) -> tuple:
    """
    Checks if the prompt semantically aligns with allowed technical domains
    using centroid-based similarity.
    Returns: (bool, float) — (is_aligned, similarity_score)
    """
    # If centroid unavailable, default to allow (avoid system crash)
    if DOMAIN_CENTROID is None:
        return True, 1.0

    prompt_vec = get_embedding(prompt)
    if prompt_vec is None:
        return True, 1.0

    # Convert tensor to list if needed
    if hasattr(prompt_vec, 'tolist'):
        prompt_vec = prompt_vec.tolist()

    # Single comparison against precomputed centroid
    score = cosine_similarity(prompt_vec, DOMAIN_CENTROID)

    # If similarity is too low, it's off-topic
    return score >= DOMAIN_THRESHOLD, score