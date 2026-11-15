"""Request and response bodies for auth, history and admin endpoints."""
from datetime import datetime
from typing import Annotated, Any, Literal, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

Role = Literal["user", "admin", "owner"]
Status = Literal["active", "disabled"]


def _clean_name(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise ValueError("Please enter your name.")
    return value


Name = Annotated[str, Field(min_length=1, max_length=80), AfterValidator(_clean_name)]


# ------------------------------------------------------------------ auth

class RegisterRequest(BaseModel):
    name: Name
    email: EmailStr
    password: str = Field(max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: Role
    status: Status
    created_at: datetime
    last_login_at: Optional[datetime] = None


class SessionOut(BaseModel):
    user: Optional[UserOut] = None


class UpdateProfileRequest(BaseModel):
    name: Name


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)


class PasswordConfirmRequest(BaseModel):
    password: str = Field(max_length=128)


class LinkInfo(BaseModel):
    kind: Literal["invite", "reset"]
    email: str
    role: Optional[Role] = None
    expires_at: datetime
    invited_by: Optional[str] = None


class AcceptInviteRequest(BaseModel):
    name: Name
    password: str = Field(max_length=128)


class ResetPasswordRequest(BaseModel):
    password: str = Field(max_length=128)


# ------------------------------------------------------------------ history

class HistoryMarker(BaseModel):
    biomarker_key: str
    display_name: str
    status: str
    value: float
    unit: str


class HistoryItem(BaseModel):
    id: str
    created_at: datetime
    status_summary: dict[str, int]
    marker_count: int
    requires_consult: bool
    markers: list[HistoryMarker]


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int


# ------------------------------------------------------------------ admin

class AdminUserOut(UserOut):
    report_count: int = 0
    locked: bool = False
    can_manage: bool = False


class AdminUserPage(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int


class AdminUpdateUserRequest(BaseModel):
    name: Optional[Name] = None
    email: Optional[EmailStr] = None
    status: Optional[Status] = None


class LinkCreated(BaseModel):
    path: str
    expires_at: datetime


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: Literal["user", "admin"] = "user"


class InviteOut(BaseModel):
    id: str
    email: str
    role: Optional[Role]
    status: Literal["pending", "accepted", "expired", "revoked"]
    created_at: datetime
    expires_at: datetime
    created_by: Optional[str] = None


class InviteCreated(BaseModel):
    invite: InviteOut
    path: str


class AddAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class AddAdminResult(BaseModel):
    action: Literal["promoted", "invited"]
    user: Optional[AdminUserOut] = None
    invite: Optional[InviteOut] = None
    path: Optional[str] = None


class TransferOwnershipRequest(BaseModel):
    user_id: str
    password: str = Field(max_length=128)


class DailyCount(BaseModel):
    date: str
    analyses: int
    signups: int


class StatsOut(BaseModel):
    users_total: int
    users_by_role: dict[str, int]
    users_disabled: int
    reports_total: int
    reports_last_7_days: int
    signups_last_7_days: int
    daily: list[DailyCount]


class AuditEntry(BaseModel):
    id: int
    created_at: datetime
    actor_email: Optional[str]
    action: str
    target_type: Optional[str]
    target_email: Optional[str]
    ip: Optional[str]
    details: Optional[dict[str, Any]]


class AuditPage(BaseModel):
    items: list[AuditEntry]
    total: int
    page: int
    page_size: int
