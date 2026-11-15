"""Admin portal API. Admins manage users; only the owner manages admins and ownership."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.deps import require_admin, require_owner
from app.core.security import normalize_email, verify_password
from app.models.account_schemas import (
    AddAdminRequest, AddAdminResult, AdminUpdateUserRequest, AdminUserOut, AdminUserPage, AuditEntry,
    AuditPage, DailyCount, InviteCreateRequest, InviteCreated, InviteOut, LinkCreated, StatsOut,
    TransferOwnershipRequest, UserOut,
)
from app.models.database import get_db, utcnow
from app.models.entities import (
    LINK_INVITE, LINK_RESET, ROLE_ADMIN, ROLE_OWNER, ROLE_USER, ROLES, STATUS_ACTIVE, STATUS_DISABLED,
    AccessLink, AuditLog, Report, User,
)
from app.services.accounts import (
    audit, can_manage, issue_link, link_path, renew_link, revoke_pending_links, revoke_sessions,
)

router = APIRouter(prefix="/admin")
IST = timezone(timedelta(hours=5, minutes=30))


# ------------------------------------------------------------------ helpers

def _report_counts(db: Session, user_ids: list[str]) -> dict[str, int]:
    if not user_ids:
        return {}
    rows = (db.query(Report.owner_id, func.count(Report.id))
            .filter(Report.owner_id.in_(user_ids)).group_by(Report.owner_id).all())
    return dict(rows)


def _user_out(db: Session, actor: User, user: User, count: Optional[int] = None) -> AdminUserOut:
    if count is None:
        count = _report_counts(db, [user.id]).get(user.id, 0)
    return AdminUserOut(
        **UserOut.model_validate(user).model_dump(),
        report_count=count, locked=user.is_locked(utcnow()), can_manage=can_manage(actor, user),
    )


def _managed_user(db: Session, actor: User, user_id: str) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found.")
    if not can_manage(actor, target):
        if target.id == actor.id:
            raise HTTPException(403, "Use Account settings to change your own account.")
        if target.role == ROLE_OWNER:
            raise HTTPException(403, "The owner account can't be changed by anyone else.")
        raise HTTPException(403, "Only the owner can manage admins.")
    return target


def _confirm_password(actor: User, password: str) -> None:
    if not verify_password(actor.password_hash, password):
        raise HTTPException(400, "Your password is incorrect.")


def _invite_out(db: Session, link: AccessLink) -> InviteOut:
    creator = db.get(User, link.created_by_id) if link.created_by_id else None
    return InviteOut(id=link.id, email=link.email, role=link.role, status=link.status(utcnow()),
                     created_at=link.created_at, expires_at=link.expires_at,
                     created_by=creator.email if creator else None)


def _check_invite_role(actor: User, role: Optional[str]) -> None:
    if role == ROLE_ADMIN and actor.role != ROLE_OWNER:
        raise HTTPException(403, "Only the owner can invite admins.")


# ------------------------------------------------------------------ dashboard

@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    now = utcnow()
    week_ago, fortnight_ago = now - timedelta(days=7), now - timedelta(days=14)
    by_role = dict(db.query(User.role, func.count(User.id)).group_by(User.role).all())
    report_times = [r[0] for r in db.query(Report.created_at).filter(Report.created_at >= fortnight_ago)]
    signup_times = [u[0] for u in db.query(User.created_at).filter(User.created_at >= fortnight_ago)]

    def by_day(times: list[datetime]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for t in times:
            key = t.astimezone(IST).date().isoformat()
            counts[key] = counts.get(key, 0) + 1
        return counts

    analyses, signups = by_day(report_times), by_day(signup_times)
    today = now.astimezone(IST).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    return StatsOut(
        users_total=sum(by_role.values()),
        users_by_role={role: by_role.get(role, 0) for role in ROLES},
        users_disabled=db.query(User).filter(User.status == STATUS_DISABLED).count(),
        reports_total=db.query(Report).count(),
        reports_last_7_days=sum(1 for t in report_times if t >= week_ago),
        signups_last_7_days=sum(1 for t in signup_times if t >= week_ago),
        daily=[DailyCount(date=d, analyses=analyses.get(d, 0), signups=signups.get(d, 0)) for d in days],
    )


# ------------------------------------------------------------------ users

@router.get("/users", response_model=AdminUserPage)
def list_users(q: str = Query("", max_length=100), role: Optional[str] = Query(None),
               status: Optional[str] = Query(None), page: int = Query(1, ge=1),
               page_size: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    query = db.query(User)
    if q.strip():
        needle = q.strip().lower()
        query = query.filter(or_(func.lower(User.email).contains(needle, autoescape=True),
                                 func.lower(User.name).contains(needle, autoescape=True)))
    if role in ROLES:
        query = query.filter(User.role == role)
    if status in (STATUS_ACTIVE, STATUS_DISABLED):
        query = query.filter(User.status == status)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    counts = _report_counts(db, [u.id for u in users])
    return AdminUserPage(items=[_user_out(db, actor, u, counts.get(u.id, 0)) for u in users],
                         total=total, page=page, page_size=page_size)


@router.get("/users/{user_id}", response_model=AdminUserOut)
def get_user(user_id: str, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found.")
    return _user_out(db, actor, user)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(user_id: str, body: AdminUpdateUserRequest, request: Request,
                db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    target = _managed_user(db, actor, user_id)
    changed: list[str] = []
    if body.name is not None and body.name != target.name:
        target.name = body.name
        changed.append("name")
    if body.email is not None:
        email = normalize_email(body.email)
        if email != target.email:
            if db.query(User).filter(User.email == email, User.id != target.id).first():
                raise HTTPException(409, "Another account already uses this email.")
            target.email = email
            changed.append("email")
    if changed:
        audit(db, request, "user.updated", actor=actor, target=target, details={"fields": changed})
    if body.status is not None and body.status != target.status:
        target.status = body.status
        if body.status == STATUS_DISABLED:
            revoke_sessions(db, target.id)
        audit(db, request, f"user.{'disabled' if body.status == STATUS_DISABLED else 'enabled'}",
              actor=actor, target=target)
    db.commit()
    return _user_out(db, actor, target)


@router.post("/users/{user_id}/unlock", response_model=AdminUserOut)
def unlock_user(user_id: str, request: Request, db: Session = Depends(get_db),
                actor: User = Depends(require_admin)):
    target = _managed_user(db, actor, user_id)
    target.failed_logins = 0
    target.locked_until = None
    audit(db, request, "user.unlocked", actor=actor, target=target)
    db.commit()
    return _user_out(db, actor, target)


@router.post("/users/{user_id}/sign-out", response_model=AdminUserOut)
def sign_out_user(user_id: str, request: Request, db: Session = Depends(get_db),
                  actor: User = Depends(require_admin)):
    target = _managed_user(db, actor, user_id)
    revoke_sessions(db, target.id)
    audit(db, request, "user.signed_out", actor=actor, target=target)
    db.commit()
    return _user_out(db, actor, target)


@router.post("/users/{user_id}/reset-link", response_model=LinkCreated)
def create_reset_link(user_id: str, request: Request, db: Session = Depends(get_db),
                      actor: User = Depends(require_admin)):
    target = _managed_user(db, actor, user_id)
    revoke_pending_links(db, kind=LINK_RESET, user_id=target.id)
    link, token = issue_link(db, kind=LINK_RESET, email=target.email, user_id=target.id, created_by=actor)
    audit(db, request, "reset.created", actor=actor, target=target)
    db.commit()
    return LinkCreated(path=link_path(LINK_RESET, token), expires_at=link.expires_at)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, request: Request, db: Session = Depends(get_db),
                actor: User = Depends(require_admin)):
    target = _managed_user(db, actor, user_id)
    audit(db, request, "user.deleted", actor=actor, target=target, details={"role": target.role})
    db.delete(target)
    db.commit()


# ------------------------------------------------------------------ admin access (owner only)

@router.post("/access", response_model=AddAdminResult)
def add_admin(body: AddAdminRequest, request: Request, db: Session = Depends(get_db),
              actor: User = Depends(require_owner)):
    _confirm_password(actor, body.password)
    email = normalize_email(body.email)
    existing = db.query(User).filter_by(email=email).first()
    if existing is not None:
        if existing.role == ROLE_OWNER:
            raise HTTPException(409, "That's the owner account.")
        if existing.role == ROLE_ADMIN:
            raise HTTPException(409, "This person is already an admin.")
        existing.role = ROLE_ADMIN
        revoke_pending_links(db, kind=LINK_INVITE, email=email)
        audit(db, request, "role.promoted", actor=actor, target=existing, details={"role": ROLE_ADMIN})
        db.commit()
        return AddAdminResult(action="promoted", user=_user_out(db, actor, existing))

    revoke_pending_links(db, kind=LINK_INVITE, email=email)
    link, token = issue_link(db, kind=LINK_INVITE, email=email, role=ROLE_ADMIN, created_by=actor)
    audit(db, request, "invite.created", actor=actor, target_type="invite", target_email=email,
          details={"role": ROLE_ADMIN})
    db.commit()
    return AddAdminResult(action="invited", invite=_invite_out(db, link), path=link_path(LINK_INVITE, token))


@router.delete("/access/{user_id}", response_model=AdminUserOut)
def remove_admin(user_id: str, request: Request, db: Session = Depends(get_db),
                 actor: User = Depends(require_owner)):
    target = _managed_user(db, actor, user_id)
    if target.role != ROLE_ADMIN:
        raise HTTPException(400, "This person is not an admin.")
    target.role = ROLE_USER
    audit(db, request, "role.demoted", actor=actor, target=target, details={"role": ROLE_USER})
    db.commit()
    return _user_out(db, actor, target)


@router.post("/transfer-ownership", response_model=UserOut)
def transfer_ownership(body: TransferOwnershipRequest, request: Request, db: Session = Depends(get_db),
                       actor: User = Depends(require_owner)):
    _confirm_password(actor, body.password)
    target = db.get(User, body.user_id)
    if target is None or target.role != ROLE_ADMIN or target.status != STATUS_ACTIVE:
        raise HTTPException(400, "Ownership can only be transferred to an active admin.")
    # Demote first so the single-owner rule in the database is never violated.
    actor.role = ROLE_ADMIN
    db.flush()
    target.role = ROLE_OWNER
    audit(db, request, "owner.transferred", actor=actor, target=target)
    db.commit()
    return actor


# ------------------------------------------------------------------ invites

@router.post("/invites", response_model=InviteCreated, status_code=201)
def create_invite(body: InviteCreateRequest, request: Request, db: Session = Depends(get_db),
                  actor: User = Depends(require_admin)):
    _check_invite_role(actor, body.role)
    email = normalize_email(body.email)
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "This email already has an account.")
    revoke_pending_links(db, kind=LINK_INVITE, email=email)
    link, token = issue_link(db, kind=LINK_INVITE, email=email, role=body.role, created_by=actor)
    audit(db, request, "invite.created", actor=actor, target_type="invite", target_email=email,
          details={"role": body.role})
    db.commit()
    return InviteCreated(invite=_invite_out(db, link), path=link_path(LINK_INVITE, token))


@router.get("/invites", response_model=list[InviteOut])
def list_invites(role: Optional[str] = Query(None), include_closed: bool = Query(False),
                 db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    query = db.query(AccessLink).filter(AccessLink.kind == LINK_INVITE)
    if actor.role != ROLE_OWNER:
        query = query.filter(AccessLink.role == ROLE_USER)
    elif role in (ROLE_USER, ROLE_ADMIN):
        query = query.filter(AccessLink.role == role)
    invites = [_invite_out(db, link) for link in query.order_by(AccessLink.created_at.desc()).limit(100)]
    return invites if include_closed else [i for i in invites if i.status in ("pending", "expired")]


def _invite_for(db: Session, actor: User, invite_id: str) -> AccessLink:
    link = db.get(AccessLink, invite_id)
    if link is None or link.kind != LINK_INVITE:
        raise HTTPException(404, "Invite not found.")
    _check_invite_role(actor, link.role)
    if link.used_at is not None:
        raise HTTPException(400, "This invite has already been accepted.")
    return link


@router.post("/invites/{invite_id}/renew", response_model=InviteCreated)
def renew_invite(invite_id: str, request: Request, db: Session = Depends(get_db),
                 actor: User = Depends(require_admin)):
    link = _invite_for(db, actor, invite_id)
    if db.query(User).filter_by(email=link.email).first():
        raise HTTPException(409, "This email already has an account.")
    token = renew_link(link)
    audit(db, request, "invite.renewed", actor=actor, target_type="invite", target_email=link.email,
          details={"role": link.role})
    db.commit()
    return InviteCreated(invite=_invite_out(db, link), path=link_path(LINK_INVITE, token))


@router.delete("/invites/{invite_id}", status_code=204)
def revoke_invite(invite_id: str, request: Request, db: Session = Depends(get_db),
                  actor: User = Depends(require_admin)):
    link = _invite_for(db, actor, invite_id)
    link.revoked_at = utcnow()
    audit(db, request, "invite.revoked", actor=actor, target_type="invite", target_email=link.email,
          details={"role": link.role})
    db.commit()


# ------------------------------------------------------------------ audit log

@router.get("/audit-logs", response_model=AuditPage)
def audit_logs(category: Optional[str] = Query(None, max_length=20), q: str = Query("", max_length=100),
               page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
               db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    query = db.query(AuditLog)
    if category:
        query = query.filter(AuditLog.action.startswith(f"{category}.", autoescape=True))
    if q.strip():
        needle = q.strip().lower()
        query = query.filter(or_(func.lower(AuditLog.actor_email).contains(needle, autoescape=True),
                                 func.lower(AuditLog.target_email).contains(needle, autoescape=True)))
    total = query.count()
    rows = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [AuditEntry(id=r.id, created_at=r.created_at, actor_email=r.actor_email, action=r.action,
                        target_type=r.target_type, target_email=r.target_email, ip=r.ip, details=r.details)
             for r in rows]
    return AuditPage(items=items, total=total, page=page, page_size=page_size)
