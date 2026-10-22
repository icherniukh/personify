#!/usr/bin/env python3
"""Offline research store, corpus index, stylometry and pack assembler for extract-persona.

Stdlib only. Fetching is done by the host agent (web tools, user-supplied files);
this script never touches the network and never calls a model.

Store layout (one directory per persona id):

    <research-root>/<id>/
      manifest.json                 subject, aliases, index state, history
      sources.jsonl                 one provenance record per captured source
      sources/raw/<source_id>.txt   text exactly as captured
      sources/normalized/<source_id>.txt
      corpus/chunks.jsonl           ~200-word chunks with ids, speakers, hashes
      corpus/utterances.jsonl       subject-attributed verbatim units (deduped)
      corpus/embeddings/            reserved for an optional embedding index
      profile/stylometry.json       measured sentence-building profile
      analysis/analysis.json        latest agent-written analysis (claims + evidence ids)
      analysis/history/             every previous analysis, timestamped
      packs/                        every assembled pack, timestamped

Subcommands: init, add-source, index, profile, status, retrieve, assemble,
validate, migrate, budget. Run with -h for details.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

TOOL_VERSION = "0.6.0"
STORE_VERSION = 1
PACK_SCHEMA_VERSION = 2

SKILL_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_DIR / "references" / "persona-pack.schema.json"

SOURCE_TYPES = (
    "transcript", "interview", "podcast", "speech", "writing", "social-post",
    "script", "quote-collection", "article-about", "analysis", "reference", "other",
)
ATTRIBUTIONS = ("subject", "mixed", "about")
CONTEXTS = ("work", "casual", "personal", "pressure", "conflict", "public", "teaching", "unknown")

V1_REQUIRED = (
    "id", "display_name", "summary", "voice", "interaction_stance", "value_profile",
    "reasoning_style", "preferred_terminology", "speech_patterns", "default_structures",
    "ambiguity_policy", "tradeoff_policy", "compression_policy", "interaction_rules",
    "prompt_overlay", "provenance", "quality_level",
)
BLOCK_FIELDS = ("ambiguity_policy", "tradeoff_policy", "compression_policy", "prompt_overlay", "identity")

# Layer plan. Budgets are hypotheses (see docs/extract-persona.md): a small stable
# core for caching and re-anchoring, the v1 lens in standard, rich evidence in
# extended, and everything else retrievable from the corpus on demand.
DEFAULT_BUDGETS = {"core": 450, "standard": 1600, "extended": 1600}
LAYER_FIELDS = {
    "core": ["display_name", "summary", "voice", "core"],
    "standard": [
        "interaction_stance", "value_profile", "reasoning_style", "preferred_terminology",
        "speech_patterns", "default_structures", "ambiguity_policy", "tradeoff_policy",
        "compression_policy", "interaction_rules", "prompt_overlay",
    ],
    "extended": [
        "idiolect", "humor", "under_pressure", "stances", "voice_calibration",
        "example_utterances", "contradictions", "knowledge_boundaries", "relationships",
    ],
    "retrievable": ["retrieval"],
}
# Lowest priority first: trimmed from the pack (kept in the store) when extended overflows.
EXTENDED_TRIM_ORDER = (
    ("relationships", None), ("contradictions", None), ("stances", None),
    ("example_utterances", "items"), ("idiolect", "signature_phrases"),
    ("under_pressure", None), ("voice_calibration", None),
)
# (parent, key) lists whose items must carry evidence ids or inferred: true.
EVIDENCE_LISTS = (
    ("idiolect", "signature_phrases"), ("idiolect", "sentence_patterns"), (None, "stances"),
    (None, "relationships"), (None, "under_pressure"), (None, "contradictions"),
    ("humor", "mechanisms"),
)

DISCOURSE_MARKERS = (
    "you know", "i mean", "look", "listen", "so", "well", "now", "anyway", "actually",
    "basically", "honestly", "literally", "right", "okay", "ok", "like", "the thing is",
    "here's the thing", "by the way", "of course", "in fact", "frankly", "obviously",
    "again", "and so", "but", "you see", "mind you", "let me be clear", "to be fair",
)
HEDGES = ("maybe", "perhaps", "probably", "i think", "i guess", "sort of", "kind of", "might", "possibly", "i suppose", "seems")
INTENSIFIERS = ("very", "really", "totally", "absolutely", "completely", "extremely", "so much", "incredibly", "insanely", "super", "definitely")
STOPWORDS = frozenset(
    "a an the and or but if then so of to in on at for with by from as is are was were be been being it its "
    "this that these those i you he she we they me him her us them my your his our their not no do does did "
    "have has had will would can could should just there here what which who whom how when where why all any".split()
)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['\u2019][A-Za-z]+)?")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?\u2026])[\"\u201d\u2019)\]]*\s+(?=[\"\u201c\u2018(\[]?[A-Z0-9])")
SPEAKER_RE = re.compile(r"^\s*(?:\[[^\]]{1,20}\]\s*)?([A-Z][A-Za-z0-9 .'\-]{0,40}?)\s*:\s+(.+)$")
TIMESTAMP_RE = re.compile(r"[\[(]?\b\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?\b[\])]?")
SAID_BY_RE = re.compile(r"^[\s,]*(?:said|says|told|added|wrote|joked|recalled)\s+((?:one |a |an |the )?[A-Za-z][A-Za-z.'\-]*(?: [A-Z][A-Za-z.'\-]*)?)")
QUOTE_RE = re.compile(r"[\u201c\"]([^\u201c\u201d\"]{20,600})[\u201d\"]")


# --------------------------------------------------------------------------- utils

def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """Same deterministic chars/4 estimate as scripts/token_overhead.py."""
    return math.ceil(len(text) / 4) if text else 0


def words(text: str) -> list[str]:
    return [w.replace("\u2019", "'") for w in WORD_RE.findall(text)]


def split_sentences(text: str) -> list[str]:
    out: list[str] = []
    for para in text.split("\n"):
        para = para.strip()
        if para:
            out.extend(s.strip() for s in SENT_SPLIT_RE.split(para) if s.strip())
    return out


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def research_root(override: str | None = None) -> Path:
    if override:
        return Path(override)
    if os.environ.get("PERSONIFY_RESEARCH_DIR"):
        return Path(os.environ["PERSONIFY_RESEARCH_DIR"])
    return xdg_data_home() / "personify" / "research"


def personas_dir() -> Path:
    return xdg_data_home() / "personify" / "personas"


# --------------------------------------------------------------------------- normalization

_PUNCT_MAP = str.maketrans({"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'", "\u2013": "-", "\u2014": " - ", "\u00a0": " "})


def normalize_text(raw: str) -> str:
    """NFKC, straight quotes, no timestamps, collapsed spaces; line structure kept for speaker parsing."""
    text = unicodedata.normalize("NFKC", raw).translate(_PUNCT_MAP).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        line = TIMESTAMP_RE.sub("", line)
        lines.append(re.sub(r"[ \t]+", " ", line).strip())
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return text.strip() + "\n"


# --------------------------------------------------------------------------- store

class Store:
    def __init__(self, root: Path, persona_id: str):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", persona_id):
            raise SystemExit(f"persona id must be kebab-case: {persona_id!r}")
        self.id = persona_id
        self.dir = root / persona_id
        self.manifest_path = self.dir / "manifest.json"
        self.sources_path = self.dir / "sources.jsonl"
        self.chunks_path = self.dir / "corpus" / "chunks.jsonl"
        self.utterances_path = self.dir / "corpus" / "utterances.jsonl"
        self.stylometry_path = self.dir / "profile" / "stylometry.json"
        self.analysis_path = self.dir / "analysis" / "analysis.json"

    def exists(self) -> bool:
        return self.manifest_path.is_file()

    def manifest(self) -> dict[str, Any]:
        if not self.exists():
            raise SystemExit(f"no research store for {self.id!r} at {self.dir}; run init first")
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        manifest["updated_at"] = now_iso()
        write_json(self.manifest_path, manifest)

    def log(self, event: dict[str, Any]) -> None:
        manifest = self.manifest()
        manifest["history"].append({"at": now_iso(), **event})
        self.save_manifest(manifest)

    def init(self, display_name: str, aliases: list[str], kind: str = "real-person", role: str | None = None) -> dict[str, Any]:
        if self.exists():
            manifest = self.manifest()
            manifest["subject"]["aliases"] = sorted(set(manifest["subject"]["aliases"]) | set(aliases))
            if role:
                manifest["subject"]["role"] = role
            self.save_manifest(manifest)
            return manifest
        for sub in ("sources/raw", "sources/normalized", "corpus/embeddings", "profile", "analysis/history", "packs"):
            (self.dir / sub).mkdir(parents=True, exist_ok=True)
        default_aliases = {display_name}
        parts = display_name.split()
        if len(parts) > 1:
            default_aliases.add(parts[-1])
        manifest = {
            "store_version": STORE_VERSION,
            "tool_version": TOOL_VERSION,
            "persona_id": self.id,
            "subject": {"display_name": display_name, "aliases": sorted(default_aliases | set(aliases)), "kind": kind, "role": role},
            "created_at": now_iso(),
            "indexed_sources": {},
            "counts": {"sources": 0, "chunks": 0, "utterances": 0},
            "corpus_sha": None,
            "embeddings": None,
            "history": [],
        }
        self.save_manifest(manifest)
        return manifest

    def sources(self) -> list[dict[str, Any]]:
        return read_jsonl(self.sources_path)

    def add_source(self, text: str, meta: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        self.manifest()
        normalized = normalize_text(text)
        digest = sha256_text(normalized)
        source_id = f"src-{digest[:12]}"
        rows = self.sources()
        for row in rows:
            if row["sha256"] == digest:
                # Same content again: keep one copy, remember the extra URL (mirror, repost).
                url = meta.get("url")
                if url and url != row.get("url") and url not in row.setdefault("alt_urls", []):
                    row["alt_urls"].append(url)
                    write_jsonl(self.sources_path, rows)
                return row, False
        (self.dir / "sources" / "raw" / f"{source_id}.txt").write_text(text, encoding="utf-8")
        (self.dir / "sources" / "normalized" / f"{source_id}.txt").write_text(normalized, encoding="utf-8")
        record = {
            "id": source_id,
            "sha256": digest,
            "url": meta.get("url"),
            "alt_urls": [],
            "title": meta.get("title"),
            "source_type": meta.get("source_type") or "other",
            "attribution": meta.get("attribution") or "about",
            "voice": meta.get("voice") or "verbatim",
            "context": meta.get("context") or "unknown",
            "published": meta.get("published"),
            "retrieved_at": meta.get("retrieved_at") or now_iso(),
            "language": meta.get("language") or "en",
            "rights_note": meta.get("rights_note"),
            "words": len(words(normalized)),
            "added_at": now_iso(),
        }
        rows.append(record)
        write_jsonl(self.sources_path, rows)
        self.log({"event": "add-source", "source_id": source_id})
        return record, True

    def normalized_text(self, source_id: str) -> str:
        return (self.dir / "sources" / "normalized" / f"{source_id}.txt").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- indexing

def is_subject(label: str | None, aliases: list[str]) -> bool:
    if not label:
        return False
    lab = label.strip().lower().rstrip(".")
    for alias in aliases:
        a = alias.strip().lower()
        if lab == a or (len(lab) > 2 and (a.endswith(" " + lab) or a.startswith(lab + " "))):
            return True
    return False


def parse_turns(text: str) -> list[tuple[str | None, str]]:
    """Split a transcript into (speaker, text) turns. Unlabelled lines continue the current turn."""
    turns: list[tuple[str | None, str]] = []
    speaker: str | None = None
    buf: list[str] = []
    for line in text.split("\n"):
        m = SPEAKER_RE.match(line)
        if m and len(m.group(1).split()) <= 4:
            if buf:
                turns.append((speaker, " ".join(buf).strip()))
            speaker, buf = m.group(1).strip(), [m.group(2).strip()]
        elif line.strip():
            buf.append(line.strip())
        elif buf:
            turns.append((speaker, " ".join(buf).strip()))
            buf = []
    if buf:
        turns.append((speaker, " ".join(buf).strip()))
    return [(s, t) for s, t in turns if t]


def chunk_text(text: str, target_words: int = 200) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[A-Z][A-Za-z0-9 .'\-]{0,40}:\s)", text) if p.strip()]
    chunks: list[str] = []
    cur: list[str] = []
    count = 0
    for para in paras:
        pieces = [para]
        if len(words(para)) > target_words * 2:
            pieces, piece, pc = [], [], 0
            for sent in split_sentences(para):
                if piece and pc + len(words(sent)) > target_words:
                    pieces.append(" ".join(piece))
                    piece, pc = [], 0
                piece.append(sent)
                pc += len(words(sent))
            if piece:
                pieces.append(" ".join(piece))
        for piece_text in pieces:
            n = len(words(piece_text))
            if cur and count + n > target_words:
                chunks.append("\n".join(cur))
                cur, count = [], 0
            cur.append(piece_text)
            count += n
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def utterance_key(text: str) -> str:
    return sha256_text(" ".join(w.lower() for w in words(text)))


def extract_utterances(source: dict[str, Any], text: str, aliases: list[str]) -> list[dict[str, Any]]:
    """Subject-attributed units. Verbatim only from the subject's own text or labelled turns."""
    out: list[dict[str, Any]] = []
    attribution = source.get("attribution", "about")
    voice = source.get("voice", "verbatim")
    if attribution == "subject":
        turns = parse_turns(text)
        labelled = any(s for s, _ in turns)
        for speaker, body in turns:
            if labelled and speaker and not is_subject(speaker, aliases):
                continue
            for para in [p for p in body.split("\n") if p.strip()] or [body]:
                out.append({"text": para, "speaker": speaker or (aliases[0] if aliases else None), "kind": voice, "prev_turn": None})
    elif attribution == "mixed":
        prev: str | None = None
        for speaker, body in parse_turns(text):
            if is_subject(speaker, aliases):
                out.append({"text": body, "speaker": speaker, "kind": voice, "prev_turn": prev[:300] if prev else None})
            prev = f"{speaker}: {body}" if speaker else body
    else:  # about: quoted spans are only candidate subject lines, flagged secondary
        for m in QUOTE_RE.finditer(text):
            span = m.group(1).strip()
            said = SAID_BY_RE.match(text[m.end():m.end() + 60])
            if said and not is_subject(said.group(1), aliases) and said.group(1).lower() not in {"he", "she", "they"}:
                continue  # quote attributed to someone else ("... said one deckhand")
            if len(words(span)) >= 5:
                out.append({"text": span, "speaker": None, "kind": "secondary-quote", "prev_turn": None})
    return [u for u in out if len(words(u["text"])) >= 3]


