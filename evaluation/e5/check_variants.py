"""Second pass over the generated phrases: keep only the ones that really mean the same food.

A phrase that names a different dish ("brown rice roti" for brown rice) or is not a real way of writing it would teach
the model wrong matches and make the test unfair, so each item's phrases are reviewed again and filtered. The number
kept and dropped is printed. Run after generate_data.py; it then rewrites dataset.json with the checked phrases.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_data as g  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"


def main() -> None:
    variants = json.loads((DATA / "name_variants.json").read_text())
    names = {i["id"]: i["names"] for i in g.items()}
    path = DATA / "name_variants_checked.json"
    checked = json.loads(path.read_text()) if path.exists() else {}
    todo = [k for k in variants if k not in checked and k in names]
    for start in range(0, len(todo), 15):
        batch = todo[start:start + 15]
        listing = "\n".join(f"{k} (known as: {' | '.join(names[k][:4])}): {json.dumps(variants[k], ensure_ascii=False)}"
                            for k in batch)
        answer = g.ask("You are checking Indian food names. For each item, keep ONLY the phrases that a person would use "
                       "to mean exactly this same food (spelling variants, transliterations, Hindi or Telugu names). "
                       "Remove phrases that name a different dish or ingredient, add another food, or are not real "
                       "usage. Return JSON {\"<id>\": [kept phrases]}.\n\n" + listing, model="qwen/qwen3.8-27b")
        for k in batch:
            kept = answer.get(k) or answer.get(k.split(":", 1)[1]) or []  # some models drop the "dish:" prefix
            checked[k] = [v for v in kept if isinstance(v, str) and v in variants[k]]
        path.write_text(json.dumps(checked, ensure_ascii=False, indent=1))
    before = sum(len(v) for v in variants.values())
    after = sum(len(v) for v in checked.values())
    print(f"phrases kept {after} of {before}")
    data = json.loads((DATA / "dataset.json").read_text())
    data["name_variants"] = {k: [s.strip() for s in v if 1 < len(s.strip()) <= 120] for k, v in checked.items()}
    (DATA / "dataset.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
