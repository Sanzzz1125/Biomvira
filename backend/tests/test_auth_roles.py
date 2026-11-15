"""Authentication, sessions, roles (guest/user/admin/owner), ownership and audit logging."""
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.database import utcnow
from app.models.entities import AccessLink, AuditLog, Report, User, UserSession
from tests.conftest import PASSWORD

ANALYSIS = {
    "user_profile": {"age": 30, "gender": "female", "diet_type": "veg", "allergens": []},
    "biomarkers": [{"biomarker_key": "vitamin_d", "value": 12.5, "unit": "ng/mL"}],
}


def actions(db_sessions) -> list[str]:
    with db_sessions() as db:
        return [a for (a,) in db.query(AuditLog.action).order_by(AuditLog.id)]


# ------------------------------------------------------------------ sign-up & login

def test_register_logs_in_and_rejects_duplicates_and_weak_passwords(api):
    client = api()
    response = client.post("/api/v1/auth/register",
                           json={"name": "  Asha  Rao ", "email": "Asha@Example.com", "password": PASSWORD})
    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert response.json()["email"] == "asha@example.com"
    assert response.json()["name"] == "Asha Rao"
    assert "password_hash" not in response.text
    assert client.get("/api/v1/auth/me").json()["email"] == "asha@example.com"

    again = api().post("/api/v1/auth/register", json={"name": "A", "email": "asha@example.com", "password": PASSWORD})
    assert again.status_code == 409
    for weak in ("short1", "lettersonly", "12345678"):
        bad = api().post("/api/v1/auth/register", json={"name": "B", "email": "b@example.com", "password": weak})
        assert bad.status_code == 422


def test_session_cookie_is_http_only_and_csrf_cookie_is_readable(api, make_user):
    make_user("cookie@example.com")
    response = api().login("cookie@example.com")
    cookies = "\n".join(response.headers.get_list("set-cookie"))
    session_line = next(line for line in cookies.split("\n") if line.startswith("nl_session="))
    csrf_line = next(line for line in cookies.split("\n") if line.startswith("nl_csrf="))
    assert "HttpOnly" in session_line and "SameSite=lax" in session_line
    assert "HttpOnly" not in csrf_line


def test_login_errors_are_generic_and_lockout_after_five_failures(api, make_user, db_sessions):
    make_user("lock@example.com")
    client = api()
    unknown = client.login("nobody@example.com", "Wrong1234")
    wrong = client.login("lock@example.com", "Wrong1234")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json() == {"detail": "Invalid email or password."}
    for _ in range(4):
        client.login("lock@example.com", "Wrong1234")
    locked = client.login("lock@example.com")  # correct password, but locked
    assert locked.status_code == 429
    assert "auth.locked" in actions(db_sessions)
    with db_sessions() as db:
        user = db.query(User).filter_by(email="lock@example.com").one()
        user.locked_until = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.login("lock@example.com").status_code == 200


def test_session_endpoint_is_quiet_for_guests(api, signed_in):
    assert api().get("/api/v1/auth/session").json() == {"user": None}
    client = signed_in("someone@example.com")
    assert client.get("/api/v1/auth/session").json()["user"]["email"] == "someone@example.com"


def test_logout_ends_the_session(signed_in):
    client = signed_in("bye@example.com")
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_signed_in_changes_require_the_csrf_header(signed_in):
    client = signed_in("csrf@example.com")
    blocked = client.client.post("/api/v1/auth/logout")  # raw client: no CSRF header
    assert blocked.status_code == 403
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_change_password_signs_out_other_devices(api, signed_in):
    laptop = signed_in("pw@example.com")
    phone = api()
    assert phone.login("pw@example.com").status_code == 200
    bad = laptop.post("/api/v1/auth/change-password", json={"current_password": "nope", "new_password": "NewPass123"})
    assert bad.status_code == 400
    ok = laptop.post("/api/v1/auth/change-password", json={"current_password": PASSWORD, "new_password": "NewPass123"})
    assert ok.status_code == 200
    assert laptop.get("/api/v1/auth/me").status_code == 200
    assert phone.get("/api/v1/auth/me").status_code == 401
    assert api().login("pw@example.com", "NewPass123").status_code == 200


