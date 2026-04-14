import json
import os
from typing import List, Optional, Tuple

import numpy as np
from openai import OpenAI

_client: Optional[OpenAI] = None

RAG_SYSTEM_PROMPT = """You are a knowledgeable assistant helping a listener who is engaged with a podcast. You have access to the source material the podcast is based on. 

Answer the user's question clearly and concisely, drawing specifically from the provided context. If the context doesn't contain enough information, say so honestly. Keep your answer conversational, as if you are a helpful podcast host pausing to clarify a point.

Keep your answer to 2-4 sentences unless more detail is clearly needed."""


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    arr_a = np.array(a, dtype=np.float32)
    arr_b = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))


def find_relevant_chunks(
    question_embedding: List[float],
    source_embeddings: List[Tuple[str, List[float]]],
    top_k: int = 3,
) -> List[str]:
    """Return the top-k most relevant source content chunks."""
    if not source_embeddings:
        return []

    scored = [
        (content, _cosine_similarity(question_embedding, emb))
        for content, emb in source_embeddings
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [content for content, _ in scored[:top_k]]


def create_question_embedding(question: str) -> List[float]:
    client = _get_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=question,
    )
    return response.data[0].embedding


def generate_answer(question: str, context_chunks: List[str]) -> str:
    """Generate an answer using RAG context."""
    client = _get_client()

    context = "\n\n---\n\n".join(context_chunks)
    user_message = (
        f"Context from the podcast source material:\n\n{context}\n\n"
        f"Listener's question: {question}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()
