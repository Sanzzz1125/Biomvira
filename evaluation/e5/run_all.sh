#!/bin/sh
# Re-run the whole e5 pipeline and its tests: check phrases -> train -> compress -> held-out accuracy -> app tests.
# Usage (repo root): sh evaluation/e5/run_all.sh <python with torch + sentence-transformers>   (about 15-30 minutes)
set -e
PY=${1:-python3}
OUT=${TMPDIR:-/tmp}/biomvira-e5
.venv/bin/python evaluation/e5/check_variants.py
$PY evaluation/e5/train.py "$OUT"
$PY evaluation/e5/compress.py "$OUT"
cd backend && DATABASE_URL=sqlite:// ../.venv/bin/python -m pytest -q tests/test_e5.py tests/test_plan_engine.py tests/test_chatbot.py
echo "Accuracy report: backend/app/nlp/e5/report.json"
