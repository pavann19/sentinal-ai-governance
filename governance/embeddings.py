from sentence_transformers import SentenceTransformer, util

# Load the model locally
model = SentenceTransformer('all-mpnet-base-v2')

def get_embedding(text: str):
    """Generates a vector for the text."""
    # This must return a Tensor or List of floats, never None
    return model.encode(text, convert_to_tensor=True)

def cosine_similarity(vec1, vec2) -> float:
    """Calculates similarity."""
    return float(util.pytorch_cos_sim(vec1, vec2).item())