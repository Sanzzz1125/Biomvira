"""Shrink the fine-tuned e5 model for the server and build its search index.

1. Vocabulary: keep only the word pieces used by English, Hindi and Telugu text (our data, translations and FAQ, never
   the held-out test phrases) plus every single character of those scripts, so any text can still be written.
2. Export to ONNX and quantise the weights to 8 bits (onnxruntime, MIT). The server needs no PyTorch.
3. Index: embeddings of every known dish, ingredient and food name, every FAQ question, and safety phrases.
4. Re-measure accuracy with the compressed model on the same held-out tests.

Usage:  python evaluation/e5/compress.py <fine-tuned folder>   -> backend/app/nlp/e5/
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from tokenizers import Tokenizer
from transformers import AutoModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
OUT = ROOT / "backend" / "app" / "nlp" / "e5"
import train  # noqa: E402  (data and test splits)

SAFETY = {  # phrases that must reach the fixed safety replies even when written in Hindi or Telugu
    "safety:emergency": ["chest pain", "severe chest pain right now", "i cannot breathe", "heart attack", "fainted",
                         "unconscious", "heavy bleeding", "vomiting blood", "seizure", "stroke", "severe allergic reaction"],
    "safety:self_harm": ["i want to kill myself", "i want to end my life", "suicide", "i want to hurt myself"],
    # Hindi and Telugu (written by hand; the same meanings as the English ones)
    "safety:medicine": ["which tablet should i take", "how many mg of iron tablet", "medicine dose for diabetes",
                        "can i stop my thyroid medicine", "supplement dosage", "insulin dose"],
}


SAFETY["safety:emergency"] += [
    "सीने में तेज़ दर्द", "मुझे अभी सीने में दर्द हो रहा है", "सांस नहीं ले पा रहा हूँ", "सांस लेने में बहुत तकलीफ़",
    "बेहोश हो गया", "बेहोश हो गई", "बेहोश हो गए हैं", "होश नहीं आ रहा", "స్పృహ కోల్పోయారు", "స్పృహ లేదు", "बहुत ज़्यादा खून बह रहा है", "खून की उल्टी", "दिल का दौरा", "दौरा पड़ा",
    "ఛాతీలో తీవ్రమైన నొప్పి", "నాకు ఇప్పుడు ఛాతీ నొప్పిగా ఉంది", "ఊపిరి ఆడటం లేదు", "శ్వాస తీసుకోవడం చాలా కష్టంగా ఉంది",
    "స్పృహ తప్పి పడిపోయారు", "చాలా రక్తం పోతోంది", "రక్తం వాంతి", "గుండెపోటు", "ఫిట్స్ వచ్చాయి"]
SAFETY["safety:self_harm"] += ["मैं अपनी जान देना चाहता हूँ", "मैं आत्महत्या करना चाहता हूँ", "मैं खुद को नुकसान पहुँचाना चाहता हूँ",
                               "నేను చనిపోవాలనుకుంటున్నాను", "నేను ఆత్మహత్య చేసుకోవాలనుకుంటున్నాను", "నన్ను నేను గాయపరచుకోవాలనుకుంటున్నాను"]
SAFETY["safety:medicine"] += ["कौन सी गोली लूँ", "आयरन की गोली कितनी लेनी चाहिए", "दवा की खुराक कितनी है", "क्या मैं थायराइड की दवा बंद कर दूँ",
                              "ఏ మాత్ర వేసుకోవాలి", "ఐరన్ మాత్ర ఎంత వేసుకోవాలి", "మందు మోతాదు ఎంత", "నేను థైరాయిడ్ మందు ఆపవచ్చా"]


def corpus() -> list[str]:
    d = train.DATA
    test_items = set(d["test_items"])
    texts = [n for i in d["items"] for n in i["names"]]
    texts += [v for k, vs in d.get("name_variants", {}).items() if k not in test_items for v in vs]
    texts += [q for f in d["faq"] for q in f["questions"]]
    texts += [v for k, vs in d["question_variants"].items() if k.split(":")[1] not in set(d["test_faq"]) for v in vs]
    texts += [p for ps in SAFETY.values() for p in ps]
    for folder, names in ((ROOT / "backend/app/data/i18n", ("strings_en.txt", "hi.txt", "te.txt")),
                          (ROOT / "frontend/src/lib/i18n", ("ui_en.txt", "ui_hi.txt", "ui_te.txt"))):
        for n in names:
            texts += (folder / n).read_text(encoding="utf-8").split("\n")
    return texts


def prune(src: Path, dst: Path) -> None:
    tok_json = json.loads((src / "tokenizer.json").read_text())
    vocab = tok_json["model"]["vocab"]
    tokenizer = Tokenizer.from_file(str(src / "tokenizer.json"))
    # Keep EVERY piece written only in Latin, Devanagari or Telugu (plus digits and punctuation), so any English,
    # Hindi or Telugu word a person types keeps its learned meaning; only the other ~100 languages are dropped.
    def ours(piece: str) -> bool:
        return all(c == "▁" or c.isascii() or "\u0900" <= c <= "\u097f" or "\u0c00" <= c <= "\u0c7f"
                   or "\u00a0" <= c <= "\u00ff" or "\u2010" <= c <= "\u2030" for c in piece)
    keep = {0, 1, 2, 3} | {i for i, (piece, _score) in enumerate(vocab) if ours(piece)}
    for enc in tokenizer.encode_batch([f"query: {t}".lower() for t in corpus()] + [f"query: {t}" for t in corpus()]):
        keep.update(enc.ids)
    chars = [chr(c) for r in ((0x20, 0x7F), (0xA0, 0x100), (0x900, 0x980), (0xC00, 0xC80), (0x2010, 0x2030)) for c in range(*r)]
    piece_id = {p: i for i, (p, _s) in enumerate(vocab)}
    for ch in chars:
        for p in (ch, "▁" + ch):
            if p in piece_id:
                keep.add(piece_id[p])
    keep = sorted(i for i in keep if i < len(vocab))
    new_id = {old: new for new, old in enumerate(keep)}
    tok_json["model"]["vocab"] = [vocab[i] for i in keep]
    tok_json["model"]["unk_id"] = new_id[tok_json["model"]["unk_id"]]
    tok_json["added_tokens"] = [dict(t, id=new_id[t["id"]]) for t in tok_json["added_tokens"] if t["id"] in new_id]
    for spec in (tok_json.get("post_processor") or {}).get("special_tokens", {}).values():
        spec["ids"] = [new_id[i] for i in spec["ids"]]
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "tokenizer.json").write_text(json.dumps(tok_json, ensure_ascii=False))
    model = AutoModel.from_pretrained(src)
    weight = model.embeddings.word_embeddings.weight.data[keep].clone()
    model.resize_token_embeddings(len(keep))
    model.embeddings.word_embeddings.weight.data = weight
    model.config.vocab_size = len(keep)
    model.save_pretrained(dst / "torch")
    print(f"vocabulary {len(vocab)} -> {len(keep)} pieces")


def export(dst: Path) -> None:
    """ONNX transformer that takes word vectors (inputs_embeds); the word table is stored separately as 8-bit rows,
    so the server reads only the rows a message uses instead of expanding the whole table on every request."""
    class Encoder(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model

        def forward(self, inputs_embeds, attention_mask):
            return self.model(inputs_embeds=inputs_embeds, attention_mask=attention_mask, use_cache=False).last_hidden_state

    bert = AutoModel.from_pretrained(dst / "torch").eval()
    table = bert.embeddings.word_embeddings.weight.detach().numpy()
    scale = np.abs(table).max(1) / 127.0
    np.save(dst / "words_int8.npy", np.round(table / scale[:, None]).astype(np.int8))
    np.save(dst / "words_scale.npy", scale.astype(np.float32))
    embeds = torch.zeros(1, 4, table.shape[1])
    torch.onnx.export(Encoder(bert), (embeds, torch.ones(1, 4, dtype=torch.long)), str(dst / "model_fp32.onnx"),
                      input_names=["inputs_embeds", "attention_mask"], output_names=["last_hidden_state"],
                      dynamic_axes={"inputs_embeds": {0: "b", 1: "t"}, "attention_mask": {0: "b", 1: "t"},
                                    "last_hidden_state": {0: "b", 1: "t"}}, opset_version=17, dynamo=False)
    quantize_dynamic(str(dst / "model_fp32.onnx"), str(dst / "model.onnx"), weight_type=QuantType.QInt8,
                     op_types_to_quantize=["MatMul"])
    (dst / "model_fp32.onnx").unlink()


def _ids(sp, texts):
    """SentencePiece ids -> model ids (model id = SentencePiece id + 1; unknown -> 3), with <s> ... </s>, max 64."""
    rows = [[0] + [3 if i == 0 else i + 1 for i in ids][:62] + [2] for ids in sp.encode(list(texts))]
    width = max(len(r) for r in rows)
    ids = np.array([r + [1] * (width - len(r)) for r in rows], dtype=np.int64)
    mask = np.array([[1] * len(r) + [0] * (width - len(r)) for r in rows], dtype=np.int64)
    return ids, mask


def trim_spm(work: Path) -> None:
    """The model's own SentencePiece file, cut to the kept pieces (same tokens, about 40 MB in memory instead of 143)."""
    from huggingface_hub import hf_hub_download
    from sentencepiece import sentencepiece_model_pb2 as pb
    model = pb.ModelProto()
    model.ParseFromString(Path(hf_hub_download("intfloat/multilingual-e5-small", "sentencepiece.bpe.model")).read_bytes())
    keep = {p for p, _ in json.loads((work / "tokenizer.json").read_text())["model"]["vocab"]}
    pieces = [p for p in model.pieces if p.type != pb.ModelProto.SentencePiece.NORMAL or p.piece in keep]
    del model.pieces[:]
    model.pieces.extend(pieces)
    (work / "spm.model").write_bytes(model.SerializeToString())


