from sentence_transformers import SentenceTransformer

# Module-level cache for the embedding model (loaded once, reused)
_model = None


def get_embedding_model():
    """
    Load and return the sentence-transformer embedding model.
    The model is loaded once and reused across all subsequent calls.

    Returns:
        A SentenceTransformer model instance.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def create_embeddings(texts):
    """
    Generate normalized embeddings for a list of text strings.

    Args:
        texts: A list of text strings to embed.

    Returns:
        A list of embedding vectors (as lists of floats).
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def create_query_embedding(query):
    """
    Generate a normalized embedding for a single query string.

    Args:
        query: The query text to embed.

    Returns:
        An embedding vector (as a list of floats).
    """
    model = get_embedding_model()
    embedding = model.encode([query], normalize_embeddings=True)
    return embedding[0].tolist()
