from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.chat import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatMessageIn, ChatMessageOut, ChatResponse
from app.services.groq_service import build_user_context, chat_completion

router = APIRouter(prefix="/chat", tags=["chat"])

HISTORY_LIMIT = 20  # number of past messages to feed back as context


@router.post("/message", response_model=ChatResponse)
def send_message(
    payload: ChatMessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Build recent history for context
    recent = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    recent = list(reversed(recent))
    llm_messages = [{"role": m.role, "content": m.content} for m in recent]

    reply_text = chat_completion(
        llm_messages,
        user_context=build_user_context(current_user),
        language=payload.language,
    )

    assistant_msg = ChatMessage(user_id=current_user.id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return ChatResponse(
        reply=reply_text,
        history=[ChatMessageOut.model_validate(m) for m in history],
    )


@router.get("/history", response_model=list[ChatMessageOut])
def get_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