class Onnx:
    """The same encoder the server uses (see backend/app/nlp/embed.py)."""

    def __init__(self, folder: Path):
        import sentencepiece
        self.tok = sentencepiece.SentencePieceProcessor(model_file=str(folder / "spm.model"))
        self.words = np.load(folder / "words_int8.npy", mmap_mode="r")
        self.scale = np.load(folder / "words_scale.npy")
        self.sess = ort.InferenceSession(str(folder / "model.onnx"), providers=["CPUExecutionProvider"])

    def encode(self, texts, batch_size=128, normalize_embeddings=True):
        out = []
        for i in range(0, len(texts), batch_size):
            ids, mask = _ids(self.tok, texts[i:i + batch_size])
            vectors = (self.words[ids].astype(np.float32) * self.scale[ids][..., None])
            hidden = self.sess.run(None, {"inputs_embeds": vectors, "attention_mask": mask})[0]
            pooled = (hidden * mask[..., None]).sum(1) / mask.sum(1, keepdims=True)
            out.append(pooled / np.linalg.norm(pooled, axis=1, keepdims=True))
        return np.concatenate(out)


def build_index(model, dst: Path) -> None:
    names_index, _ = train.name_sets()
    faq_index, _ = train.question_sets()
    entries = (names_index + [(t, f"faq:{fid}") for t, fid in faq_index]
               + [(train.norm(p), label) for label, ps in SAFETY.items() for p in ps])
    emb = model.encode([f"query: {t}" for t, _ in entries])
    np.save(dst / "index.npy", emb.astype(np.float16))
    (dst / "index.json").write_text(json.dumps([{"text": t, "label": l} for t, l in entries], ensure_ascii=False))