def index_store(store: Store, rebuild: bool = False) -> dict[str, Any]:
    """Incremental: only sources whose sha is not yet indexed are processed."""
    manifest = store.manifest()
    aliases = manifest["subject"]["aliases"]
    indexed: dict[str, str] = {} if rebuild else dict(manifest.get("indexed_sources", {}))
    chunks = [] if rebuild else read_jsonl(store.chunks_path)
    utterances = [] if rebuild else read_jsonl(store.utterances_path)
    by_key = {u["sha"]: u for u in utterances}
    new_sources = 0
    for source in store.sources():
        sid = source["id"]
        if indexed.get(sid) == source["sha256"]:
            continue
        new_sources += 1
        text = store.normalized_text(sid)
        chunks = [c for c in chunks if c["source_id"] != sid]
        for n, body in enumerate(chunk_text(text)):
            chunks.append({
                "id": f"{sid}#c{n}", "source_id": sid, "n": n, "text": body,
                "speakers": sorted({s for s, _ in parse_turns(body) if s}),
                "words": len(words(body)), "tokens": estimate_tokens(body), "sha": sha256_text(body),
            })
        counter = sum(1 for u in utterances if u["source_id"] == sid)
        for utt in extract_utterances(source, text, aliases):
            key = utterance_key(utt["text"])
            if key in by_key:
                existing = by_key[key]
                if sid != existing["source_id"] and sid not in existing.setdefault("also_in", []):
                    existing["also_in"].append(sid)
                continue
            record = {
                "id": f"u-{sid[4:12]}-{counter}", "source_id": sid, "sha": key, "text": utt["text"],
                "speaker": utt["speaker"], "kind": utt["kind"], "prev_turn": utt["prev_turn"],
                "context": source.get("context", "unknown"), "words": len(words(utt["text"])), "also_in": [],
            }
            counter += 1
            by_key[key] = record
            utterances.append(record)
        indexed[sid] = source["sha256"]
    chunks.sort(key=lambda c: (c["source_id"], c["n"]))
    write_jsonl(store.chunks_path, chunks)
    write_jsonl(store.utterances_path, utterances)
    corpus_sha = sha256_text("".join(sorted(c["sha"] for c in chunks)) + "".join(sorted(u["sha"] for u in utterances)))
    manifest = store.manifest()
    manifest["indexed_sources"] = indexed
    manifest["corpus_sha"] = corpus_sha
    manifest["counts"] = {"sources": len(indexed), "chunks": len(chunks), "utterances": len(utterances)}
    manifest["history"].append({"at": now_iso(), "event": "rebuild" if rebuild else "index", "new_sources": new_sources, "corpus_sha": corpus_sha})
    store.save_manifest(manifest)
    return {"new_sources": new_sources, **manifest["counts"], "corpus_sha": corpus_sha}


