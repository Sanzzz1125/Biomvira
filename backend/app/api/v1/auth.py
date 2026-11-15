"""Sign-up, login, sessions, self-service account management and one-time links."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, get_optional_user
from app.core.ratelimit import enforce_rate_limit
from app.core.security import (
    hash_password, needs_rehash, normalize_email, password_problem, verify_password,
)
from app.models.account_schemas import (
    AcceptInviteRequest, ChangePasswordRequest, LinkInfo, LoginRequest, PasswordConfirmRequest,
    RegisterRequest, ResetPasswordRequest, SessionOut, UpdateProfileRequest, UserOut,
)
from app.models.database import get_db, utcnow
from app.models.entities import (
    LINK_INVITE, LINK_RESET, ROLE_OWNER, ROLE_USER, STATUS_ACTIVE, User, UserSession,
)
from app.services.accounts import (
    audit, clear_auth_cookies, find_usable_link, revoke_sessions, set_csrf_cookie, start_session,
)

router = APIRouter(prefix="/auth")

INVALID_CREDENTIALS = "Invalid email or password."
INVALID_LINK = "This link is invalid, already used or expired. Ask for a new one."


def _check_password(password: str) -> None:
    problem = password_problem(password)
    if problem:
        raise HTTPException(422, problem)


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "register")
    _check_password(body.password)
    email = normalize_email(body.email)
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists. Try logging in.")
    user = User(email=email, name=body.name, password_hash=hash_password(body.password), role=ROLE_USER,
                last_login_at=utcnow())
    db.add(user)
    db.flush()
    start_session(db, user, request, response)
    audit(db, request, "auth.register", actor=user, target=user)
    db.commit()
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "login")
    email = normalize_email(body.email)
    user = db.query(User).filter_by(email=email).first()
    now = utcnow()

    if user is not None and user.is_locked(now):
        minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise HTTPException(429, f"Too many failed attempts. Try again in {minutes} minute(s).")

    if not verify_password(user.password_hash if user else None, body.password):
        if user is not None:
            user.failed_logins += 1
            if user.failed_logins >= settings.max_failed_logins:
                user.failed_logins = 0
                user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
                audit(db, request, "auth.locked", target=user)
        audit(db, request, "auth.login_failed", target=user, target_email=email)
        db.commit()
        raise HTTPException(401, INVALID_CREDENTIALS)

    if user.status != STATUS_ACTIVE:
        raise HTTPException(403, "This account has been disabled. Contact an administrator.")

    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = now
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    start_session(db, user, request, response)
    audit(db, request, "auth.login", actor=user, target=user)
    db.commit()
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db),
           user: Optional[User] = Depends(get_optional_user)):
    session_id = getattr(request.state, "session_id", None)
    if session_id:
        db.query(UserSession).filter_by(id=session_id).delete()
        audit(db, request, "auth.logout", actor=user, target=user)
        db.commit()
    clear_auth_cookies(response)


@router.get("/session", response_model=SessionOut)
def session(request: Request, response: Response, user: Optional[User] = Depends(get_optional_user)):
    """Who is signed in, if anyone. Always 200, so the site can check quietly on every page load."""
    if user is not None and not request.cookies.get(settings.csrf_cookie_name):
        set_csrf_cookie(response)
    return SessionOut(user=user)


@router.get("/me", response_model=UserOut)
def me(request: Request, response: Response, user: User = Depends(get_current_user)):
    if not request.cookies.get(settings.csrf_cookie_name):
        set_csrf_cookie(response)
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: UpdateProfileRequest, request: Request, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    if body.name != user.name:
        user.name = body.name
        audit(db, request, "account.updated", actor=user, target=user, details={"fields": ["name"]})
        db.commit()
    return user


@router.post("/change-password", response_model=UserOut)
def change_password(body: ChangePasswordRequest, request: Request, response: Response,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(user.password_hash, body.current_password):
        raise HTTPException(400, "Your current password is incorrect.")
    _check_password(body.new_password)
    user.password_hash = hash_password(body.new_password)
    # Signs out every other device, then starts a fresh session here.
    revoke_sessions(db, user.id)
    start_session(db, user, request, response)
    audit(db, request, "auth.password_changed", actor=user, target=user)
    db.commit()
    return user


@router.post("/delete-account", status_code=204)
def delete_account(body: PasswordConfirmRequest, request: Request, response: Response,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(user.password_hash, body.password):
        raise HTTPException(400, "Your password is incorrect.")
    if user.role == ROLE_OWNER:
        raise HTTPException(400, "The owner account can't be deleted. Transfer ownership to an admin first.")
    audit(db, request, "account.deleted", actor=user, target=user)
    db.delete(user)  # sessions, links and reports are removed by ON DELETE CASCADE
    db.commit()
    clear_auth_cookies(response)


# ------------------------------------------------------------------ one-time links

def _link_info(db: Session, token: str, kind: str) -> LinkInfo:
    link = find_usable_link(db, token, kind)
    if link is None:
        raise HTTPException(404, INVALID_LINK)
    inviter = db.get(User, link.created_by_id) if link.created_by_id else None
    return LinkInfo(kind=link.kind, email=link.email, role=link.role, expires_at=link.expires_at,
                    invited_by=inviter.name if inviter else None)


@router.get("/invites/{token}", response_model=LinkInfo)
def invite_info(token: str, db: Session = Depends(get_db)):
    return _link_info(db, token, LINK_INVITE)


@router.post("/invites/{token}/accept", response_model=UserOut, status_code=201)
def accept_invite(token: str, body: AcceptInviteRequest, request: Request, response: Response,
                  db: Session = Depends(get_db)):
    enforce_rate_limit(request, "invite")
    link = find_usable_link(db, token, LINK_INVITE)
    if link is None:
        raise HTTPException(404, INVALID_LINK)
    if db.query(User).filter_by(email=link.email).first():
        raise HTTPException(409, "An account with this email already exists. Log in instead.")
    _check_password(body.password)
    user = User(email=link.email, name=body.name, password_hash=hash_password(body.password),
                role=link.role or ROLE_USER, last_login_at=utcnow())
    db.add(user)
    link.used_at = utcnow()
    db.flush()
    start_session(db, user, request, response)
    audit(db, request, "invite.accepted", actor=user, target=user, details={"role": user.role})
    db.commit()
    return user


@router.get("/reset/{token}", response_model=LinkInfo)
def reset_info(token: str, db: Session = Depends(get_db)):
    return _link_info(db, token, LINK_RESET)


@router.post("/reset/{token}", response_model=UserOut)
def reset_password(token: str, body: ResetPasswordRequest, request: Request, response: Response,
                   db: Session = Depends(get_db)):
    enforce_rate_limit(request, "reset")
    link = find_usable_link(db, token, LINK_RESET)
    user = db.get(User, link.user_id) if link and link.user_id else None
    if link is None or user is None:
        raise HTTPException(404, INVALID_LINK)
    _check_password(body.password)
    user.password_hash = hash_password(body.password)
    user.failed_logins = 0
    user.locked_until = None
    link.used_at = utcnow()
    revoke_sessions(db, user.id)
    audit(db, request, "reset.completed", actor=user, target=user)
    if user.status != STATUS_ACTIVE:
        db.commit()
        raise HTTPException(403, "Password updated, but this account is disabled. Contact an administrator.")
    user.last_login_at = utcnow()
    start_session(db, user, request, response)
    db.commit()
    return user
