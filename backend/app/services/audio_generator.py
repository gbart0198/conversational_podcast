import os
from pathlib import Path
from typing import Optional

from openai import OpenAI

_client: Optional[OpenAI] = None

AUDIO_DIR = os.getenv("AUDIO_DIR", "./data/audio")

# Voice mapping for each speaker
SPEAKER_VOICES = {
    "Alex": "onyx",
    "Sam": "nova",
    "Assistant": "alloy",
}


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def generate_audio(text: str, speaker: str, filename: str) -> str:
    """Generate TTS audio for the given text and save to file. Returns the file path."""
    client = _get_client()
    voice = SPEAKER_VOICES.get(speaker, "alloy")

    Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(AUDIO_DIR, filename)

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    response.stream_to_file(output_path)
    return output_path