# --------------------------------------------------------------------------- stylometry

def _rate(count: int, total: int, per: int = 100) -> float:
    return round(per * count / total, 3) if total else 0.0


def _phrase_count(text_lower: str, phrase: str) -> int:
    return len(re.findall(r"(?<![a-z'])" + re.escape(phrase) + r"(?![a-z'])", text_lower))


def _ends_with(sentence: str, mark: str) -> bool:
    return sentence.rstrip("\"')]").endswith(mark)


def stylometry(utterances: list[dict[str, Any]], top: int = 25) -> dict[str, Any]:
    """Measured sentence-building profile of the subject's own lines (Biber-style surface features)."""
    verbatim = [u for u in utterances if u.get("kind") == "verbatim"]
    basis = verbatim or utterances
    basis_kind = "verbatim" if verbatim else ("secondary" if utterances else "none")
    texts = [u["text"] for u in basis]
    sentences = [s for t in texts for s in split_sentences(t) if words(s)]
    sent_lens = [len(words(s)) for s in sentences]
    raw_words = [w for t in texts for w in words(t)]
    all_words = [w.lower() for w in raw_words]
    total = len(all_words)
    nsent = len(sentences)
    joined = "\n".join(t.lower().replace("\u2019", "'") for t in texts)
    buckets = {"1-5": 0, "6-10": 0, "11-20": 0, "21-35": 0, "36+": 0}
    for n in sent_lens:
        buckets["1-5" if n <= 5 else "6-10" if n <= 10 else "11-20" if n <= 20 else "21-35" if n <= 35 else "36+"] += 1
    window = 100
    if total >= window:
        ttrs = [len(set(all_words[i:i + window])) / window for i in range(0, total - window + 1, window // 2)]
        mattr = round(sum(ttrs) / len(ttrs), 3)
    else:
        mattr = round(len(set(all_words)) / total, 3) if total else 0.0
    openers: Counter = Counter()
    for s in sentences:
        ws = [w.lower() for w in words(s)]
        openers[ws[0]] += 1
        if len(ws) > 1:
            openers[" ".join(ws[:2])] += 1
    per_k = lambda c: round(1000 * c / total, 2) if total else 0.0

    def lexicon(entries: Iterable[str]) -> dict[str, float]:
        counts = {e: _phrase_count(joined, e) for e in entries}
        return {k: per_k(v) for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])) if v}

    return {
        "basis": basis_kind,
        "utterances": len(basis),
        "words": total,
        "sentences": nsent,
        "sentence_words": {
            "mean": round(sum(sent_lens) / nsent, 2) if nsent else 0.0,
            "p10": percentile(sent_lens, 0.1), "p50": percentile(sent_lens, 0.5), "p90": percentile(sent_lens, 0.9),
            "histogram": buckets,
        },
        "short_sentence_share": round(buckets["1-5"] / nsent, 3) if nsent else 0.0,
        "utterance_words_p50": percentile([len(words(t)) for t in texts], 0.5),
        "question_rate": round(sum(_ends_with(s, "?") for s in sentences) / nsent, 3) if nsent else 0.0,
        "exclamation_rate": round(sum(_ends_with(s, "!") for s in sentences) / nsent, 3) if nsent else 0.0,
        "commas_per_sentence": round(sum(s.count(",") for s in sentences) / nsent, 2) if nsent else 0.0,
        "per_100_words": {
            "first_person_singular": _rate(sum(w in {"i", "me", "my", "mine", "i'm", "i've", "i'd", "i'll"} for w in all_words), total),
            "first_person_plural": _rate(sum(w in {"we", "us", "our", "ours", "we're", "we've"} for w in all_words), total),
            "second_person": _rate(sum(w in {"you", "your", "yours", "you're", "you've"} for w in all_words), total),
            "contractions": _rate(sum("'" in w for w in all_words), total),
            "all_caps_words": _rate(sum(len(w) > 1 and w.isupper() and not w.isdigit() for w in raw_words), total),
        },
        "mattr_100": mattr,
        "mean_word_length": round(sum(len(w) for w in all_words) / total, 2) if total else 0.0,
        "discourse_markers_per_1k": lexicon(DISCOURSE_MARKERS),
        "hedges_per_1k": lexicon(HEDGES),
        "intensifiers_per_1k": lexicon(INTENSIFIERS),
        "top_openers": [{"opener": k, "count": v} for k, v in openers.most_common(12) if v >= 2],
        "signature_candidates": signature_candidates(basis, top=top),
    }


