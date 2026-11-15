"""Shared account operations: sessions, cookies, one-time links and audit logging."""
import secrets
from datetime import timedelta
from typing import Any, Optional

from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.core.ratelimit import client_ip
from app.core.security import hash_token, new_token
from app.models.database import utcnow
from app.models.entities import (
    LINK_INVITE, ROLE_ADMIN, ROLE_OWNER, ROLE_USER, AccessLink, AuditLog, User, UserSession,
)


# ------------------------------------------------------------------ sessions & cookies

def _set_cookie(response: Response, name: str, value: str, *, http_only: bool) -> None:
    response.set_cookie(
        name, value,
        max_age=settings.session_ttl_days * 86400,
        httponly=http_only,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def set_csrf_cookie(response: Response) -> None:
    # Readable by the frontend, which echoes it in the X-CSRF-Token header (double-submit).
    _set_cookie(response, settings.csrf_cookie_name, secrets.token_urlsafe(24), http_only=False)


def start_session(db: Session, user: User, request: Request, response: Response) -> None:
    now = utcnow()
    db.query(UserSession).filter(UserSession.user_id == user.id,
                                 UserSession.expires_at <= now).delete(synchronize_session=False)
    token = new_token()
    db.add(UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=now + timedelta(days=settings.session_ttl_days),
        ip=client_ip(request),
        user_agent=(request.headers.get("user-agent") or "")[:255],
    ))
    _set_cookie(response, settings.session_cookie_name, token, http_only=True)
    set_csrf_cookie(response)


def clear_auth_cookies(response: Response) -> None:
    for name in (settings.session_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(name, path="/", secure=settings.cookie_secure, samesite="lax")


def revoke_sessions(db: Session, user_id: str) -> int:
    return db.query(UserSession).filter(UserSession.user_id == user_id).delete(synchronize_session=False)


# ------------------------------------------------------------------ one-time links

def issue_link(db: Session, *, kind: str, email: str, created_by: Optional[User],
               role: Optional[str] = None, user_id: Optional[str] = None) -> tuple[AccessLink, str]:
    token = new_token()
    link = AccessLink(
        kind=kind, email=email, role=role, user_id=user_id,
        token_hash=hash_token(token),
        created_by_id=created_by.id if created_by else None,
        expires_at=utcnow() + timedelta(hours=settings.link_ttl_hours),
    )
    db.add(link)
    return link, token


def renew_link(link: AccessLink) -> str:
    token = new_token()
    link.token_hash = hash_token(token)
    link.created_at = utcnow()
    link.expires_at = utcnow() + timedelta(hours=settings.link_ttl_hours)
    link.revoked_at = None
    return token


def find_usable_link(db: Session, token: str, kind: str) -> Optional[AccessLink]:
    link = db.query(AccessLink).filter_by(token_hash=hash_token(token), kind=kind).first()
    if link is None or link.status(utcnow()) != "pending":
        return None
    return link


def link_path(kind: str, token: str) -> str:
    return f"/invite/{token}" if kind == LINK_INVITE else f"/reset-password/{token}"


def revoke_pending_links(db: Session, *, kind: str, email: Optional[str] = None,
                         user_id: Optional[str] = None) -> None:
    query = db.query(AccessLink).filter(AccessLink.kind == kind, AccessLink.used_at.is_(None),
                                        AccessLink.revoked_at.is_(None))
    if email is not None:
        query = query.filter(AccessLink.email == email)
    if user_id is not None:
        query = query.filter(AccessLink.user_id == user_id)
    for link in query.all():
        link.revoked_at = utcnow()


# ------------------------------------------------------------------ permissions

def can_manage(actor: User, target: User) -> bool:
    """Admins manage users; only the owner manages admins; nobody manages the owner."""
    if actor.id == target.id or target.role == ROLE_OWNER:
        return False
    if target.role == ROLE_ADMIN:
        return actor.role == ROLE_OWNER
    return target.role == ROLE_USER and actor.is_staff


# ------------------------------------------------------------------ audit log

def audit(db: Session, request: Optional[Request], action: str, *, actor: Optional[User] = None,
          target: Optional[User] = None, target_type: Optional[str] = None,
          target_id: Optional[str] = None, target_email: Optional[str] = None,
          details: Optional[dict[str, Any]] = None) -> None:
    db.add(AuditLog(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        action=action,
        target_type=target_type or ("user" if target else None),
        target_id=target_id or (target.id if target else None),
        target_email=target_email or (target.email if target else None),
        ip=client_ip(request) if request is not None else None,
        details=details,
    ))
