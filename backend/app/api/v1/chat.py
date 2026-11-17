"""Chat endpoints for the NutriLens assistant.

Guests' chats are never stored. For signed-in users each conversation is saved to their account, and a conversation
started from a report is linked to it, so opening that report again continues the same chat. Deleting the report or
the account deletes its chats (ON DELETE CASCADE).
"""
import re
import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.chat.engine import answer
from app.core.deps import get_current_user, get_optional_user
from app.core.ratelimit import client_ip, limiter
from app.models.database import get_db, utcnow
from app.models.entities import ChatConversation, ChatMessage, Report, User

router = APIRouter()
MAX_MESSAGES = 300  # per conversation (user + assistant messages)
MAX_LISTED = 100


class ChatMarker(BaseModel):
    key: str = Field(max_length=60)
    name: str = Field(default="", max_length=120)
    value: Optional[float] = None
    unit: str = Field(default="", max_length=30)
    status: str = Field(default="", max_length=20)
    range_low: Optional[float] = None
    range_high: Optional[float] = None


class ChatPlan(BaseModel):
    name: str = Field(max_length=200)
    purpose: str = Field(default="improve", max_length=20)
    foods: List[str] = Field(default_factory=list, max_length=20)


class ChatContext(BaseModel):
    """The user's own analysed results, sent by the results page so answers can be personal."""
    markers: List[ChatMarker] = Field(default_factory=list, max_length=100)
    plans: List[ChatPlan] = Field(default_factory=list, max_length=40)
    diet_type: Optional[str] = Field(default=None, max_length=20)
    allergens: List[str] = Field(default_factory=list, max_length=10)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    topic: Optional[str] = Field(default=None, max_length=80)
    context: Optional[ChatContext] = None
    conversation_id: Optional[str] = Field(default=None, max_length=36)
    report_id: Optional[str] = Field(default=None, max_length=36)


class ChatResponse(BaseModel):
    reply: str
    kind: str
    suggestions: List[str]
    topic: Optional[str] = None
    conversation_id: Optional[str] = None
    saved: bool = False


class ChatMessageOut(BaseModel):
    role: str
    text: str
    kind: str
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    report_id: Optional[str] = None
    report_date: Optional[datetime] = None
    preview: str = ""
    message_count: int
    updated_at: datetime


class ConversationDetail(BaseModel):
    id: str
    title: str
    report_id: Optional[str] = None
    report_date: Optional[datetime] = None
    topic: Optional[str] = None
    updated_at: datetime
    messages: List[ChatMessageOut]


def _plain(text: str, limit: int = 120) -> str:
    text = re.sub(r"\*\*|^- ", "", text, flags=re.M)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _title(message: str) -> str:
    title = " ".join(message.split())
    title = title[0].upper() + title[1:] if title else "New chat"
    return title if len(title) <= 80 else title[:79].rstrip() + "…"


def _context_from_report(report: Report) -> dict[str, Any]:
    """Rebuild the assistant's context from a saved analysis, so a report's chat stays personal."""
    analysis = report.analysis or {}
    return {
        "markers": [{"key": m.get("biomarker_key", ""), "name": m.get("display_name", ""), "value": m.get("value"),
                     "unit": m.get("unit", ""), "status": m.get("status", ""), "range_low": m.get("range_low"),
                     "range_high": m.get("range_high")} for m in analysis.get("marker_analyses", [])],
        "plans": [{"name": p.get("biomarker_display_name", ""), "purpose": p.get("purpose", "improve"),
                   "foods": [f.get("name", "") for f in p.get("recommended_foods", [])]}
                  for p in analysis.get("recommendations", [])],
        "diet_type": (analysis.get("user_profile") or {}).get("diet_type"),
        "allergens": (analysis.get("user_profile") or {}).get("allergens", []),
    }


