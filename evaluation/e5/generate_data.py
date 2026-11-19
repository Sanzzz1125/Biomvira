"""Build the training and test data for the multilingual-e5-small fine-tune (run once; output in evaluation/e5/data).

Items come from NutriLens's own data: 278 dishes, 165 shopping ingredients, 187 recommended foods and the assistant's
FAQ. A language model (Groq, offline, our static data only) writes the other ways people type them: romanised Hindi
and Telugu, Hinglish, common misspellings, and the questions in Hindi, Telugu and Hinglish. 30% of the items are held
out as the test set: the model never sees them, or any phrase for them, in training.

Usage (repo root, GROQ_API_KEY in backend/.env):  python evaluation/e5/generate_data.py
"""
import json
import random
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import settings  # noqa: E402

OUT = Path(__file__).resolve().parent / "data"
MODEL = "openai/gpt-oss-120b"


def ask(prompt: str, model: str = MODEL) -> dict:
    extra = ({"reasoning_effort": "low", "include_reasoning": False} if "gpt-oss" in model
             else {"reasoning_effort": "none"})
    r = None
    for attempt in range(30):  # the free plan allows 8,000 tokens a minute: wait and retry
        r = httpx.post(settings.chat_llm_base_url + "/chat/completions", timeout=120,
                       headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                       json={"model": model, "temperature": 0.7, "response_format": {"type": "json_object"},
                             "messages": [{"role": "user", "content": prompt}], **extra})
        if r.status_code == 200:
            try:
                return json.loads(r.json()["choices"][0]["message"]["content"])
            except (ValueError, KeyError):
                pass
        wait = re.search(r"try again in ([\d.]+)s", r.text)
        time.sleep(min(90, float(wait.group(1)) + 1 if wait else 20))
    raise RuntimeError(f"no answer: {r.status_code} {r.text[:200]}")


def items() -> list[dict]:
    """Every item with the names NutriLens already knows (these become the search index)."""
    from app.engine.recommender import FOODS_DATABASE
    from app.plan.catalog import catalog
    from app.plan.ingredient_local import NAMES
    from app.plan.ingredient_names import INGREDIENTS
    from app.plan.nutrition import ingredients
    ifct = ingredients()
    out = []
    dishes = catalog()
    for d in (dishes.values() if isinstance(dishes, dict) else dishes):
        names = {d["name"], *d.get("also_called", []), *d.get("names", {}).values()}
        out.append({"id": f"dish:{d['id']}", "kind": "dish", "primary": d["name"], "names": sorted(n for n in names if n)})
    for name, (codes, _check) in INGREDIENTS.items():
        names = {name, *NAMES.get(name, ())}
        for code in codes if isinstance(codes, (list, tuple, set)) else [codes]:
            food = ifct.get(code) or {}
            names |= {v for k, v in (food.get("names") or {}).items() if k in ("hi", "te")}
        out.append({"id": f"ingredient:{name}", "kind": "ingredient", "primary": name, "names": sorted(n for n in names if n)})
    for f in FOODS_DATABASE:
        names = {f["name"], *(p.strip() for p in f["name"].split("/")), *(p.strip() for p in (f.get("hindi_name") or "").split("/"))}
        out.append({"id": f"food:{f['id']}", "kind": "food", "primary": f["name"].split("/")[0].strip(), "names": sorted(n for n in names if n)})
    return out


def variants(batch: list[dict]) -> dict:
    listing = "\n".join(f"{i['id']}: {' | '.join(i['names'][:4])}" for i in batch)
    return ask(
        "For each Indian food item below, write 6 OTHER ways real people in India type it in a chat or a diet list: "
        "romanised Hindi, romanised Telugu, Hinglish, Hindi in Devanagari, Telugu in Telugu script, and one common "
        "misspelling. Do not repeat the names given. Return JSON {\"<id>\": [\"...\", ...]}.\n\n" + listing)


def questions(batch: list[tuple[str, str]]) -> dict:
    listing = "\n".join(f"{qid}: {q}" for qid, q in batch)
    return ask(
        "Rewrite each question as a real Indian user would type it in a chat: once in Hindi (Devanagari), once in "
        "Telugu (Telugu script), once in Hinglish (romanised Hindi mixed with English), once in romanised Telugu, and "
        "once in casual English with different words. Keep the meaning exact. Return JSON "
        "{\"<id>\": [\"hindi\", \"telugu\", \"hinglish\", \"romanised telugu\", \"english\"]}.\n\n" + listing)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    random.seed(7)
    all_items = items()
    path = OUT / "name_variants.json"
    found = json.loads(path.read_text()) if path.exists() else {}
    todo = [i for i in all_items if i["id"] not in found]
    for start in range(0, len(todo), 20):
        batch = todo[start:start + 20]
        bare = {i["id"].split(":", 1)[1]: i["id"] for i in batch}  # some models drop the "dish:" prefix in keys
        for k, v in variants(batch).items():
            if isinstance(v, list) and (k in bare.values() or k in bare):
                found[k if k in bare.values() else bare[k]] = v
        path.write_text(json.dumps(found, ensure_ascii=False, indent=1))
        print("names", len(found), "/", len(all_items), flush=True)

    from app.chat.faq import FAQ
    faq = [(f"faq:{fid}:{n}", q) for fid, qs, _a, _f in FAQ for n, q in enumerate(qs[:3])]
    qpath = OUT / "question_variants.json"
    qfound = json.loads(qpath.read_text()) if qpath.exists() else {}
    todo = [x for x in faq if x[0] not in qfound]
    for start in range(0, len(todo), 15):
        qfound.update({k: v for k, v in questions(todo[start:start + 15]).items() if isinstance(v, list)})
        qpath.write_text(json.dumps(qfound, ensure_ascii=False, indent=1))
        print("questions", len(qfound), "/", len(faq), flush=True)

    # Split by item: test items (and every phrase for them) are never trained on.
    ids = [i["id"] for i in all_items]
    random.shuffle(ids)
    test_ids = set(ids[: int(len(ids) * 0.3)])
    faq_ids = sorted({fid for fid, *_ in FAQ})
    random.shuffle(faq_ids)
    test_faq = set(faq_ids[: int(len(faq_ids) * 0.3)])
    clean = lambda v: [s.strip() for s in v if isinstance(s, str) and 1 < len(s.strip()) <= 120]
    split = {"items": all_items, "test_items": sorted(test_ids), "test_faq": sorted(test_faq),
             "name_variants": {k: clean(v) for k, v in found.items()},
             "question_variants": {k: clean(v) for k, v in qfound.items()},
             "faq": [{"id": fid, "questions": qs} for fid, qs, _a, _f in FAQ]}
    (OUT / "dataset.json").write_text(json.dumps(split, ensure_ascii=False, indent=1))
    print("items", len(all_items), "test items", len(test_ids), "faq", len(faq_ids), "test faq", len(test_faq))


if __name__ == "__main__":
    main()
