"""ORM models: accounts, sessions, access links, saved reports and the audit log."""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base, UTCDateTime, utcnow

JSONType = JSON().with_variant(JSONB(), "postgresql")

ROLE_USER, ROLE_ADMIN, ROLE_OWNER = "user", "admin", "owner"
ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_OWNER)
STATUS_ACTIVE, STATUS_DISABLED = "active", "disabled"
LINK_INVITE, LINK_RESET = "invite", "reset"


def new_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), default=ROLE_USER)
    status: Mapped[str] = mapped_column(String(10), default=STATUS_ACTIVE)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin', 'owner')", name="role"),
        CheckConstraint("status IN ('active', 'disabled')", name="status"),
        # The database itself guarantees there can never be more than one owner.
        Index("uq_users_single_owner", "role", unique=True,
              postgresql_where=text("role = 'owner'"), sqlite_where=text("role = 'owner'")),
    )

    @property
    def is_staff(self) -> bool:
        return self.role in (ROLE_ADMIN, ROLE_OWNER)

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class AccessLink(Base):
    """One-time invite and password-reset links. Only a hash of the token is stored."""

    __tablename__ = "access_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(10))
    email: Mapped[str] = mapped_column(String(254), index=True)
    role: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("kind IN ('invite', 'reset')", name="kind"),
    )

    def status(self, now: datetime) -> str:
        if self.used_at:
            return "accepted" if self.kind == LINK_INVITE else "used"
        if self.revoked_at:
            return "revoked"
        if self.expires_at <= now:
            return "expired"
        return "pending"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSONType)
    status_summary: Mapped[dict[str, Any]] = mapped_column(JSONType)
    marker_count: Mapped[int] = mapped_column(Integer, default=0)
    requires_consult: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ix_reports_owner_created", "owner_id", "created_at"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    target_email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONType, nullable=True)
