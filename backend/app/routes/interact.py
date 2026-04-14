import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..database import get_connection
from ..models import InteractRequest, InteractionResponse
from ..services import audio_generator, rag_service

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/{talk_id}/interact", response_model=InteractionResponse, status_code=201)
def interact(talk_id: str, payload: InteractRequest):
    """Handle a user's interjection during the podcast playback."""
    conn = get_connection()
    try:
        # Validate talk exists and is ready
        talk = conn.execute(
            "SELECT * FROM talks WHERE id = ?", (talk_id,)
        ).fetchone()
        if not talk:
            raise HTTPException(status_code=404, detail="Talk not found")
        if talk["status"] != "ready":
            raise HTTPException(
                status_code=400,
                detail=f"Talk is not ready for interaction (status: {talk['status']})",
            )

        # Fetch source embeddings for RAG
        source_rows = conn.execute(
            "SELECT content, embedding FROM sources WHERE talk_id = ?", (talk_id,)
        ).fetchall()

        source_embeddings = []
        for row in source_rows:
            if row["embedding"]:
                try:
                    emb = json.loads(row["embedding"])
                    source_embeddings.append((row["content"], emb))
                except (json.JSONDecodeError, ValueError):
                    pass

        # Build answer via RAG
        question_emb = rag_service.create_question_embedding(payload.question)
        context_chunks = rag_service.find_relevant_chunks(
            question_emb, source_embeddings, top_k=3
        )

        # Fall back to full source content if no embeddings
        if not context_chunks:
            context_chunks = [row["content"][:2000] for row in source_rows]

        answer = rag_service.generate_answer(payload.question, context_chunks)

        # Generate TTS audio for the answer
        interaction_id = str(uuid.uuid4())
        audio_filename = f"{talk_id}_interact_{interaction_id}.mp3"
        audio_generator.generate_audio(answer, "Assistant", audio_filename)

        now = _now()
        conn.execute(
            """INSERT INTO interactions
               (id, talk_id, segment_index, question, answer, audio_file, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                interaction_id,
                talk_id,
                payload.segment_index,
                payload.question,
                answer,
                audio_filename,
                now,
            ),
        )
        conn.commit()

        return InteractionResponse(
            id=interaction_id,
            segment_index=payload.segment_index,
            question=payload.question,
            answer=answer,
            audio_file=audio_filename,
            created_at=now,
        )
    finally:
        conn.close()


@router.post("/{talk_id}/interact/voice", response_model=InteractionResponse, status_code=201)
async def interact_voice(
    talk_id: str,
    audio: UploadFile = File(...),
    segment_index: int = Form(...),
):
    """Handle a voice-recorded question by transcribing it and then calling the regular interact flow."""
    import os
    from openai import OpenAI

    conn = get_connection()
    try:
        talk = conn.execute(
            "SELECT * FROM talks WHERE id = ?", (talk_id,)
        ).fetchone()
        if not talk:
            raise HTTPException(status_code=404, detail="Talk not found")
        if talk["status"] != "ready":
            raise HTTPException(status_code=400, detail="Talk is not ready")
    finally:
        conn.close()

    # Transcribe using Whisper
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    audio_bytes = await audio.read()

    import io
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "question.webm"

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    question_text = transcript.text.strip()

    if not question_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio. Please try again.")

    # Reuse the text interact endpoint logic
    from ..models import InteractRequest
    return interact(talk_id, InteractRequest(question=question_text, segment_index=segment_index))