def signature_candidates(utterances: list[dict[str, Any]], top: int = 25) -> list[dict[str, Any]]:
    """Recurring 2-6 word n-grams; cross-source recurrence required when more than one source exists."""
    grams: dict[str, dict[str, Any]] = {}
    sources = {u["source_id"] for u in utterances}
    for u in utterances:
        ws = [w.lower() for w in words(u["text"])]
        seen: set[str] = set()
        for n in range(2, 7):
            for i in range(len(ws) - n + 1):
                g = ws[i:i + n]
                if all(w in STOPWORDS for w in g) or g[-1] in {"the", "a", "an", "and", "of", "to"}:
                    continue
                key = " ".join(g)
                if key in seen:
                    continue
                seen.add(key)
                entry = grams.setdefault(key, {"count": 0, "sources": set(), "evidence": []})
                entry["count"] += 1
                entry["sources"].add(u["source_id"])
                entry["sources"].update(u.get("also_in", []))
                if len(entry["evidence"]) < 3:
                    entry["evidence"].append(u["id"])
    # A gram fully explained by a longer gram with the same support is not a separate phrase.
    covered: set[str] = set()
    for key, v in grams.items():
        parts = key.split()
        if len(parts) > 2:
            for sub in (" ".join(parts[:-1]), " ".join(parts[1:])):
                if sub in grams and grams[sub]["count"] == v["count"]:
                    covered.add(sub)
    min_sources = 2 if len(sources) > 1 else 1
    ranked = [(k, v) for k, v in grams.items() if k not in covered and v["count"] >= 3 and len(v["sources"]) >= min_sources]
    ranked.sort(key=lambda kv: (-(kv[1]["count"] * (1 + 0.5 * (len(kv[0].split()) - 2))), kv[0]))
    picked: list[dict[str, Any]] = []
    for key, v in ranked:
        if any(key in p["phrase"] and p["count"] >= v["count"] for p in picked):
            continue  # a longer phrase with the same support already covers it
        picked.append({"phrase": key, "count": v["count"], "sources": len(v["sources"]), "evidence": v["evidence"]})
        if len(picked) >= top:
            break
    return picked


# --------------------------------------------------------------------------- coverage gate

def coverage(store: Store, min_sources: int = 3, min_verbatim_words: int = 3000) -> dict[str, Any]:
    sources = store.sources()
    utterances = read_jsonl(store.utterances_path)
    verbatim_words = sum(u["words"] for u in utterances if u["kind"] == "verbatim")
    types = Counter(s["source_type"] for s in sources)
    contexts = Counter(u.get("context", "unknown") for u in utterances)
    indexed = set(store.manifest().get("indexed_sources", {}))
    checks = [
        ("distinct_sources", len(sources) >= min_sources, f"{len(sources)} sources (want >= {min_sources})"),
        ("source_type_variety", len(types) >= 2, f"types: {dict(types)}"),
        ("verbatim_volume", verbatim_words >= min_verbatim_words,
         f"{verbatim_words} subject verbatim words (want >= {min_verbatim_words}; collect more than the pack needs)"),
        ("pressure_context", any(c in contexts for c in ("pressure", "conflict")), "subject lines from a pressure/conflict context"),
        ("provenance", all(s.get("url") or s.get("rights_note") for s in sources), "every source has a url or an origin/rights note"),
        ("indexed", indexed == {s["id"] for s in sources}, "all sources indexed"),
    ]
    return {
        "persona_id": store.id,
        "sources": len(sources), "utterances": len(utterances), "verbatim_words": verbatim_words,
        "source_types": dict(types), "contexts": dict(contexts),
        "checks": [{"check": c, "ok": ok, "detail": d} for c, ok, d in checks],
        "ready": all(ok for _, ok, _ in checks),
    }


# --------------------------------------------------------------------------- retrieval (BM25, stdlib)

def _tokens(text: str) -> list[str]:
    return [w.lower() for w in words(text) if w.lower() not in STOPWORDS]


def bm25_search(docs: list[dict[str, Any]], query: str, k: int = 3, k1: float = 1.5, b: float = 0.75) -> list[tuple[float, dict[str, Any]]]:
    if not docs:
        return []
    toks = [_tokens(d["text"]) for d in docs]
    avgdl = (sum(len(t) for t in toks) / len(toks)) or 1.0
    df: Counter = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    scored = []
    for doc, t in zip(docs, toks):
        tf = Counter(t)
        score = 0.0
        for term in set(_tokens(query)):
            if term in tf:
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(t) / avgdl))
        if score > 0:
            scored.append((round(score, 4), doc))
    scored.sort(key=lambda sd: (-sd[0], sd[1]["id"]))
    return scored[:k]


def retrieve(store: Store, query: str, k: int = 3, kind: str = "all", max_tokens: int = 400) -> list[dict[str, Any]]:
    """Top-k corpus items for per-turn injection, capped by a token budget."""
    docs: list[dict[str, Any]] = []
    if kind in ("all", "utterance"):
        docs += [{**u, "doc_kind": "utterance"} for u in read_jsonl(store.utterances_path)]
    if kind in ("all", "chunk"):
        docs += [{**c, "doc_kind": "chunk"} for c in read_jsonl(store.chunks_path)]
    sources = {s["id"]: s for s in store.sources()}
    results, used = [], 0
    for score, doc in bm25_search(docs, query, k=k * 4):
        cost = estimate_tokens(doc["text"])
        if used + cost > max_tokens:
            continue
        used += cost
        src = sources.get(doc["source_id"], {})
        results.append({
            "id": doc["id"], "kind": doc["doc_kind"], "score": score, "text": doc["text"],
            "source_url": src.get("url"), "source_type": src.get("source_type"),
            "verbatim": doc.get("kind") == "verbatim", "usage": "shape-not-lines",
        })
        if len(results) >= k:
            break
    return results


