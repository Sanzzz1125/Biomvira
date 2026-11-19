"""Fine-tune multilingual-e5-small on NutriLens names and questions, and measure it on held-out items.

Accuracy is top-1: the right dish/ingredient/food (or FAQ entry) must be the closest of ALL known names, using only
phrases for items that were held out of training. Compared with the word matching used before and with the base model.

Usage:  python evaluation/e5/train.py <output folder>      (needs torch + sentence-transformers; data from generate_data.py)
"""
import json
import random
import sys
import unicodedata
from pathlib import Path

import numpy as np
from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

DATA = json.loads((Path(__file__).resolve().parent / "data" / "dataset.json").read_text())
BASE = "intfloat/multilingual-e5-small"
NOT_FOOD = ["pizza", "burger", "pasta with cheese", "sushi", "my phone number", "hello", "tablet", "paracetamol",
            "coca cola", "noodles maggi", "the weather today", "cricket", "car", "laptop", "doctor appointment",
            "मेरा नाम", "నా పేరు", "chocolate cake", "french fries", "wine", "beer", "cigarette", "gym", "running"]


def norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFC", s).lower().split())


def typos(name: str, rng: random.Random) -> list[str]:
    """Realistic slips of a real name: a dropped, swapped or doubled letter (Latin names of 5+ letters)."""
    if len(name) < 5 or not name.isascii():
        return []
    i = rng.randrange(1, len(name) - 1)
    return [name[:i] + name[i + 1:], name[:i] + name[i + 1] + name[i] + name[i + 2:], name[:i] + name[i] + name[i:]]


def name_sets():
    """Real names only (IFCT 2017 regional names, our checked Hindi/Telugu names, curated other names).
    Held-out items are in the index under their English name only; their other real names are the test phrases."""
    rng = random.Random(11)
    test = set(DATA["test_items"])
    index, queries = [], {"train": [], "test": []}
    for item in DATA["items"]:
        primary = norm(item["primary"])
        names = sorted({norm(n) for n in item["names"]} | {primary})
        if item["id"] in test:
            index.append((primary, item["id"]))
            queries["test"] += [(n, item["id"]) for n in names if n != primary]
            queries["test"] += [(t, item["id"]) for t in typos(primary, rng)]
        else:
            index += [(n, item["id"]) for n in names]
            queries["train"] += [(t, item["id"]) for n in names for t in typos(n, rng)]
    return index, queries


def question_sets():
    test = set(DATA["test_faq"])
    index = [(norm(q), f["id"]) for f in DATA["faq"] for q in f["questions"]]
    queries = {"train": [], "test": [], "test_english": []}
    for key, vs in DATA["question_variants"].items():
        fid = key.split(":")[1]
        for n, v in enumerate(vs):
            split = "train" if fid not in test else ("test_english" if n == 4 else "test")
            queries[split].append((norm(v), fid))
    return index, queries


def accuracy(model, index, queries, threshold=None):
    texts = [t for t, _ in index]
    emb = model.encode([f"query: {t}" for t in texts], batch_size=128, normalize_embeddings=True)
    q = model.encode([f"query: {t}" for t, _ in queries], batch_size=128, normalize_embeddings=True)
    sims = q @ emb.T
    best = sims.argmax(1)
    right = sum(index[b][1] == label for b, (_, label) in zip(best, queries))
    return right / max(len(queries), 1), sims.max(1)


def script(text: str) -> str:
    if any("\u0c00" <= c <= "\u0c7f" for c in text):
        return "telugu_script"
    if any("\u0900" <= c <= "\u097f" for c in text):
        return "hindi_script"
    return "latin"


def breakdown(model, index, queries) -> dict:
    """Accuracy per script and per item type, each with a 95% confidence interval (Wilson)."""
    texts = [t for t, _ in index]
    emb = model.encode([f"query: {t}" for t in texts], batch_size=128, normalize_embeddings=True)
    q = model.encode([f"query: {t}" for t, _ in queries], batch_size=128, normalize_embeddings=True)
    best = (q @ emb.T).argmax(1)
    groups = {}
    for b, (text, label) in zip(best, queries):
        ok = index[b][1] == label
        for g in (script(text), label.split(":")[0] if ":" in label else "faq", "all"):
            groups.setdefault(g, []).append(ok)
    out = {}
    for g, oks in groups.items():
        n, p = len(oks), sum(oks) / len(oks)
        z = 1.96
        centre = (p + z * z / (2 * n)) / (1 + z * z / n)
        half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
        out[g] = {"n": n, "accuracy": round(p, 3), "ci95": [round(centre - half, 3), round(centre + half, 3)]}
    return out


