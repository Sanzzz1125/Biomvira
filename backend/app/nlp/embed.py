"""multilingual-e5-small (MIT), fine-tuned on Biomvira data, for understanding food names and questions in English,
Hindi, Telugu and Hinglish.

Built offline by evaluation/e5/ (generate_data.py, train.py, compress.py): pruned to the vocabulary of the three
languages, exported to ONNX and quantised to 8 bits, so the server runs it with onnxruntime only (no PyTorch). Its
accuracy on held-out phrases and the match thresholds are in e5/report.json.

Used for:
  - the "what do you usually eat" text: which of our dishes the person already eats (plan engine);
  - custom allergies and dislikes: which ingredients they mean, in any of the three languages (plan engine);
  - the assistant: which FAQ entry or safety topic a question means, including Hindi, Telugu and Hinglish questions.
If the model files are missing or fail to load, every function returns no match and the callers keep their word matching.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)
FOLDER = Path(__file__).resolve().parent / "e5"


@lru_cache(maxsize=1)
def _model():
    try:
        import onnxruntime as ort
        import sentencepiece
        tok = sentencepiece.SentencePieceProcessor(model_file=str(FOLDER / "spm.model"))  # 40 MB in memory
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1  # small server: one thread, low memory
        options.enable_cpu_mem_arena = False
        sess = ort.InferenceSession(str(FOLDER / "model.onnx"), options, providers=["CPUExecutionProvider"])
        words = (np.load(FOLDER / "words_int8.npy", mmap_mode="r"), np.load(FOLDER / "words_scale.npy"))
        index = np.load(FOLDER / "index.npy").astype(np.float32)
        labels = json.loads((FOLDER / "index.json").read_text(encoding="utf-8"))
        report = json.loads((FOLDER / "report.json").read_text())
        return tok, (sess, words), index, labels, report
    except Exception as error:  # missing files or runtime: fall back to word matching
        log.warning("e5 model unavailable: %s", error)
        return None


def available() -> bool:
    return _model() is not None


def norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text or "").lower().split())


def _ids(sp, texts):
    """SentencePiece ids -> model ids (model id = SentencePiece id + 1; unknown -> 3), with <s> ... </s>, max 64."""
    rows = [[0] + [3 if i == 0 else i + 1 for i in ids][:62] + [2] for ids in sp.encode(list(texts))]
    width = max(len(r) for r in rows)
    ids = np.array([r + [1] * (width - len(r)) for r in rows], dtype=np.int64)
    mask = np.array([[1] * len(r) + [0] * (width - len(r)) for r in rows], dtype=np.int64)
    return ids, mask


def encode(texts: list[str]) -> np.ndarray:
    tok, (sess, (words, scale)), *_ = _model()
    ids, mask = _ids(tok, [f"query: {norm(t)}" for t in texts])
    vectors = words[ids].astype(np.float32) * scale[ids][..., None]  # only the rows this text uses
    hidden = sess.run(None, {"inputs_embeds": vectors, "attention_mask": mask})[0]
    pooled = (hidden * mask[..., None]).sum(1) / mask.sum(1, keepdims=True)
    return pooled / np.linalg.norm(pooled, axis=1, keepdims=True)


def nearest(texts: list[str], prefix) -> list[tuple[Optional[str], float]]:
    """For each text, the closest index entry whose label starts with prefix ('dish:', 'faq', ...) and its similarity."""
    model = _model()
    if model is None or not texts:
        return [(None, 0.0)] * len(texts)
    _tok, _sess, index, labels, _report = model
    rows = [i for i, e in enumerate(labels) if e["label"].startswith(prefix)]
    sims = encode(texts) @ index[rows].T
    best = sims.argmax(1)
    return [(labels[rows[b]]["label"], float(sims[k, b])) for k, b in enumerate(best)]


def threshold(kind: str) -> float:
    model = _model()
    return float(model[4][f"{kind}_threshold"]) if model else 1.1


def segments(text: str) -> list[str]:
    """'2 idli with sambar, rice and dal' -> ['2 idli', 'sambar', 'rice', 'dal'] (numbers and units dropped)."""
    parts = re.split(r"[,;\n/+|•]|\band\b|\bwith\b|\baur\b|\bke saath\b|\bతో\b|\bమరియు\b|\bऔर\b|\bके साथ\b", text, flags=re.I)
    out = []
    for p in parts:
        p = re.sub(r"\b\d+(\.\d+)?\s*(g|gm|grams?|ml|cups?|katori|bowls?|pieces?|nos?|tbsp|tsp|glass(es)?)?\b", " ", p, flags=re.I)
        p = re.sub(r"\b(breakfast|lunch|dinner|snacks?|morning|evening|night|tiffin|nashta)\b\s*:?", " ", p, flags=re.I)
        p = " ".join(p.split())
        if len(p) >= 3:
            out.append(p)
    return out[:40]


def match_items(text: str, kind: str) -> dict[str, float]:
    """Dishes ('dish') or ingredients ('ingredient') named in free text, with similarity, above the measured threshold."""
    model = _model()
    if model is None or not model[4].get("live", {}).get("names"):
        return {}  # name matching goes live only after it meets the agreed 95% on unseen real phrases
    parts = segments(text)
    found: dict[str, float] = {}
    for (label, score) in nearest(parts, f"{kind}:"):
        if label and score >= threshold("name"):
            key = label.split(":", 1)[1]
            found[key] = max(found.get(key, 0.0), score)
    return found


def match_question(question: str) -> tuple[Optional[str], float]:
    """('faq:<id>' or 'safety:<topic>', similarity) for a question in any of the three languages, else (None, score)."""
    model = _model()
    if model is None or not model[4].get("live", {}).get("questions"):
        return None, 0.0
    (safety, s_score), (faq, f_score) = nearest([question], "safety:")[0], nearest([question], "faq:")[0]
    # Safety first: an emergency, self-harm or medicine question wins when it is close (measured: emergencies
    # 0.79-0.97, everyday questions at most 0.57).
    if safety and (s_score >= 0.85 or (s_score >= 0.75 and s_score >= f_score)):
        return safety, s_score
    return (faq, f_score) if faq and f_score >= threshold("faq") else (None, f_score)


@lru_cache(maxsize=1)
def _faq_rows() -> dict:
    rows = {}
    for i, e in enumerate(_model()[3]):
        if e["label"].startswith("faq:"):
            rows.setdefault(e["label"][4:], []).append(i)
    return rows


def faq_similarities(question: str) -> dict[str, float]:
    """FAQ id -> how close this question is to that FAQ's example questions (empty when the model is off)."""
    model = _model()
    if model is None or not model[4].get("live", {}).get("questions"):
        return {}
    vector, index = encode([question])[0], model[2]
    return {fid: float((index[rows] @ vector).max()) for fid, rows in _faq_rows().items()}
