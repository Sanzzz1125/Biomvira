"""Shared test setup. Every test gets its own empty in-memory database; tests never touch
the real (Neon or local) database, even when backend/.env defines DATABASE_URL."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AUTO_MIGRATE"] = "false"
os.environ["COOKIE_SECURE"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.ratelimit import limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.database import Base, get_db, make_engine  # noqa: E402
from app.models.entities import User  # noqa: E402

PASSWORD = "Nutri1ens!"


@pytest.fixture
def db_sessions():
    # Optional: TEST_DATABASE_URL=postgresql://... runs the suite against a disposable Postgres.
    # Never point it at a real database: every test wipes all tables.
    engine = make_engine(os.environ.get("TEST_DATABASE_URL", "sqlite://"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    limiter.reset()
    yield sessions
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


class Api:
    """A browser-like client: keeps cookies and echoes the CSRF cookie on unsafe requests."""

    def __init__(self) -> None:
        self.client = TestClient(app)

    def _headers(self, kwargs: dict) -> dict:
        headers = dict(kwargs.pop("headers", {}) or {})
        token = self.client.cookies.get("nl_csrf")
        if token and "X-CSRF-Token" not in headers:
            headers["X-CSRF-Token"] = token
        return headers

    def get(self, url, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url, **kwargs):
        return self.client.post(url, headers=self._headers(kwargs), **kwargs)

    def patch(self, url, **kwargs):
        return self.client.patch(url, headers=self._headers(kwargs), **kwargs)

    def delete(self, url, **kwargs):
        return self.client.delete(url, headers=self._headers(kwargs), **kwargs)

    def login(self, email: str, password: str = PASSWORD):
        return self.post("/api/v1/auth/login", json={"email": email, "password": password})


@pytest.fixture
def api(db_sessions):
    return Api


@pytest.fixture
def make_user(db_sessions):
    def _make(email: str, role: str = "user", name: str = "Test Person", status: str = "active") -> User:
        with db_sessions() as db:
            user = User(email=email, name=name, password_hash=hash_password(PASSWORD), role=role, status=status)
            db.add(user)
            db.commit()
            return user
    return _make


@pytest.fixture
def signed_in(api, make_user):
    """Create an account with the given role and return a client already logged in as it."""
    def _signed_in(email: str, role: str = "user") -> Api:
        make_user(email, role)
        client = api()
        assert client.login(email).status_code == 200
        return client
    return _signed_in
