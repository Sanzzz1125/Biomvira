"""The e5 model: only the parts that met their agreed accuracy are live (see backend/app/nlp/e5/report.json)."""
import json
from pathlib import Path

import pytest

from app.chat.engine import answer
from app.nlp import embed

REPORT = json.loads((Path(embed.__file__).parent / "e5" / "report.json").read_text())
pytestmark = pytest.mark.skipif(not embed.available(), reason="e5 model files not present")


def test_live_flags_follow_measured_accuracy():
    assert REPORT["live"]["questions"] is True and REPORT["compressed_questions_english"] >= 0.95
    assert REPORT["live"]["names"] is False  # 85% < 95%: word matching is used for names
    assert embed.match_items("వేరుశనగ", "ingredient") == {}


def test_hindi_and_telugu_questions_are_understood():
    reply = answer("आयरन की कमी में क्या खाना चाहिए?")
    assert reply.topic != "non_english" and reply.kind in ("answer", "clarify")
    assert answer("నా ఆహార ప్రణాళికను ఎలా సేవ్ చేయాలి?").topic != "non_english"


def test_emergency_in_hindi_gets_the_safety_reply():
    assert answer("मुझे अभी सीने में बहुत तेज़ दर्द हो रहा है").kind == "safety"
