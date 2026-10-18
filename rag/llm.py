import requests
import json

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2"

# System prompt that constrains the LLM to answer only from provided context
SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based ONLY on the provided PDF context.

Rules you MUST follow:
1. Answer using ONLY the information found in the provided context below.
2. NEVER invent facts or use outside knowledge.
3. Do NOT make assumptions beyond what the context states.
4. If the context does not contain enough information to answer the question, respond with exactly: "I couldn't find that information in the uploaded PDF."
5. Keep your answers concise, clear, and well-structured.
6. When referencing specific information, mention the relevant page number(s) from the source.
7. If the context contains partial information, share what you found and note that the answer may be incomplete."""


def generate_answer(question, context):
    """
    Send the question and retrieved context to Ollama and return the generated answer.

    Args:
        question: The user's question.
        context: The retrieved context string from the PDF chunks.

    Returns:
        The generated answer string.

    Raises:
        ConnectionError: If Ollama is not running or unreachable.
    """
    # Build the user message with the retrieved context
    user_message = f"""Context from the uploaded PDF:
---
{context}
---

Question: {question}

Provide a clear and concise answer based ONLY on the context above."""

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "stream": False,
        "options": {
            "num_predict": 512
        }
    }

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=300  # Local CPU inference can take several minutes.
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Ollama is not running. Please start Ollama and try again. "
            "Download it from https://ollama.com and run: ollama pull llama3.2"
        )
    except requests.exceptions.Timeout:
        raise ConnectionError(
            "Ollama did not finish generating a response within 5 minutes. "
            "Please check that Ollama is running and try again."
        )
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Error communicating with Ollama: {str(e)}")

    try:
        result = response.json()
        answer = result["message"]["content"]
        return answer.strip()
    except (KeyError, json.JSONDecodeError):
        return "I couldn't find that information in the uploaded PDF."
