from datetime import datetime

from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessageOut]
