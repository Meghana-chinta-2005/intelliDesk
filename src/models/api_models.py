import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    chunk_count: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    sender: str
    text: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: int
    title: str
    created_at: datetime.datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    conversation_id: Optional[int] = Field(None, description="If empty, a new conversation will be created.")


class AnswerResponse(BaseModel):
    answer: str
    conversation_id: int
    sources: List[Dict[str, Any]]
    question: str = ""


class SummaryResponse(BaseModel):
    document_id: int
    summary: str


class LogDetail(BaseModel):
    id: int
    event_type: str
    username: Optional[str] = None
    message: str
    created_at: datetime.datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    total_documents: int
    total_queries: int
    avg_response_time: float
    recent_logs: List[LogDetail]
