"""Production-like test of the compressed e5 model, on items it never trained on.

The site's index holds every real name we know, so the agreed target is about UNSEEN PHRASES: for each held-out item
one real name (IFCT regional name, Hindi/Telugu name or other name) is hidden from the index and used as the query,
plus typos of its English name. A strict threshold is chosen so that wrong matches stay at or below 2%; below it the
model answers "no match" (callers then keep word matching). Non-foods are checked against the same threshold.

Usage:  python evaluation/e5/evaluate.py      (writes the thresholds into backend/app/nlp/e5/report.json)
"""
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train  # noqa: E402
from compress import OUT, Onnx  # noqa: E402


def main() -> None:
    model = Onnx(OUT)
    rng = random.Random(5)
    test = set(train.DATA["test_items"])
    index, queries = [], []
    for item in train.DATA["items"]:
        names = sorted({train.norm(n) for n in item["names"]} | {train.norm(item["primary"])})
        if item["id"] in test and len(names) > 1:
            hidden = rng.choice([n for n in names if n != train.norm(item["primary"])])
            queries.append((hidden, item["id"]))
            queries += [(t, item["id"]) for t in train.typos(train.norm(item["primary"]), rng)]
            names = [n for n in names if n != hidden]
        index += [(n, item["id"]) for n in names]
    emb = model.encode([f"query: {t}" for t, _ in index])
    q = model.encode([f"query: {t}" for t, _ in queries])
    sims = q @ emb.T
    # As on the site, a query only searches its own kind (dishes, ingredients or foods).
    kind = np.array([i.split(":")[0] for _, i in index])
    for row, (_, label) in enumerate(queries):
        sims[row, kind != label.split(":")[0]] = -1
    best, score = sims.argmax(1), sims.max(1)
    # A name that ICMR-NIN gives to several foods (e.g. "rajmah" for black, brown and red rajma) is right for any of them.
    all_names = {i["id"]: {train.norm(n) for n in i["names"]} | {train.norm(i["primary"])} for i in train.DATA["items"]}
    right = np.array([index[b][1] == label or text in all_names[index[b][1]]
                      for b, (text, label) in zip(best, queries)])
    junk = model.encode([f"query: {t}" for t in train.NOT_FOOD])
    junk_score = (junk @ emb.T).max(1)

    rows = []
    for t in np.arange(0.70, 0.99, 0.005):
        taken = score >= t
        wrong = (taken & ~right).sum() / len(queries)
        rows.append((round(float(t), 3), float((taken & right).sum() / len(queries)), float(wrong),
                     float((junk_score >= t).mean())))
    print("t correct wrong nonfood"); [print(r) for r in rows[::4]]
    safe = next((r for r in rows if r[2] <= 0.02 and r[3] <= 0.05), rows[-1])
    by_script = {}
    for (text, _), ok, s in zip(queries, right, score):
        g = by_script.setdefault(train.script(text), [0, 0, 0])
        g[0] += 1
        g[1] += int(ok)
        g[2] += int(ok and s >= safe[0])
    result = {"queries": len(queries), "top1_accuracy": round(float(right.mean()), 3),
              "threshold": safe[0], "correct_at_threshold": round(safe[1], 3), "wrong_at_threshold": round(safe[2], 3),
              "non_food_matched_at_threshold": round(safe[3], 3),
              "by_script": {k: {"n": n, "top1": round(a / n, 3), "correct_at_threshold": round(c / n, 3)}
                            for k, (n, a, c) in by_script.items()}}
    report_path = OUT / "report.json"
    report = json.loads(report_path.read_text())
    report["unseen_phrase_test"] = result
    report["name_threshold"] = safe[0]  # strict: at most 2% wrong matches, at most 5% of non-foods matched
    report_path.write_text(json.dumps(report, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
