"""Hand-written assistant questions (typos, word forms, Hinglish): accuracy must not drop below what was measured.

chat_questions.txt was used while improving the matcher; chat_questions_holdout.txt never was, so it shows how the
assistant does on wording it has not seen. Safety and medicine questions must always be handled correctly.
"""
from pathlib import Path

import pytest

from app.chat.engine import answer
from app.nlp import embed

DATA = Path(__file__).parent / "data"


def rows(name):
    return [line.split(" | ", 1) for line in (DATA / name).read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]


def correct(expected: str, reply) -> bool:
    if "/" in expected:
        return any(correct(e, reply) for e in expected.split("/"))
    if expected.startswith("kind:"):
        return reply.kind == expected[5:]
    if expected.startswith("test:"):
        return (reply.topic or "") == expected
    return (reply.topic or "") == f"faq:{expected}"


@pytest.mark.parametrize("name, floor", [("chat_questions.txt", 0.95), ("chat_questions_holdout.txt", 0.80)])
def test_accuracy_floor(name, floor):
    if not embed.available():
        pytest.skip("e5 model files not present")
    data = rows(name)
    right = sum(correct(e, answer(q)) for e, q in data)
    assert right / len(data) >= floor, f"{name}: {right}/{len(data)}"


@pytest.mark.parametrize("expected, question", [r for n in ("chat_questions.txt", "chat_questions_holdout.txt")
                                                 for r in rows(n) if r[0].startswith("kind:")])
def test_safety_and_medicine_questions_always_right(expected, question):
    assert correct(expected, answer(question)), question
