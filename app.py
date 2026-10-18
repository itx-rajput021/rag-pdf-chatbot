import os
import uuid
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from rag.pdf_loader import extract_text_from_pdf
from rag.chunker import chunk_text
from rag.embeddings import get_embedding_model
from rag.vector_store import add_chunks, search_chunks, get_document_count
from rag.retriever import retrieve_context
from rag.llm import generate_answer

app = Flask(__name__)

# Configuration
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads"
)
ALLOWED_EXTENSIONS = {"pdf"}

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Pre-load embedding model at startup so first request is fast
print("Loading embedding model...")
get_embedding_model()
print("Embedding model loaded.")


def allowed_file(filename):
    """Check if the uploaded file has a valid PDF extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Serve the main chat interface."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_pdf():
    """Handle PDF upload, extract text, chunk, embed, and store in ChromaDB."""
    try:
        # Check if file is present in the request
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided. Please select a PDF."}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"success": False, "error": "Please select a PDF."}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF files are allowed."}), 400

        # Generate a unique filename to avoid collisions and path traversal
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)

        # Extract text from the PDF
        try:
            pages = extract_text_from_pdf(filepath)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Failed to process the PDF: {str(e)}"
            }), 400

        if not pages:
            return jsonify({
                "success": False,
                "error": "No selectable text was found. This may be a scanned PDF."
            }), 400

        # Check if any page actually has text content
        total_text = "".join(p["text"] for p in pages).strip()
        if not total_text:
            return jsonify({
                "success": False,
                "error": "No selectable text was found. This may be a scanned PDF."
            }), 400

        # Split text into overlapping chunks
        chunks = chunk_text(pages, chunk_size=1000, overlap=200)

        if not chunks:
            return jsonify({
                "success": False,
                "error": "Could not create text chunks from this PDF."
            }), 400

        # Store chunks with embeddings in ChromaDB
        add_chunks(chunks, document_name=original_name)

        return jsonify({
            "success": True,
            "filename": original_name,
            "pages": len(pages),
            "chunks": len(chunks)
        })

    except Exception:
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while processing the PDF."
        }), 500


@app.route("/ask", methods=["POST"])
def ask_question():
    """Handle user questions: retrieve context and generate an answer."""
    try:
        data = request.get_json()

        if not data or "question" not in data or not data["question"].strip():
            return jsonify({"success": False, "error": "Please enter a question."}), 400

        question = data["question"].strip()

        # Retrieve relevant context from ChromaDB
        context, sources = retrieve_context(question, top_k=5)

        if not context:
            return jsonify({
                "success": True,
                "answer": "I couldn't find that information in the uploaded PDF.",
                "sources": []
            })

        # Generate answer using Ollama
        answer = generate_answer(question, context)

        return jsonify({
            "success": True,
            "answer": answer,
            "sources": sources
        })

    except ConnectionError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 503
    except Exception:
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while generating the answer."
        }), 500


@app.route("/stats", methods=["GET"])
def stats():
    """Return the number of chunks stored in ChromaDB."""
    try:
        count = get_document_count()
        return jsonify({"success": True, "total_chunks": count})
    except Exception:
        return jsonify({"success": False, "error": "Could not retrieve stats."}), 500


@app.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeding the 25 MB limit."""
    return jsonify({
        "success": False,
        "error": "File is too large. Maximum upload size is 25 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
