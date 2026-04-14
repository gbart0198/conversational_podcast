from typing import List, Optional
from pydantic import BaseModel


class SourceInput(BaseModel):
    type: str  # 'text' | 'url'
    content: str


class CreateTalkRequest(BaseModel):
    title: str
    sources: List[SourceInput]


class TalkResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: str


class ScriptSegmentResponse(BaseModel):
    id: str
    position: int
    speaker: str
    text: str
    audio_file: Optional[str] = None


class InteractionResponse(BaseModel):
    id: str
    segment_index: int
    question: str
    answer: str
    audio_file: Optional[str] = None
    created_at: str


class TalkDetailResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    segments: List[ScriptSegmentResponse] = []
    interactions: List[InteractionResponse] = []


class InteractRequest(BaseModel):
    question: str
    segment_index: int
