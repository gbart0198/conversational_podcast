import json
import os
from typing import List, Optional

from openai import OpenAI

_client: Optional[OpenAI] = None

SCRIPT_SYSTEM_PROMPT = """You are an expert podcast producer. Your job is to transform source material into a natural, engaging conversational podcast script between two hosts: Alex and Sam.

Guidelines:
- Alex is curious and asks insightful questions.
- Sam is knowledgeable and gives clear, relatable explanations.
- The conversation should flow naturally, with each host building on the other's points.
- Cover the key topics from the source material.
- Include analogies, examples, and moments of reflection.
- Keep each speaking turn concise (2-5 sentences).
- Generate 12-20 segments total.

Respond ONLY with a valid JSON object in this exact format:
{
  "title": "Episode title based on the content",
  "segments": [
    {"speaker": "Alex", "text": "..."},
    {"speaker": "Sam", "text": "..."}
  ]
}"""


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def generate_script(source_texts: List[str]) -> dict:
    """Generate a conversational podcast script from source texts."""
    client = _get_client()

    # Combine and truncate source texts
    combined = "\n\n---\n\n".join(source_texts)
    truncated = combined[:12000]

    user_message = f"Here is the source material for the podcast:\n\n{truncated}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