# --------------------------------------------------------------------------- YAML subset (dump + load)
# The repo has no YAML dependency (CI runs on a bare Python), so packs are written and read with a
# small subset: block maps, block lists, |/> block scalars, plain/single/double-quoted scalars.

_PLAIN_START = re.compile(r"^[A-Za-z0-9_$(/]")
_YAML_SPECIAL = {"true", "false", "yes", "no", "on", "off", "null", "~", "y", "n"}
_NUMBER_LIKE = re.compile(r"^[-+]?(\d[\d_]*\.?\d*([eE][-+]?\d+)?|\.\d+|0x[0-9a-fA-F]+|0o[0-7]+)$")


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value) if isinstance(value, float) else str(value)
    s = str(value)
    plain = (
        bool(s) and _PLAIN_START.match(s) is not None and s == s.strip() and ": " not in s and " #" not in s
        and not s.endswith(":") and s.lower() not in _YAML_SPECIAL and not _NUMBER_LIKE.match(s)
        and not re.match(r"\d{4}-\d{2}-\d{2}", s) and not any(ch in s for ch in "`\"\t\n")
    )
    return s if plain else json.dumps(s, ensure_ascii=False)


def _block(text: str, indent: int) -> list[str]:
    pad = " " * indent
    return [pad + line if line.strip() else "" for line in text.rstrip("\n").split("\n")]


def _blockable(text: str) -> bool:
    """A literal block round-trips exactly only without leading blanks, trailing spaces or extra trailing newlines."""
    body = text[:-1] if text.endswith("\n") else text
    return bool(body.strip()) and body == body.strip("\n") and not text[:1].isspace() and all(l == l.rstrip() for l in body.split("\n"))


def _block_style(text: str) -> str:
    return "|" if text.endswith("\n") else "|-"


