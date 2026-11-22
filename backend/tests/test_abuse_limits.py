"""Limits against abuse: per-visitor limits on uploads, analysis and plans; site-wide caps that a faked
X-Forwarded-For cannot dodge; API docs off in production; OCR one report at a time."""
import asyncio

import pytest

from app.chat import llm
from app.core.ratelimit import limiter, site_wide


def test_upload_limit_per_visitor(api):
    client = api()
    codes = [client.post("/api/v1/extract-report", data={"raw_text": "Vitamin D 12 ng/mL 30-100"}).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10 and codes[10] == 429


def test_plan_limit_per_visitor(api):
    client = api()
    body = {"words": ["peanut"]}
    codes = [client.post("/api/v1/diet-plan/allergy-check", json=body).status_code for _ in range(31)]
    assert codes[-1] == 429 and codes[:30].count(200) == 30


def test_signups_capped_site_wide_even_with_faked_ips(api):
    from tests.conftest import PASSWORD
    for i in range(31):
        r = api().post("/api/v1/auth/register", headers={"X-Forwarded-For": f"10.0.0.{i}"},
                       json={"name": "N", "email": f"u{i}@example.com", "password": PASSWORD})
    assert r.status_code == 429


def test_language_model_calls_capped_site_wide(monkeypatch):
    for _ in range(25):
        assert site_wide("llm", 25, 60)
    monkeypatch.setattr(llm.settings, "groq_api_key", "test-only")
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: pytest.fail("no call past the cap"))
    assert llm._complete([{"role": "user", "content": "hi"}]) is None


def test_docs_can_be_turned_off(monkeypatch):
    import importlib
    from app import config, main
    monkeypatch.setattr(config.settings, "api_docs", False)
    reloaded = importlib.reload(main)
    try:
        assert reloaded.app.docs_url is None and reloaded.app.openapi_url is None
    finally:
        monkeypatch.setattr(config.settings, "api_docs", True)
        importlib.reload(main)


def test_second_upload_waits_for_the_slot_instead_of_failing():
    from app.api.v1 import extract

    async def scenario():
        order = []

        async def job(name, hold):
            async with extract.report_slot(wait_seconds=5):
                order.append(name)
                await asyncio.sleep(hold)
        await asyncio.gather(job("first", 0.2), job("second", 0))
        return order
    assert asyncio.run(scenario()) == ["first", "second"]