# ------------------------------------------------------------------ history ownership

def test_guests_can_analyze_but_nothing_is_saved(api, db_sessions):
    guest = api()
    response = guest.post("/api/v1/analyze-and-recommend", json=ANALYSIS)
    assert response.status_code == 200
    assert response.json()["saved_to_history"] is False
    assert guest.get("/api/v1/history").status_code == 401
    with db_sessions() as db:
        assert db.query(Report).count() == 0


def test_every_role_can_analyze_and_only_sees_its_own_reports(signed_in):
    clients = {role: signed_in(f"{role}@example.com", role) for role in ("user", "admin", "owner")}
    ids = {}
    for role, client in clients.items():
        result = client.post("/api/v1/analyze-and-recommend", json=ANALYSIS)
        assert result.status_code == 200 and result.json()["saved_to_history"] is True
        ids[role] = result.json()["analysis_id"]
        page = client.get("/api/v1/history").json()
        assert [item["id"] for item in page["items"]] == [ids[role]]
        assert page["items"][0]["markers"][0]["status"] == "low"
        assert client.get(f"/api/v1/history/{ids[role]}").json()["analysis_id"] == ids[role]
    # Nobody, including the owner, can open or delete someone else's report.
    for role, client in clients.items():
        for other, report_id in ids.items():
            if other != role:
                assert client.get(f"/api/v1/history/{report_id}").status_code == 404
                assert client.delete(f"/api/v1/history/{report_id}").status_code == 404
    assert clients["user"].delete(f"/api/v1/history/{ids['user']}").status_code == 204
    assert clients["user"].get("/api/v1/history").json()["total"] == 0


def test_deleting_an_account_deletes_its_reports(signed_in, db_sessions):
    client = signed_in("leaving@example.com")
    client.post("/api/v1/analyze-and-recommend", json=ANALYSIS)
    assert client.post("/api/v1/auth/delete-account", json={"password": "wrong"}).status_code == 400
    assert client.post("/api/v1/auth/delete-account", json={"password": PASSWORD}).status_code == 204
    with db_sessions() as db:
        assert db.query(User).count() == 0
        assert db.query(Report).count() == 0
        assert db.query(UserSession).count() == 0


# ------------------------------------------------------------------ role boundaries

ADMIN_ROUTES = [
    ("get", "/api/v1/admin/stats"), ("get", "/api/v1/admin/users"), ("get", "/api/v1/admin/audit-logs"),
    ("get", "/api/v1/admin/invites"), ("post", "/api/v1/admin/invites"),
]
OWNER_ROUTES = [("post", "/api/v1/admin/access"), ("delete", "/api/v1/admin/access/x"),
                ("post", "/api/v1/admin/transfer-ownership")]


@pytest.mark.parametrize("method,path", ADMIN_ROUTES + OWNER_ROUTES)
def test_guests_get_401_and_users_get_403_on_admin_routes(api, signed_in, method, path):
    assert getattr(api(), method)(path).status_code == 401
    assert getattr(signed_in("plain@example.com"), method)(path).status_code == 403


@pytest.mark.parametrize("method,path", OWNER_ROUTES)
def test_admins_get_403_on_owner_routes(signed_in, method, path):
    assert getattr(signed_in("adm@example.com", "admin"), method)(path).status_code == 403


