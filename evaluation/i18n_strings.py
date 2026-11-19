"""List every English string the analysis results can show, one per line, for translation.

Usage: python i18n_strings.py > backend/app/data/i18n/strings_en.txt
Translations live in hi.txt and te.txt, one line per English line in the same order; build_i18n.py joins them.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.engine.explanation_generator import BIOMARKER_CLINICAL_PROFILES  # noqa: E402
from app.engine.recommender import ABSORPTION_RULES, TAG_LABELS, TAG_NOTES  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "backend" / "app" / "data"
seen, out = set(), []


def add(text):
    if isinstance(text, str) and text.strip() and text not in seen:
        assert "\n" not in text, text
        seen.add(text)
        out.append(text)


for b in json.loads((DATA / "biomarkers.json").read_text())["biomarkers"]:
    for key in ("display_name", "category", "clinical_warning_message", "low_status_message"):
        add(b.get(key))
for f in json.loads((DATA / "foods.json").read_text())["foods"]:
    for key in ("name", "category", "serving_size", "tip"):
        add(f.get(key))
    for s in f.get("synergies", []):
        add(s)
for v in list(TAG_LABELS.values()) + list(TAG_NOTES.values()):
    add(v)
for rules in ABSORPTION_RULES.values():
    for s in rules.get("dos", []) + rules.get("donts", []):
        add(s)
for p in BIOMARKER_CLINICAL_PROFILES.values():
    for key in ("role", "depletion_impact", "repletion_strategy"):
        add(p.get(key))
print("\n".join(out))