def rebuild_index() -> None:
    """Index only (after changing names, FAQ or safety phrases): no retraining."""
    build_index(Onnx(OUT), OUT)


def main(src: Path) -> None:
    work = Path(str(src) + "_small")
    prune(src, work)
    export(work)
    trim_spm(work)
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ("model.onnx", "spm.model", "words_int8.npy", "words_scale.npy"):
        (OUT / name).write_bytes((work / name).read_bytes())
    model = Onnx(OUT)
    names_index, names_q = train.name_sets()
    faq_index, faq_q = train.question_sets()
    report = json.loads((src / "report.json").read_text())
    if (OUT / "report.json").exists():  # keep the go-live decisions made from the measured accuracy
        old = json.loads((OUT / "report.json").read_text())
        report.update({k: old[k] for k in ("live", "live_reason") if k in old})
    report["compressed_names"] = train.accuracy(model, names_index, names_q["test"])[0]
    report["compressed_questions"] = train.accuracy(model, faq_index, faq_q["test"])[0]
    report["compressed_questions_english"] = train.accuracy(model, faq_index, faq_q["test_english"])[0]
    report["model_mb"] = round((OUT / "model.onnx").stat().st_size / 1e6, 1)
    build_index(model, OUT)
    (OUT / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    rebuild_index() if sys.argv[1] == "--index-only" else main(Path(sys.argv[1]))