def test_admin_manages_users_but_not_admins_or_the_owner(api, signed_in, make_user):
    admin = signed_in("boss@example.com", "admin")
    user = make_user("member@example.com")
    other_admin = make_user("peer@example.com", "admin")
    owner = make_user("owner@example.com", "owner")
    victim = api()
    assert victim.login("member@example.com").status_code == 200

    disabled = admin.patch(f"/api/v1/admin/users/{user.id}", json={"status": "disabled"})
    assert disabled.status_code == 200 and disabled.json()["status"] == "disabled"
    assert victim.get("/api/v1/auth/me").status_code == 401          # signed out immediately
    assert api().login("member@example.com").status_code == 403      # cannot sign back in
    assert admin.patch(f"/api/v1/admin/users/{user.id}", json={"status": "active"}).status_code == 200

    for target in (other_admin, owner):
        assert admin.patch(f"/api/v1/admin/users/{target.id}", json={"name": "Hacked"}).status_code == 403
        assert admin.delete(f"/api/v1/admin/users/{target.id}").status_code == 403
        assert admin.post(f"/api/v1/admin/users/{target.id}/reset-link").status_code == 403
    me = admin.get("/api/v1/auth/me").json()
    assert admin.patch(f"/api/v1/admin/users/{me['id']}", json={"status": "disabled"}).status_code == 403
    assert admin.post("/api/v1/admin/invites", json={"email": "x@example.com", "role": "admin"}).status_code == 403
    listed = {u["email"]: u["can_manage"] for u in admin.get("/api/v1/admin/users").json()["items"]}
    assert listed == {"member@example.com": True, "peer@example.com": False, "owner@example.com": False,
                      "boss@example.com": False}


# ------------------------------------------------------------------ owner powers

def test_only_one_owner_can_ever_exist(make_user):
    make_user("first@example.com", "owner")
    with pytest.raises(IntegrityError):
        make_user("second@example.com", "owner")


def test_owner_promotes_existing_user_and_removes_admin(signed_in, api, make_user, db_sessions):
    owner = signed_in("owner@example.com", "owner")
    member = make_user("member@example.com")
    assert owner.post("/api/v1/admin/access", json={"email": "member@example.com", "password": "bad"}).status_code == 400
    promoted = owner.post("/api/v1/admin/access", json={"email": "Member@Example.com", "password": PASSWORD})
    assert promoted.status_code == 200 and promoted.json()["action"] == "promoted"
    new_admin = api()
    new_admin.login("member@example.com")
    assert new_admin.get("/api/v1/admin/stats").status_code == 200
    assert owner.delete(f"/api/v1/admin/access/{member.id}").status_code == 200
    assert new_admin.get("/api/v1/admin/stats").status_code == 403   # takes effect immediately
    assert {"role.promoted", "role.demoted"} <= set(actions(db_sessions))


def test_owner_invites_a_new_admin_by_one_time_link(signed_in, api, db_sessions):
    owner = signed_in("owner@example.com", "owner")
    invited = owner.post("/api/v1/admin/access", json={"email": "new.admin@example.com", "password": PASSWORD})
    assert invited.status_code == 200 and invited.json()["action"] == "invited"
    token = invited.json()["path"].rsplit("/", 1)[1]
    info = api().get(f"/api/v1/auth/invites/{token}").json()
    assert info["email"] == "new.admin@example.com" and info["role"] == "admin"

    newcomer = api()
    accepted = newcomer.post(f"/api/v1/auth/invites/{token}/accept", json={"name": "New Admin", "password": PASSWORD})
    assert accepted.status_code == 201 and accepted.json()["role"] == "admin"
    assert newcomer.get("/api/v1/admin/stats").status_code == 200
    # Single use: the same link can't create a second account.
    assert api().post(f"/api/v1/auth/invites/{token}/accept", json={"name": "X", "password": PASSWORD}).status_code == 404
    with db_sessions() as db:
        assert db.query(AccessLink).filter_by(email="new.admin@example.com").one().token_hash != token


def test_invites_expire_and_can_be_revoked_or_renewed(signed_in, api, db_sessions):
    admin = signed_in("adm@example.com", "admin")
    created = admin.post("/api/v1/admin/invites", json={"email": "friend@example.com"}).json()
    token, invite_id = created["path"].rsplit("/", 1)[1], created["invite"]["id"]
    assert [i["email"] for i in admin.get("/api/v1/admin/invites").json()] == ["friend@example.com"]
    with db_sessions() as db:
        db.get(AccessLink, invite_id).expires_at = utcnow() - timedelta(minutes=1)
        db.commit()
    assert api().get(f"/api/v1/auth/invites/{token}").status_code == 404
    renewed = admin.post(f"/api/v1/admin/invites/{invite_id}/renew").json()
    new_token = renewed["path"].rsplit("/", 1)[1]
    assert api().get(f"/api/v1/auth/invites/{token}").status_code == 404      # old link stays dead
    assert api().get(f"/api/v1/auth/invites/{new_token}").status_code == 200
    assert admin.delete(f"/api/v1/admin/invites/{invite_id}").status_code == 204
    assert api().get(f"/api/v1/auth/invites/{new_token}").status_code == 404