def dump_yaml(obj: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    lines: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                if not value:
                    lines.append(f"{pad}{key}: {'{}' if isinstance(value, dict) else '[]'}")
                else:
                    lines.append(f"{pad}{key}:")
                    lines += dump_yaml(value, indent + 2)
            elif isinstance(value, str) and _blockable(value) and ("\n" in value.strip() or key in BLOCK_FIELDS):
                lines.append(f"{pad}{key}: {_block_style(value)}")
                lines += _block(value, indent + 2)
            else:
                lines.append(f"{pad}{key}: {_scalar(value)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and item:
                sub = dump_yaml(item, indent + 2)
                lines.append(f"{pad}- {sub[0].lstrip()}")
                lines += sub[1:]
            elif isinstance(item, list) and item:
                lines.append(f"{pad}-")
                lines += dump_yaml(item, indent + 2)
            elif isinstance(item, str) and _blockable(item) and "\n" in item.strip():
                lines.append(f"{pad}- {_block_style(item)}")
                lines += _block(item, indent + 2)
            else:
                lines.append(f"{pad}- {_scalar(item) if not isinstance(item, (dict, list)) else ('{}' if isinstance(item, dict) else '[]')}")
    else:
        lines.append(pad + _scalar(obj))
    return lines


def to_yaml(obj: dict[str, Any]) -> str:
    return "\n".join(dump_yaml(obj)) + "\n"


def _parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if s.startswith('"'):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s  # e.g. '"quote" - gloss': not strict YAML, read the way the repo's line parsers read it
    if s.startswith("'") and s.endswith("'") and len(s) >= 2 and "' " not in s[1:-1]:
        return s[1:-1].replace("''", "'")
    if s == "[]":
        return []
    if s == "{}":
        return {}
    if " #" in s:
        s = s.split(" #", 1)[0].rstrip()
    low = s.lower()
    if low in ("null", "~", ""):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?\d*\.\d+([eE][-+]?\d+)?", s):
        return float(s)
    return s


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


class _Reader:
    def __init__(self, text: str):
        self.lines = text.split("\n")
        self.i = 0

    def peek(self) -> str | None:
        while self.i < len(self.lines) and (not self.lines[self.i].strip() or self.lines[self.i].lstrip().startswith("#")):
            self.i += 1
        return self.lines[self.i] if self.i < len(self.lines) else None

    def block(self, parent_indent: int, style: str) -> str:
        out: list[str] = []
        block_indent = None
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.strip():
                ind = _indent(line)
                if block_indent is None:
                    block_indent = ind
                if ind < block_indent or ind <= parent_indent:
                    break
                out.append(line[block_indent:])
            else:
                out.append("")
            self.i += 1
        while out and out[-1] == "":
            out.pop()
        if style.startswith(">"):
            paras, cur = [], []
            for l in out:
                if l == "":
                    paras.append(" ".join(cur))
                    cur = []
                else:
                    cur.append(l.strip())
            paras.append(" ".join(cur))
            text = "\n".join(paras)
        else:
            text = "\n".join(out)
        return text if style.endswith("-") else text + "\n"

    def node(self) -> Any:
        line = self.peek()
        if line is None:
            return None
        if line.lstrip().startswith("- ") or line.strip() == "-":
            return self.seq(_indent(line))
        return self.mapping(_indent(line))

    def value(self, rest: str, indent: int) -> Any:
        rest = rest.strip()
        if rest in ("|", "|-", "|+", ">", ">-", ">+"):
            return self.block(indent, rest)
        if rest == "":
            nxt = self.peek()
            if nxt is None or _indent(nxt) < indent or (_indent(nxt) == indent and not nxt.lstrip().startswith("- ")):
                return None
            return self.node()
        return _parse_scalar(rest)

    def mapping(self, indent: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while True:
            line = self.peek()
            if line is None or _indent(line) != indent or line.lstrip().startswith("- "):
                break
            m = _KEY_RE.match(line.strip())
            if not m:
                raise ValueError(f"unsupported YAML at line {self.i + 1}: {line!r}")
            self.i += 1
            out[m.group(1).strip('"')] = self.value(m.group(2) or "", indent)
        return out

    def seq(self, indent: int) -> list[Any]:
        out: list[Any] = []
        while True:
            line = self.peek()
            if line is None or _indent(line) != indent or not (line.lstrip().startswith("- ") or line.strip() == "-"):
                break
            body = line.strip()[2:].strip() if line.strip() != "-" else ""
            if body in ("|", "|-", ">", ">-"):
                self.i += 1
                out.append(self.block(indent, body))
            elif body and not body.startswith(('"', "'")) and _KEY_RE.match(body):
                self.lines[self.i] = " " * (indent + 2) + body  # "- key: v" opens a map at indent+2
                out.append(self.mapping(indent + 2))
            elif body == "":
                self.i += 1
                out.append(self.node())
            else:
                self.i += 1
                out.append(_parse_scalar(body))
        return out


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*|\"[^\"]+\"):(?:\s+(.*)|$)")


def load_yaml(text: str) -> Any:
    return _Reader(text).node()


# --------------------------------------------------------------------------- schema validation (JSON Schema subset)

def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


_TYPES = {
    "object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list), "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool), "null": lambda v: v is None,
}


def validate_instance(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    """Supports: $ref (#/$defs), type, const, enum, minLength, pattern, minimum, maximum, minItems,
    maxItems, items, required, properties, additionalProperties(bool), anyOf, not, allOf, if/then/else."""
    if "$ref" in schema:
        return validate_instance(value, root["$defs"][schema["$ref"].split("/")[-1]], root, path)
    errors: list[str] = []
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_TYPES[t](value) for t in types):
            return [f"{path}: expected {'/'.join(types)}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not one of {schema['enum']}")
    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errors.append(f"{path}: must not be empty")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match {schema['pattern']}")
    if _TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: allows at most {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate_instance(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                errors += validate_instance(value[key], sub, root, f"{path}.{key}")
        if schema.get("additionalProperties") is False:
            errors += [f"{path}: unexpected field {key!r}" for key in value if key not in props]
    if "anyOf" in schema and not any(not validate_instance(value, sub, root, path) for sub in schema["anyOf"]):
        errors.append(f"{path}: does not match any allowed shape")
    if "not" in schema and not validate_instance(value, schema["not"], root, path):
        errors.append(f"{path}: {schema.get('notMessage', 'matches a forbidden shape')}")
    for sub in schema.get("allOf", []):
        errors += validate_instance(value, sub, root, path)
    if "if" in schema:
        if not validate_instance(value, schema["if"], root, path):
            errors += validate_instance(value, schema.get("then", {}), root, path)
        elif "else" in schema:
            errors += validate_instance(value, schema["else"], root, path)
    return errors


# --------------------------------------------------------------------------- grounding + budgets

def evidence_ids(store: Store) -> set[str]:
    ids = {s["id"] for s in store.sources()}
    ids |= {c["id"] for c in read_jsonl(store.chunks_path)}
    ids |= {u["id"] for u in read_jsonl(store.utterances_path)}
    return ids


def grounding_errors(pack: dict[str, Any], known_ids: set[str] | None) -> list[str]:
    """Each evidence-bearing item needs evidence ids (that exist in the store, when given) or inferred: true."""
    errors: list[str] = []
    for parent, key in EVIDENCE_LISTS:
        container = pack.get(parent) if parent else pack
        items = container.get(key) if isinstance(container, dict) else None
        for i, item in enumerate(items or []):
            if not isinstance(item, dict):
                continue
            where = f"{parent + '.' if parent else ''}{key}[{i}]"
            ev = item.get("evidence") or []
            if not ev and not item.get("inferred"):
                errors.append(f"{where}: needs evidence ids or inferred: true")
            if known_ids is not None and ev:
                missing = [e for e in ev if e not in known_ids]
                if missing:
                    errors.append(f"{where}: unknown evidence ids {missing}")
    examples = pack.get("example_utterances") or {}
    for i, item in enumerate(examples.get("items") or [] if isinstance(examples, dict) else []):
        if known_ids is not None and isinstance(item, dict) and item.get("evidence") not in known_ids:
            errors.append(f"example_utterances.items[{i}]: unknown evidence id {item.get('evidence')!r}")
    return errors


def layer_tokens(pack: dict[str, Any], layer: str) -> int:
    fields = {k: pack[k] for k in LAYER_FIELDS[layer] if k in pack}
    return estimate_tokens(to_yaml(fields)) if fields else 0


def budget_report(pack: dict[str, Any]) -> dict[str, Any]:
    layers = pack.get("layers") or {}
    out: dict[str, Any] = {}
    for name in ("core", "standard", "extended"):
        budget = (layers.get(name) or {}).get("budget_tokens", DEFAULT_BUDGETS[name])
        used = layer_tokens(pack, name)
        out[name] = {"budget_tokens": budget, "estimated_tokens": used, "ok": used <= budget}
    out["full_pack_tokens"] = estimate_tokens(to_yaml(pack))
    return out


def validate_pack(pack: Any, store: Store | None = None, check_budget: bool = True) -> list[str]:
    """Schema (v1 and v2) + for v2: evidence grounding and the core-layer budget."""
    if not isinstance(pack, dict):
        return ["$: pack must be a mapping"]
    schema = load_schema()
    errors = validate_instance(pack, schema, schema)
    if pack.get("schema_version") == PACK_SCHEMA_VERSION:
        errors += grounding_errors(pack, evidence_ids(store) if store else None)
        if check_budget:
            core = budget_report(pack)["core"]
            if not core["ok"]:
                errors.append(f"layers.core: ~{core['estimated_tokens']} tokens exceeds budget {core['budget_tokens']}")
    return errors


# --------------------------------------------------------------------------- assembly

def make_layers(budgets: dict[str, int]) -> dict[str, Any]:
    return {
        "core": {"budget_tokens": budgets["core"], "load": "always", "fields": list(LAYER_FIELDS["core"])},
        "standard": {"budget_tokens": budgets["standard"], "load": "default", "fields": list(LAYER_FIELDS["standard"])},
        "extended": {"budget_tokens": budgets["extended"], "load": "on-request", "fields": list(LAYER_FIELDS["extended"])},
        "retrievable": {"load": "per-turn", "fields": list(LAYER_FIELDS["retrievable"])},
    }


def stylometry_summary(profile: dict[str, Any]) -> dict[str, Any]:
    sw = profile.get("sentence_words", {})
    per100 = profile.get("per_100_words", {})
    return {
        "basis": profile.get("basis", "none"),
        "basis_words": profile.get("words", 0),
        "sentence_words_p50": sw.get("p50", 0.0),
        "sentence_words_p90": sw.get("p90", 0.0),
        "short_sentence_share": profile.get("short_sentence_share", 0.0),
        "question_rate": profile.get("question_rate", 0.0),
        "exclamation_rate": profile.get("exclamation_rate", 0.0),
        "contractions_per_100": per100.get("contractions", 0.0),
        "first_person_per_100": per100.get("first_person_singular", 0.0),
        "top_openers": [o["opener"] for o in profile.get("top_openers", [])[:5]],
    }


EXTENDED_ANALYSIS_KEYS = ("humor", "under_pressure", "stances", "voice_calibration", "contradictions", "knowledge_boundaries", "relationships")


def assemble(store: Store, analysis: dict[str, Any], budgets: dict[str, int] | None = None,
             quality_level: str = "research-backed") -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge agent analysis + measured profile + corpus pointers into a v2 pack. Returns (pack, report)."""
    budgets = {**DEFAULT_BUDGETS, **(budgets or {})}
    manifest = store.manifest()
    utterance_rows = read_jsonl(store.utterances_path)
    if store.stylometry_path.is_file():
        profile = json.loads(store.stylometry_path.read_text(encoding="utf-8"))
    else:
        profile = stylometry(utterance_rows)
        write_json(store.stylometry_path, profile)
    utterances = {u["id"]: u for u in utterance_rows}
    sources = store.sources()

    pack: dict[str, Any] = {"schema_version": PACK_SCHEMA_VERSION, "id": store.id}
    for key in ("display_name", "summary", "voice"):
        if key in analysis:
            pack[key] = analysis[key]
    core = dict(analysis.get("core") or {})
    core.setdefault("identity", analysis.get("summary", ""))
    pack["core"] = core
    for key in LAYER_FIELDS["standard"]:
        if key in analysis:
            pack[key] = analysis[key]

    idiolect = dict(analysis.get("idiolect") or {})
    if not idiolect.get("signature_phrases"):
        idiolect["signature_phrases"] = [
            {"phrase": m["phrase"], "evidence": m["evidence"], "frequency": m["count"], "use": "sparingly"}
            for m in profile.get("signature_candidates", [])[:8]
        ]
    if not idiolect.get("discourse_markers"):
        idiolect["discourse_markers"] = list(profile.get("discourse_markers_per_1k", {}))[:6]
    idiolect["stylometry"] = stylometry_summary(profile)
    pack["idiolect"] = idiolect
    for key in EXTENDED_ANALYSIS_KEYS:
        if analysis.get(key):
            pack[key] = analysis[key]

    examples = []
    for item in analysis.get("example_utterances") or []:
        ev = item.get("evidence") if isinstance(item, dict) else item
        utt = utterances.get(ev)
        if utt is None:
            raise SystemExit(f"example utterance {ev!r} is not an utterance id in the corpus")
        context = (item.get("context") if isinstance(item, dict) else None) or utt.get("context", "unknown")
        # text always comes from the corpus, so examples are verbatim by construction
        examples.append({"text": utt["text"], "evidence": ev, "context": context})
    if examples:
        pack["example_utterances"] = {
            "usage": "shape-not-lines",
            "note": "Show rhythm, length and stance. Do not paste these lines; vary wording every reply.",
            "items": examples,
        }

    counts = manifest.get("counts", {})
    pack["retrieval"] = {
        "store": f"${{XDG_DATA_HOME:-~/.local/share}}/personify/research/{store.id}",
        "corpus_sha": manifest.get("corpus_sha"),
        "chunks": counts.get("chunks", 0),
        "utterances": counts.get("utterances", 0),
        "method": "bm25",
        "embeddings": manifest.get("embeddings"),
        "top_k": 3,
        "max_injected_tokens": 400,
        "command": f"python3 <extract-persona skill dir>/scripts/persona_extract.py retrieve {store.id} \"<query>\"",
        "inject_when": analysis.get("retrieval_inject_when") or [
            "the task touches a topic listed in stances or knowledge_boundaries",
            "the voice drifts generic and fresh shape examples are needed",
            "the user asks what the persona actually said about something",
        ],
    }
    pack["layers"] = make_layers(budgets)

    prov = dict(analysis.get("provenance") or {})
    pack["provenance"] = {
        "source_type": prov.get("source_type", "research-backed"),
        "created_by": "extract-persona",
        "sources": [s["url"] for s in sources if s.get("url")],
        "source_records": [
            {k: s.get(k) for k in ("id", "url", "title", "source_type", "attribution", "voice", "context", "published", "retrieved_at")}
            for s in sources
        ],
        "extraction": {
            "tool_version": TOOL_VERSION,
            "pack_schema_version": PACK_SCHEMA_VERSION,
            "extracted_at": now_iso(),
            "corpus_sha": manifest.get("corpus_sha"),
            "stylometry_basis_words": profile.get("words", 0),
        },
        "notes": prov.get("notes") or f"Assembled from {len(sources)} sources and {len(utterances)} attributed utterances in the research store.",
    }
    pack["quality_level"] = quality_level

    trimmed = fit_extended(pack, budgets["extended"])
    return pack, {"budget": budget_report(pack), "trimmed_to_store": trimmed}


def fit_extended(pack: dict[str, Any], budget: int) -> list[str]:
    """Drop lowest-priority extended items until the layer fits. Dropped items stay in analysis.json."""
    trimmed: list[str] = []
    while layer_tokens(pack, "extended") > budget:
        for key, sub in EXTENDED_TRIM_ORDER:
            container = pack.get(key)
            target = container.get(sub) if (sub and isinstance(container, dict)) else container
            if isinstance(target, list) and len(target) > 1:
                dropped = target.pop()
                trimmed.append(f"{key}{'.' + sub if sub else ''}: {json.dumps(dropped, ensure_ascii=False)[:80]}")
                break
        else:
            break
    return trimmed


# --------------------------------------------------------------------------- migration v1 -> v2

def migrate_v1(pack: dict[str, Any]) -> dict[str, Any]:
    """Non-destructive: every v1 field is kept; core + layers + extraction metadata are added."""
    if pack.get("schema_version") == PACK_SCHEMA_VERSION:
        return pack
    markers = list(pack.get("speech_patterns") or [])[:3] or list(pack.get("preferred_terminology") or [])[:3]
    core = {
        "identity": str(pack.get("summary", "")).strip(),
        "voice_markers": markers,
        "reasoning_habits": list(pack.get("reasoning_style") or [])[:2],
    }
    out: dict[str, Any] = {"schema_version": PACK_SCHEMA_VERSION}
    for key in ("id", "display_name", "summary", "voice"):
        if key in pack:
            out[key] = pack[key]
    out["core"] = core
    for key, value in pack.items():
        if key not in out and key not in ("provenance", "quality_level", "schema_version"):
            out[key] = value
    out["layers"] = make_layers(dict(DEFAULT_BUDGETS))
    for name in ("core", "standard", "extended"):
        used = layer_tokens(out, name)
        if used > DEFAULT_BUDGETS[name]:
            # Never fail a migration on size: record the real size so the pack stays valid and the overrun is visible.
            out["layers"][name]["budget_tokens"] = int(math.ceil(used / 50.0) * 50)
            out["layers"][name]["note"] = f"raised from {DEFAULT_BUDGETS[name]} on migration; trim this layer to restore the default"
    prov = dict(pack.get("provenance") or {"source_type": "unknown"})
    prov["extraction"] = {
        "tool_version": TOOL_VERSION, "pack_schema_version": PACK_SCHEMA_VERSION,
        "migrated_from_schema": 1, "extracted_at": now_iso(), "corpus_sha": None,
    }
    out["provenance"] = prov
    out["quality_level"] = pack.get("quality_level", "draft")
    return out


# --------------------------------------------------------------------------- CLI

def _store(args: argparse.Namespace) -> Store:
    return Store(research_root(args.root), args.persona_id)


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_init(args) -> int:
    _print(_store(args).init(args.name, args.alias or [], args.kind, args.role))
    return 0


def cmd_add_source(args) -> int:
    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    meta = {k: getattr(args, k) for k in ("url", "title", "source_type", "attribution", "voice", "context", "published", "language", "rights_note")}
    record, added = _store(args).add_source(text, meta)
    _print({"added": added, "source": record})
    return 0


def cmd_index(args) -> int:
    _print(index_store(_store(args), rebuild=args.rebuild))
    return 0


def cmd_profile(args) -> int:
    store = _store(args)
    profile = stylometry(read_jsonl(store.utterances_path))
    write_json(store.stylometry_path, profile)
    _print(profile)
    return 0


def cmd_status(args) -> int:
    report = coverage(_store(args), args.min_sources, args.min_verbatim_words)
    _print(report)
    return 0


def cmd_retrieve(args) -> int:
    _print(retrieve(_store(args), args.query, k=args.k, kind=args.kind, max_tokens=args.max_tokens))
    return 0


def cmd_assemble(args) -> int:
    store = _store(args)
    analysis_file = Path(args.analysis) if args.analysis else store.analysis_path
    analysis = json.loads(analysis_file.read_text(encoding="utf-8"))
    if analysis_file.resolve() != store.analysis_path.resolve():
        if store.analysis_path.is_file():
            hist = store.dir / "analysis" / "history" / f"analysis-{stamp()}.json"
            hist.parent.mkdir(parents=True, exist_ok=True)
            hist.write_text(store.analysis_path.read_text(encoding="utf-8"), encoding="utf-8")
        write_json(store.analysis_path, analysis)
    budgets = {k: v for k, v in (("core", args.core_budget), ("standard", args.standard_budget), ("extended", args.extended_budget)) if v}
    pack, report = assemble(store, analysis, budgets, quality_level=args.quality_level)
    errors = validate_pack(pack, store)
    if errors:
        _print({"ok": False, "errors": errors, "report": report})
        return 1
    text = to_yaml(pack)
    (store.dir / "packs").mkdir(parents=True, exist_ok=True)
    (store.dir / "packs" / f"{store.id}-{stamp()}.yaml").write_text(text, encoding="utf-8")
    out = Path(args.out) if args.out else personas_dir() / f"{store.id}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    store.log({"event": "assemble", "pack": str(out), "corpus_sha": store.manifest().get("corpus_sha")})
    _print({"ok": True, "pack": str(out), "report": report})
    return 0


def load_pack_file(path: Path) -> Any:
    return load_yaml(path.read_text(encoding="utf-8"))


def cmd_validate(args) -> int:
    store = Store(research_root(args.root), args.store) if args.store else None
    failed = 0
    for p in args.packs:
        pack = load_pack_file(Path(p))
        errors = validate_pack(pack, store)
        if isinstance(pack, dict) and pack.get("id") and Path(p).stem != pack["id"]:
            errors.append(f"$.id: {pack['id']!r} must match filename stem {Path(p).stem!r}")
        version = pack.get("schema_version", 1) if isinstance(pack, dict) else "?"
        print(f"{'ok' if not errors else 'FAIL'}: {p} (schema v{version})")
        for e in errors:
            print(f"  {e}")
        failed += bool(errors)
    return 1 if failed else 0


def cmd_migrate(args) -> int:
    migrated = migrate_v1(load_pack_file(Path(args.pack)))
    errors = validate_pack(migrated, None, check_budget=False)
    if errors:
        _print({"ok": False, "errors": errors})
        return 1
    text = to_yaml(migrated)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def cmd_budget(args) -> int:
    _print(budget_report(load_pack_file(Path(args.pack))))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="extract-persona: research store, corpus index, stylometry and v2 pack assembly (offline, stdlib).")
    p.add_argument("--version", action="version", version=TOOL_VERSION)
    sub = p.add_subparsers(dest="command", required=True)

    def with_store(name: str, help_text: str) -> argparse.ArgumentParser:
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("persona_id")
        sp.add_argument("--root", help="research root (default $PERSONIFY_RESEARCH_DIR or $XDG_DATA_HOME/personify/research)")
        return sp

    sp = with_store("init", "create or update a research store")
    sp.add_argument("--name", required=True, help="display name of the person or character")
    sp.add_argument("--alias", action="append", help="speaker label or alias used in transcripts (repeatable)")
    sp.add_argument("--kind", choices=("real-person", "fictional", "composite"), default="real-person")
    sp.add_argument("--role", help="target role/use-case")
    sp.set_defaults(func=cmd_init)

    sp = with_store("add-source", "store a captured source (file path, or - for stdin)")
    sp.add_argument("file")
    sp.add_argument("--url")
    sp.add_argument("--title")
    sp.add_argument("--type", dest="source_type", choices=SOURCE_TYPES, default="other")
    sp.add_argument("--attribution", choices=ATTRIBUTIONS, default="about",
                    help="subject: all text is the subject's own words; mixed: speaker-labelled transcript; about: third-party text")
    sp.add_argument("--voice", choices=("verbatim", "paraphrase", "summary"), default="verbatim")
    sp.add_argument("--context", choices=CONTEXTS, default="unknown")
    sp.add_argument("--published", help="publication/recording date if known (YYYY-MM-DD)")
    sp.add_argument("--language", default="en")
    sp.add_argument("--rights-note", dest="rights_note", help="origin/rights note, required when there is no URL")
    sp.set_defaults(func=cmd_add_source)

    sp = with_store("index", "chunk + extract utterances for new or changed sources (incremental)")
    sp.add_argument("--rebuild", action="store_true")
    sp.set_defaults(func=cmd_index)

    sp = with_store("profile", "measure the stylometric profile from the subject's utterances")
    sp.set_defaults(func=cmd_profile)

    sp = with_store("status", "coverage gate: sources, variety, verbatim volume, pressure context")
    sp.add_argument("--min-sources", type=int, default=3)
    sp.add_argument("--min-verbatim-words", type=int, default=3000)
    sp.set_defaults(func=cmd_status)

    sp = with_store("retrieve", "BM25 search over utterances and chunks (per-turn injection)")
    sp.add_argument("query")
    sp.add_argument("-k", type=int, default=3)
    sp.add_argument("--kind", choices=("all", "utterance", "chunk"), default="all")
    sp.add_argument("--max-tokens", type=int, default=400)
    sp.set_defaults(func=cmd_retrieve)

    sp = with_store("assemble", "build and validate a v2 pack from analysis JSON")
    sp.add_argument("--analysis", help="analysis JSON (default: the store's analysis/analysis.json)")
    sp.add_argument("--out", help="pack path (default: $XDG_DATA_HOME/personify/personas/<id>.yaml)")
    sp.add_argument("--quality-level", choices=("draft", "reviewed", "research-backed"), default="research-backed")
    sp.add_argument("--core-budget", type=int)
    sp.add_argument("--standard-budget", type=int)
    sp.add_argument("--extended-budget", type=int)
    sp.set_defaults(func=cmd_assemble)

    sp = sub.add_parser("validate", help="validate pack files against the schema (v1 and v2)")
    sp.add_argument("packs", nargs="+")
    sp.add_argument("--store", help="persona id whose research store resolves evidence ids")
    sp.add_argument("--root")
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("migrate", help="migrate a v1 pack to v2 (keeps every v1 field)")
    sp.add_argument("pack")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_migrate)

    sp = sub.add_parser("budget", help="per-layer token estimate for a pack")
    sp.add_argument("pack")
    sp.set_defaults(func=cmd_budget)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
