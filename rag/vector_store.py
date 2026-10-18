import os
import hashlib
import chromadb
from rag.embeddings import create_embeddings

# Path for persistent ChromaDB storage
CHROMA_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db"
)
COLLECTION_NAME = "pdf_documents"

# Module-level ChromaDB client and collection (initialized once)
_client = None
_collection = None


def _get_collection():
    """
    Get or create the ChromaDB collection.
    Uses a persistent client so data survives server restarts.
    """
    global _client, _collection
    if _collection is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_chunks(chunks, document_name):
    """
    Add text chunks with embeddings and metadata to ChromaDB.

    Args:
        chunks: List of dicts with 'text' and 'page' keys.
        document_name: The source PDF filename.
    """
    collection = _get_collection()

    texts = [chunk["text"] for chunk in chunks]
    embeddings = create_embeddings(texts)

    # Generate stable unique IDs based on document name, page, and chunk index
    ids = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        raw_id = f"{document_name}_page{chunk['page']}_chunk{i}"
        chunk_id = hashlib.md5(raw_id.encode()).hexdigest()
        ids.append(chunk_id)
        metadatas.append({
            "source": document_name,
            "page": chunk["page"]
        })

    # Add/upsert to ChromaDB in batches for memory efficiency
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end]
        )


def search_chunks(query_embedding, top_k=5):
    """
    Search ChromaDB for the most similar chunks to the query embedding.

    Args:
        query_embedding: The query embedding vector.
        top_k: Number of results to return.

    Returns:
        A dict with 'documents', 'metadatas', and 'distances' keys.
    """
    collection = _get_collection()

    # Ensure we don't request more results than exist
    total = collection.count()
    if total == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    k = min(top_k, total)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    return results


def get_document_count():
    """
    Return the total number of chunks stored in ChromaDB.
    """
    collection = _get_collection()
    return collection.count()
