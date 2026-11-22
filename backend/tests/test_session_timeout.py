"""Sign-ins end after 2 hours without use and after 1 day at most; use within the 2 hours keeps them going."""
from datetime import timedelta

from app.models.database import utcnow
from app.models.entities import UserSession


def _shift(db_sessions, **delta):
    """Move every session into the past, as if that much time had gone by."""
    with db_sessions() as db:
        for s in db.query(UserSession).all():
            s.created_at -= timedelta(**delta)
            s.expires_at -= timedelta(**delta)
        db.commit()


def test_new_session_ends_two_hours_after_last_use(signed_in, db_sessions):
    client = signed_in("asha@example.com")
    with db_sessions() as db:
        s = db.query(UserSession).one()
        assert timedelta(minutes=115) < s.expires_at - utcnow() <= timedelta(minutes=120)
    _shift(db_sessions, minutes=121)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_use_within_two_hours_keeps_the_session(signed_in, db_sessions):
    client = signed_in("asha@example.com")
    for _ in range(3):  # used every 90 minutes for 4.5 hours
        _shift(db_sessions, minutes=90)
        assert client.get("/api/v1/auth/me").status_code == 200


def test_session_ends_after_one_day_even_when_used(signed_in, db_sessions):
    client = signed_in("asha@example.com")
    for _ in range(16):  # used every 90 minutes for 24 hours
        _shift(db_sessions, minutes=90)
        client.get("/api/v1/auth/me")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_old_seven_day_sessions_are_cut_to_one_day(signed_in, db_sessions):
    client = signed_in("asha@example.com")
    with db_sessions() as db:  # a session from before this change: started 2 days ago, valid for 7 days
        s = db.query(UserSession).one()
        s.created_at = utcnow() - timedelta(days=2)
        s.expires_at = utcnow() + timedelta(days=5)
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_cookie_lasts_one_day(api, make_user):
    make_user("asha@example.com")
    response = api().login("asha@example.com")
    cookie = response.headers.get("set-cookie", "")
    assert "Max-Age=86400" in cookie and "HttpOnly" in cookie
