import json
import os
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

try:
    import PyPDF2
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

from openai import OpenAI

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def extract_text_from_url(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; ConversationalPodcast/1.0)"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Remove scripts and styles
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not _PDF_AVAILABLE:
        raise RuntimeError("PyPDF2 is not installed")
    import io
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n\n".join(parts).strip()


def create_embedding(text: str) -> List[float]:
    client = _get_client()
    # Truncate to avoid token limit (approx 8191 tokens for text-embedding-3-small)
    truncated = text[:20000]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=truncated,
    )
    return response.data[0].embedding


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks for better retrieval."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
