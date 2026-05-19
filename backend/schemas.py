from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TextInputRequest(BaseModel):
    anon_id: Optional[str] = None
    text: str = Field(min_length=1)
    country: str = "india"


class ProcessResponse(BaseModel):
    message_id: int
    anon_id: str
    input_type: str
    interpreted_text: str
    emotion_label: str
    intensity: str
    ai_response: str
    emergency: bool
    emergency_info: Optional[Dict[str, Any]] = None


class PeerPostRequest(BaseModel):
    anon_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=1000)


class PeerReplyRequest(BaseModel):
    anon_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=1000)


class PeerReply(BaseModel):
    id: int
    post_id: int
    anon_id: str
    message: str
    created_at: str


class PeerPost(BaseModel):
    id: int
    anon_id: str
    message: str
    created_at: str
    replies: List[PeerReply]
