import pymupdf as fitz


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyMuPDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of dicts, each with 'page' (1-indexed) and 'text' keys.
        Pages with no text content are excluded.

    Raises:
        Exception: If the PDF cannot be opened or is corrupted.
    """
    pages = []

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        raise Exception(
            "Could not open the PDF file. It may be corrupted or password-protected."
        )

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()

        # Skip empty pages
        if text:
            pages.append({
                "page": page_num + 1,  # 1-indexed page numbers
                "text": text
            })

    doc.close()
    return pages