def test_owner_edits_admin_details_and_issues_reset_link(signed_in, api, make_user):
    owner = signed_in("owner@example.com", "owner")
    admin = make_user("adm@example.com", "admin")
    admin_client = api()
    admin_client.login("adm@example.com")
    edited = owner.patch(f"/api/v1/admin/users/{admin.id}", json={"name": "Renamed", "email": "adm2@example.com"})
    assert edited.status_code == 200 and edited.json()["email"] == "adm2@example.com"
    path = owner.post(f"/api/v1/admin/users/{admin.id}/reset-link").json()["path"]
    token = path.rsplit("/", 1)[1]
    assert api().get(f"/api/v1/auth/reset/{token}").json()["email"] == "adm2@example.com"
    reset = api().post(f"/api/v1/auth/reset/{token}", json={"password": "Fresh1234"})
    assert reset.status_code == 200
    assert admin_client.get("/api/v1/auth/me").status_code == 401      # old sessions revoked
    assert api().login("adm2@example.com", "Fresh1234").status_code == 200
    assert api().post(f"/api/v1/auth/reset/{token}", json={"password": "Again1234"}).status_code == 404


def test_ownership_transfer_keeps_exactly_one_owner(signed_in, make_user, db_sessions):
    owner = signed_in("owner@example.com", "owner")
    admin = make_user("adm@example.com", "admin")
    user = make_user("member@example.com")
    body = {"user_id": user.id, "password": PASSWORD}
    assert owner.post("/api/v1/admin/transfer-ownership", json=body).status_code == 400    # not an admin
    body = {"user_id": admin.id, "password": "wrong"}
    assert owner.post("/api/v1/admin/transfer-ownership", json=body).status_code == 400
    body["password"] = PASSWORD
    assert owner.post("/api/v1/admin/transfer-ownership", json=body).json()["role"] == "admin"
    with db_sessions() as db:
        assert [u.email for u in db.query(User).filter_by(role="owner")] == ["adm@example.com"]
    assert owner.get("/api/v1/admin/stats").status_code == 200          # still an admin
    assert owner.post("/api/v1/admin/access", json={"email": "z@example.com", "password": PASSWORD}).status_code == 403


def test_owner_account_cannot_be_deleted_or_managed(signed_in, make_user):
    owner = signed_in("owner@example.com", "owner")
    assert owner.post("/api/v1/auth/delete-account", json={"password": PASSWORD}).status_code == 400
    me = owner.get("/api/v1/auth/me").json()
    assert owner.delete(f"/api/v1/admin/users/{me['id']}").status_code == 403


def test_stats_and_audit_log(signed_in, db_sessions):
    owner = signed_in("owner@example.com", "owner")
    owner.post("/api/v1/analyze-and-recommend", json=ANALYSIS)
    stats = owner.get("/api/v1/admin/stats").json()
    assert stats["users_total"] == 1 and stats["users_by_role"]["owner"] == 1
    assert stats["reports_total"] == 1 and len(stats["daily"]) == 14
    assert sum(day["analyses"] for day in stats["daily"]) == 1
    logs = owner.get("/api/v1/admin/audit-logs", params={"category": "auth"}).json()
    assert logs["items"][0]["action"] == "auth.login"
    assert logs["items"][0]["actor_email"] == "owner@example.com"


def test_cli_refuses_a_second_owner(make_user, db_sessions, monkeypatch):
    from app import cli
    monkeypatch.setattr(cli, "SessionLocal", db_sessions)
    monkeypatch.setattr(cli, "_ask_password", lambda: PASSWORD)
    assert cli.create_owner("first@example.com", "First") == 0
    assert cli.create_owner("second@example.com", "Second") == 1
    with db_sessions() as db:
        assert [u.email for u in db.query(User).filter_by(role="owner")] == ["first@example.com"]
