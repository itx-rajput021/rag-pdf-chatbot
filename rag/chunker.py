def chunk_text(pages, chunk_size=1000, overlap=200):
    """
    Split page texts into overlapping chunks while preserving page numbers.

    Args:
        pages: List of dicts with 'page' and 'text' keys.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of dicts, each with 'text' and 'page' keys.
    """
    chunks = []

    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page"]

        # If the text fits in a single chunk, add it directly
        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "page": page_num
            })
            continue

        # Split long text into overlapping chunks
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Only add non-empty chunks
            if chunk.strip():
                chunks.append({
                    "text": chunk.strip(),
                    "page": page_num
                })

            # Move the window forward by (chunk_size - overlap)
            start += chunk_size - overlap

    return chunks