def _own_conversation(db: Session, user: User, conversation_id: str) -> ChatConversation:
    conversation = db.get(ChatConversation, conversation_id)
    if conversation is None or conversation.owner_id != user.id:
        raise HTTPException(404, "Chat not found.")
    return conversation


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request, db: Session = Depends(get_db),
         user: Optional[User] = Depends(get_optional_user)) -> ChatResponse:
    if not limiter.allow(f"chat:{client_ip(request)}", limit=40, window_seconds=60):
        raise HTTPException(429, "You're sending messages very quickly. Please wait a moment and try again.")
    context = body.context.model_dump() if body.context else None

    if user is None:  # guests: answer only, nothing stored
        result = answer(body.message, body.topic, context)
        return ChatResponse(reply=result.reply, kind=result.kind, suggestions=result.suggestions[:4], topic=result.topic)

    report = None
    if body.conversation_id:
        conversation = _own_conversation(db, user, body.conversation_id)
        if conversation.report_id:
            report = db.get(Report, conversation.report_id)
    else:
        if body.report_id:
            report = db.get(Report, body.report_id)
            if report is None or report.owner_id != user.id:
                raise HTTPException(404, "Report not found.")
        conversation = ChatConversation(id=str(uuid.uuid4()), owner_id=user.id, report_id=report.id if report else None,
                                        title=_title(body.message), message_count=0)
        db.add(conversation)
    if conversation.message_count + 2 > MAX_MESSAGES:
        raise HTTPException(409, "This chat is full. Please start a new chat.")

    if context is None and report is not None:
        context = _context_from_report(report)
    result = answer(body.message, body.topic or conversation.topic, context)
    suggestions = result.suggestions[:4]
    now = utcnow()
    db.add(ChatMessage(conversation_id=conversation.id, role="user", text=body.message.strip()[:500],
                       kind="user", created_at=now))
    db.add(ChatMessage(conversation_id=conversation.id, role="bot", text=result.reply, kind=result.kind,
                       suggestions=suggestions, created_at=now))
    conversation.message_count += 2
    conversation.topic = result.topic or conversation.topic
    conversation.updated_at = now
    db.commit()
    return ChatResponse(reply=result.reply, kind=result.kind, suggestions=suggestions, topic=result.topic,
                        conversation_id=conversation.id, saved=True)


@router.get("/chat/conversations", response_model=List[ConversationSummary])
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(ChatConversation, Report.created_at)
        .outerjoin(Report, Report.id == ChatConversation.report_id)
        .where(ChatConversation.owner_id == user.id)
        .order_by(ChatConversation.updated_at.desc())
        .limit(MAX_LISTED)
    ).all()
    ids = [conversation.id for conversation, _ in rows]
    previews: dict[str, str] = {}
    if ids:
        last = (select(func.max(ChatMessage.id)).where(ChatMessage.conversation_id.in_(ids), ChatMessage.role == "bot")
                .group_by(ChatMessage.conversation_id))
        for message in db.scalars(select(ChatMessage).where(ChatMessage.id.in_(last))):
            previews[message.conversation_id] = _plain(message.text)
    return [ConversationSummary(id=c.id, title=c.title, report_id=c.report_id, report_date=report_date,
                                preview=previews.get(c.id, ""), message_count=c.message_count, updated_at=c.updated_at)
            for c, report_date in rows]


@router.get("/chat/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = _own_conversation(db, user, conversation_id)
    report = db.get(Report, conversation.report_id) if conversation.report_id else None
    messages = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation.id)
                          .order_by(ChatMessage.id)).all()
    return ConversationDetail(
        id=conversation.id, title=conversation.title, report_id=conversation.report_id,
        report_date=report.created_at if report else None, topic=conversation.topic,
        updated_at=conversation.updated_at,
        messages=[ChatMessageOut(role=m.role, text=m.text, kind=m.kind, suggestions=m.suggestions or [],
                                 created_at=m.created_at) for m in messages])


@router.delete("/chat/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(_own_conversation(db, user, conversation_id))
    db.commit()
    return Response(status_code=204)
