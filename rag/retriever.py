from rag.embeddings import create_query_embedding
from rag.vector_store import search_chunks


def retrieve_context(question, top_k=5):
    """
    Retrieve the most relevant chunks from ChromaDB for a given question.

    Args:
        question: The user's question string.
        top_k: Number of top results to retrieve.

    Returns:
        A tuple of (context_string, sources_list).
        - context_string: Formatted text with source info and chunk content.
        - sources_list: List of dicts with 'source' and 'page' keys.
    """
    # Convert question to embedding
    query_embedding = create_query_embedding(question)

    # Search ChromaDB for similar chunks
    results = search_chunks(query_embedding, top_k=top_k)

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not documents:
        return "", []

    # Build the context string with source references
    context_parts = []
    sources = []
    seen_sources = set()

    for doc, meta in zip(documents, metadatas):
        source = meta.get("source", "Unknown")
        page = meta.get("page", "N/A")

        context_parts.append(
            f"Source: {source}\nPage: {page}\n\n{doc}"
        )

        # Track unique sources for the response
        source_key = f"{source}_page{page}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append({
                "source": source,
                "page": page
            })

    context = "\n\n---\n\n".join(context_parts)
    return context, sources