def word_matching(index, queries) -> float:
    """The method used before: a known name must appear in the text."""
    right = 0
    for text, label in queries:
        hits = [i for n, i in index if len(n) >= 4 and f" {n} " in f" {text} "]
        right += bool(hits) and hits[0] == label
    return right / max(len(queries), 1)


def main(out: Path) -> None:
    random.seed(7)
    names_index, names_q = name_sets()
    faq_index, faq_q = question_sets()
    print(f"index: {len(names_index)} names, {len(faq_index)} questions | test phrases: {len(names_q['test'])} names, "
          f"{len(faq_q['test'])} hi/te/Hinglish questions, {len(faq_q['test_english'])} English rewrites")
    base = SentenceTransformer(BASE, device="mps")
    report = {"word_matching_names": word_matching(names_index, names_q["test"])}
    report["base_names"] = accuracy(base, names_index, names_q["test"])[0]
    report["base_questions"] = accuracy(base, faq_index, faq_q["test"])[0]
    report["base_questions_english"] = accuracy(base, faq_index, faq_q["test_english"])[0]

    # Training pairs: a phrase -> one of its item's known names (other items in the batch are the negatives).
    by_item = {}
    for n, i in names_index:
        by_item.setdefault(i, []).append(n)
    by_faq = {}
    for q, f in faq_index:
        by_faq.setdefault(f, []).append(q)
    test_items, test_faq = set(DATA["test_items"]), set(DATA["test_faq"])
    pairs = []
    for text, item in names_q["train"]:
        pairs.append(InputExample(texts=[f"query: {text}", f"query: {random.choice(by_item[item])}"]))
    for item, names in by_item.items():
        if item not in test_items and len(names) > 1:
            pairs += [InputExample(texts=[f"query: {a}", f"query: {b}"]) for a in names for b in names if a != b][:6]
    for text, fid in faq_q["train"]:
        pairs.append(InputExample(texts=[f"query: {text}", f"query: {random.choice(by_faq[fid])}"]))
    for fid, qs in by_faq.items():
        if fid not in test_faq:
            pairs += [InputExample(texts=[f"query: {a}", f"query: {b}"]) for a in qs for b in qs if a != b][:6]
    random.shuffle(pairs)
    print("training pairs:", len(pairs))
    model = SentenceTransformer(BASE, device="mps")
    loader = DataLoader(pairs, shuffle=True, batch_size=64)
    model.fit(train_objectives=[(loader, losses.MultipleNegativesRankingLoss(model))], epochs=3, warmup_steps=50,
              optimizer_params={"lr": 3e-5}, show_progress_bar=False)
    model.save(str(out))

    report["tuned_names"], name_scores = accuracy(model, names_index, names_q["test"])
    report["tuned_questions"], faq_scores = accuracy(model, faq_index, faq_q["test"])
    report["tuned_questions_english"] = accuracy(model, faq_index, faq_q["test_english"])[0]
    # Threshold: the lowest similarity a real name match gets (5th percentile) vs. things that are not foods.
    junk = model.encode([f"query: {t}" for t in NOT_FOOD], normalize_embeddings=True)
    emb = model.encode([f"query: {t}" for t, _ in names_index], batch_size=128, normalize_embeddings=True)
    junk_best = (junk @ emb.T).max(1)
    report["name_threshold"] = float(np.percentile(name_scores, 5))
    report["non_food_above_threshold"] = float((junk_best >= report["name_threshold"]).mean())
    report["faq_threshold"] = float(np.percentile(faq_scores, 10))
    report["breakdown_names"] = breakdown(model, names_index, names_q["test"])
    report["breakdown_questions"] = breakdown(model, faq_index, faq_q["test"])
    report["test_counts"] = {"names": len(names_q["test"]), "questions": len(faq_q["test"]),
                             "questions_english": len(faq_q["test_english"])}
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
