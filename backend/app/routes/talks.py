import io
import json
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from ..database import get_connection
from ..models import (
    CreateTalkRequest,
    ScriptSegmentResponse,
    SourceInput,
    TalkDetailResponse,
    TalkResponse,
)
from ..services import audio_generator, script_generator, source_processor

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _talk_row_to_response(row) -> TalkResponse:
    return TalkResponse(
        id=row["id"],
        title=row["title"],
        status=row["status"],
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Background task: generate script + audio
# ---------------------------------------------------------------------------

def _generate_talk(talk_id: str) -> None:
    conn = get_connection()
    try:
        # Mark as processing
        conn.execute(
            "UPDATE talks SET status = 'processing' WHERE id = ?", (talk_id,)
        )
        conn.commit()

        # Fetch source texts
        rows = conn.execute(
            "SELECT content FROM sources WHERE talk_id = ?", (talk_id,)
        ).fetchall()
        source_texts = [r["content"] for r in rows]

        if not source_texts:
            conn.execute(
                "UPDATE talks SET status = 'error' WHERE id = ?", (talk_id,)
            )
            conn.commit()
            return

        # Generate script
        script_data = script_generator.generate_script(source_texts)
        segments = script_data.get("segments", [])

        # Persist segments and generate audio
        for idx, seg in enumerate(segments):
            seg_id = str(uuid.uuid4())
            speaker = seg.get("speaker", "Alex")
            text = seg.get("text", "")
            audio_filename = f"{talk_id}_seg_{idx:03d}.mp3"

            audio_generator.generate_audio(text, speaker, audio_filename)

            conn.execute(
                """INSERT INTO script_segments
                   (id, talk_id, position, speaker, text, audio_file, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (seg_id, talk_id, idx, speaker, text, audio_filename, _now()),
            )

        conn.execute("UPDATE talks SET status = 'ready' WHERE id = ?", (talk_id,))
        conn.commit()
    except Exception as exc:
        conn.execute(
            "UPDATE talks SET status = 'error' WHERE id = ?", (talk_id,)
        )
        conn.commit()
        raise exc
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[TalkResponse])
def list_talks():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM talks ORDER BY created_at DESC"
        ).fetchall()
        return [_talk_row_to_response(r) for r in rows]
    finally:
        conn.close()


@router.post("/", response_model=TalkResponse, status_code=201)
def create_talk(payload: CreateTalkRequest, background_tasks: BackgroundTasks):
    """Create a new talk from text/URL sources and kick off generation."""
    talk_id = str(uuid.uuid4())
    now = _now()

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO talks (id, title, status, created_at) VALUES (?, ?, 'created', ?)",
            (talk_id, payload.title, now),
        )

        for src in payload.sources:
            content = _resolve_source(src)
            _insert_source(conn, talk_id, src.type, content)

        conn.commit()
    finally:
        conn.close()

    background_tasks.add_task(_generate_talk, talk_id)

    return TalkResponse(id=talk_id, title=payload.title, status="created", created_at=now)


@router.post("/upload", response_model=TalkResponse, status_code=201)
async def create_talk_with_file(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
):
    """Create a new talk by uploading a PDF or text file."""
    talk_id = str(uuid.uuid4())
    now = _now()

    file_bytes = await file.read()

    if file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
        content = source_processor.extract_text_from_pdf(file_bytes)
        src_type = "pdf"
    else:
        content = file_bytes.decode("utf-8", errors="replace")
        src_type = "text"

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO talks (id, title, status, created_at) VALUES (?, ?, 'created', ?)",
            (talk_id, title, now),
        )
        _insert_source(conn, talk_id, src_type, content)
        conn.commit()
    finally:
        conn.close()

    background_tasks.add_task(_generate_talk, talk_id)

    return TalkResponse(id=talk_id, title=title, status="created", created_at=now)


@router.get("/{talk_id}", response_model=TalkDetailResponse)
def get_talk(talk_id: str):
    conn = get_connection()
    try:
        talk = conn.execute(
            "SELECT * FROM talks WHERE id = ?", (talk_id,)
        ).fetchone()
        if not talk:
            raise HTTPException(status_code=404, detail="Talk not found")

        segments_rows = conn.execute(
            "SELECT * FROM script_segments WHERE talk_id = ? ORDER BY position",
            (talk_id,),
        ).fetchall()
        interactions_rows = conn.execute(
            "SELECT * FROM interactions WHERE talk_id = ? ORDER BY created_at",
            (talk_id,),
        ).fetchall()

        segments = [
            ScriptSegmentResponse(
                id=r["id"],
                position=r["position"],
                speaker=r["speaker"],
                text=r["text"],
                audio_file=r["audio_file"],
            )
            for r in segments_rows
        ]

        from ..models import InteractionResponse

        interactions = [
            InteractionResponse(
                id=r["id"],
                segment_index=r["segment_index"],
                question=r["question"],
                answer=r["answer"],
                audio_file=r["audio_file"],
                created_at=r["created_at"],
            )
            for r in interactions_rows
        ]

        return TalkDetailResponse(
            id=talk["id"],
            title=talk["title"],
            status=talk["status"],
            created_at=talk["created_at"],
            segments=segments,
            interactions=interactions,
        )
    finally:
        conn.close()


@router.delete("/{talk_id}", status_code=204)
def delete_talk(talk_id: str):
    conn = get_connection()
    try:
        result = conn.execute("DELETE FROM talks WHERE id = ?", (talk_id,))
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Talk not found")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _resolve_source(src: SourceInput) -> str:
    if src.type == "url":
        return source_processor.extract_text_from_url(src.content)
    return src.content  # 'text' type – content is already the text


def _insert_source(conn, talk_id: str, src_type: str, content: str) -> None:
    # Create embedding for vector search
    try:
        embedding = source_processor.create_embedding(content[:20000])
        embedding_json = json.dumps(embedding)
    except Exception:
        embedding_json = None

    src_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO sources (id, talk_id, type, content, embedding, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (src_id, talk_id, src_type, content, embedding_json, _now()),
    )
