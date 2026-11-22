"""Request dependencies: who is calling, and what are they allowed to do."""
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_token
from app.models.database import get_db, utcnow
from app.models.entities import ROLE_OWNER, STATUS_ACTIVE, User, UserSession


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    session = db.query(UserSession).filter_by(token_hash=hash_token(token)).first()
    now = utcnow()
    hard_end = session.created_at + timedelta(hours=settings.session_max_hours) if session else None
    if session is None or session.expires_at <= now or hard_end <= now:
        return None
    # Sliding idle timeout: each use moves the end to 2 hours from now, never past 1 day after sign-in.
    # Written at most every few minutes, so ordinary page loads do not all write to the database.
    new_end = min(now + timedelta(minutes=settings.session_idle_minutes), hard_end)
    if abs((new_end - session.expires_at).total_seconds()) > 300:
        session.expires_at = new_end
        db.commit()
    user = db.get(User, session.user_id)
    if user is None or user.status != STATUS_ACTIVE:
        return None
    request.state.session_id = session.id
    return user


def get_current_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(401, "Please sign in to continue.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_staff:
        raise HTTPException(403, "Administrator access is required.")
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_OWNER:
        raise HTTPException(403, "Only the owner can do this.")
    return user
