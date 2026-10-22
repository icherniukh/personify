#!/usr/bin/env python3
"""Offline tests for the extract-persona research store, corpus, stylometry and v2 pack assembly."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT = ROOT_DIR / "src" / "skills" / "extract-persona" / "scripts" / "persona_extract.py"
FIXTURES = ROOT_DIR / "test" / "fixtures" / "extract_persona"
PERSONALITIES_DIR = ROOT_DIR / "src" / "assets" / "personalities"
sys.path.insert(0, str(ROOT_DIR / "test"))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


pe = load_module(SCRIPT, "persona_extract")
contract = load_module(ROOT_DIR / "test" / "personality_pack_contract_test.py", "pack_contract")
packet_builder = load_module(ROOT_DIR / "test" / "packet_builder.py", "packet_builder_for_extract")

SOURCES = {
    "podcast-harbor-talk": dict(url="https://example.test/harbor-talk", source_type="podcast", attribution="mixed", context="casual", published="2024-05-01"),
    "essay-fix-the-boat": dict(url="https://example.test/essay", source_type="writing", attribution="subject", context="work"),
    "profile-article": dict(url="https://example.test/profile", source_type="article-about", attribution="about", context="public"),
    "hearing-transcript": dict(url="https://example.test/hearing", source_type="transcript", attribution="mixed", context="pressure"),
}


def fixture_text(stem: str) -> str:
    return (FIXTURES / f"{stem}.txt").read_text(encoding="utf-8")


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


def build_store(root: Path, stems=("podcast-harbor-talk", "essay-fix-the-boat", "profile-article", "hearing-transcript")):
    store = pe.Store(root, "marlow-vance")
    store.init("Marlow Vance", [], "fictional", "maintenance-minded reviewer")
    ids = {}
    for stem in stems:
        record, _ = store.add_source(fixture_text(stem), SOURCES[stem])
        ids[stem] = record["id"]
    pe.index_store(store)
    return store, ids


def resolve(analysis, store, source_ids):
    """Replace '@stem' with the source id and '@stem:n' with the n-th subject utterance of that source."""
    utterances = pe.read_jsonl(store.utterances_path)

    def lookup(token: str) -> str:
        stem, _, n = token[1:].partition(":")
        sid = source_ids[stem]
        if not n:
            return sid
        own = [u["id"] for u in utterances if u["source_id"] == sid]
        return own[int(n)]

    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str) and node.startswith("@"):
            return lookup(node)
        return node

    return walk(analysis)


def fixture_analysis(store, ids):
    return resolve(json.loads((FIXTURES / "analysis.json").read_text(encoding="utf-8")), store, ids)


def check(label: str) -> None:
    print(f"{label}")


def test_store_dedupe_and_provenance(tmp: Path) -> None:
    check("1. sources are stored raw + normalized with provenance; duplicates merge")
    store = pe.Store(tmp, "marlow-vance")
    store.init("Marlow Vance", ["Captain Vance"], "fictional", None)
    rec, added = store.add_source(fixture_text("podcast-harbor-talk"), SOURCES["podcast-harbor-talk"])
    assert added and rec["id"].startswith("src-") and len(rec["sha256"]) == 64
    assert (store.dir / "sources" / "raw" / f"{rec['id']}.txt").read_text(encoding="utf-8") == fixture_text("podcast-harbor-talk")
    normalized = store.normalized_text(rec["id"])
    assert "00:00" not in normalized, "timestamps are stripped from the normalized copy"
    again, added_again = store.add_source(fixture_text("podcast-harbor-talk") + "\n\n", {**SOURCES["podcast-harbor-talk"], "url": "https://mirror.test/harbor"})
    assert not added_again and again["id"] == rec["id"]
    assert again["alt_urls"] == ["https://mirror.test/harbor"]
    assert len(store.sources()) == 1
    for key in ("url", "source_type", "attribution", "voice", "context", "published", "retrieved_at", "words"):
        assert key in rec, key
    manifest = store.manifest()
    assert manifest["subject"]["aliases"] == ["Captain Vance", "Marlow Vance", "Vance"]
    print("ok")


def test_attribution_and_incremental_index(tmp: Path) -> None:
    check("2. utterances are speaker-attributed; indexing is incremental with stable ids")
    store, ids = build_store(tmp, stems=("podcast-harbor-talk", "essay-fix-the-boat", "profile-article"))
    utts = pe.read_jsonl(store.utterances_path)
    podcast = [u for u in utts if u["source_id"] == ids["podcast-harbor-talk"]]
    assert podcast and all(u["speaker"] == "Marlow Vance" and u["kind"] == "verbatim" for u in podcast)
    assert not any("Welcome back" in u["text"] for u in utts), "host turns are not subject utterances"
    assert podcast[1]["prev_turn"].startswith("Host: People say"), "the turn being answered is kept as context"
    article = [u for u in utts if u["source_id"] == ids["profile-article"]]
    assert article and all(u["kind"] == "secondary-quote" for u in article)
    assert not any("shoelace" in u["text"] for u in article), "quotes attributed to other people are excluded"
    dup = [u for u in utts if u["text"].lower().strip(" ,.") == "we fix the boat we have"]
    assert len(dup) == 1 and dup[0]["also_in"] == [ids["profile-article"]], "a line found in two sources is stored once with also_in"
    before = {u["id"]: u["text"] for u in utts}
    chunks = pe.read_jsonl(store.chunks_path)
    assert all(c["id"].startswith(c["source_id"] + "#c") and c["sha"] and c["tokens"] > 0 for c in chunks)

    again = pe.index_store(store)
    assert again["new_sources"] == 0
    rec, _ = store.add_source(fixture_text("hearing-transcript"), SOURCES["hearing-transcript"])
    result = pe.index_store(store)
    assert result["new_sources"] == 1 and result["sources"] == 4
    after = {u["id"]: u["text"] for u in pe.read_jsonl(store.utterances_path)}
    assert all(after[k] == v for k, v in before.items()), "existing utterance ids are stable across incremental runs"
    hearing = [u for u in after if u.startswith("u-" + rec["id"][4:12])]
    assert len(hearing) == 5, hearing
    assert pe.read_jsonl(store.utterances_path)[-1]["context"] == "pressure"
    manifest = store.manifest()
    assert [h["event"] for h in manifest["history"]].count("index") == 3
    assert manifest["corpus_sha"] == result["corpus_sha"]
    rebuilt = pe.index_store(store, rebuild=True)
    assert rebuilt["corpus_sha"] == result["corpus_sha"], "a full rebuild reproduces the same corpus"
    print("ok")


def test_coverage_gate(tmp: Path) -> None:
    check("3. coverage gate flags missing pressure context and thin verbatim volume")
    store, _ = build_store(tmp, stems=("podcast-harbor-talk", "essay-fix-the-boat", "profile-article"))
    report = pe.coverage(store)
    status = {c["check"]: c["ok"] for c in report["checks"]}
    assert status["distinct_sources"] and status["source_type_variety"] and status["provenance"] and status["indexed"]
    assert not status["pressure_context"] and not status["verbatim_volume"] and not report["ready"]
    store.add_source(fixture_text("hearing-transcript"), SOURCES["hearing-transcript"])
    assert not {c["check"]: c["ok"] for c in pe.coverage(store)["checks"]}["indexed"]
    pe.index_store(store)
    report = pe.coverage(store, min_verbatim_words=200)
    assert report["ready"], report
    print("ok")


def test_stylometry(tmp: Path) -> None:
    check("4. stylometry measures sentence shape and finds cross-source signature phrases")
    store, _ = build_store(tmp)
    profile = pe.stylometry(pe.read_jsonl(store.utterances_path))
    assert profile["basis"] == "verbatim" and profile["words"] > 250
    assert sum(profile["sentence_words"]["histogram"].values()) == profile["sentences"]
    assert profile["sentence_words"]["p50"] <= 8, "the subject speaks in short sentences"
    assert profile["short_sentence_share"] > 0.3
    phrases = [c["phrase"] for c in profile["signature_candidates"]]
    assert "plain as rope" in phrases and "here's the thing" in phrases and "we fix the boat we have" in phrases, phrases
    assert "we fix the boat we" not in phrases, "sub-phrases with the same support are folded into the longer phrase"
    assert all(c["sources"] >= 2 for c in profile["signature_candidates"])
    assert "here's the thing" in profile["discourse_markers_per_1k"]
    assert pe.stylometry([])["basis"] == "none"
    print("ok")


def test_retrieval(tmp: Path) -> None:
    check("5. BM25 retrieval returns evidence-addressable, budget-capped results")
    store, _ = build_store(tmp)
    results = pe.retrieve(store, "should we replace old equipment or repair it", k=3, max_tokens=120)
    assert 1 <= len(results) <= 3
    assert sum(pe.estimate_tokens(r["text"]) for r in results) <= 120
    known = pe.evidence_ids(store)
    assert all(r["id"] in known and r["usage"] == "shape-not-lines" for r in results)
    assert "boat we have" in results[0]["text"].lower()
    only_chunks = pe.retrieve(store, "fog schedule board", kind="chunk")
    assert only_chunks and all(r["kind"] == "chunk" for r in only_chunks)
    assert pe.retrieve(store, "quantum chromodynamics") == []
    print("ok")


def test_assemble_v2_pack(tmp: Path) -> None:
    check("6. assemble builds a valid, layered, evidence-mapped v2 pack")
    store, ids = build_store(tmp)
    analysis = fixture_analysis(store, ids)
    pack, report = pe.assemble(store, analysis)
    errors = pe.validate_pack(pack, store)
    assert not errors, errors
    assert pack["schema_version"] == 2 and pack["quality_level"] == "research-backed"
    for key in contract.TOP_LEVEL_REQUIRED:
        assert key in pack, f"v1 field {key} kept for backward compatibility"
    assert set(pack["layers"]) == {"core", "standard", "extended", "retrievable"}
    assert report["budget"]["core"]["ok"] and report["budget"]["standard"]["ok"] and report["budget"]["extended"]["ok"]
    texts = {u["id"]: u["text"] for u in pe.read_jsonl(store.utterances_path)}
    examples = pack["example_utterances"]
    assert examples["usage"] == "shape-not-lines"
    assert all(item["text"] == texts[item["evidence"]] for item in examples["items"]), "examples are verbatim corpus lines"
    assert pack["idiolect"]["stylometry"]["basis"] == "verbatim"
    assert len(pack["provenance"]["source_records"]) == 4
    assert pack["provenance"]["extraction"]["corpus_sha"] == store.manifest()["corpus_sha"]
    assert pack["retrieval"]["method"] == "bm25" and pack["retrieval"]["utterances"] == len(texts)
    assert pack["retrieval"]["top_k"] <= 5

    text = pe.to_yaml(pack)
    assert pe.load_yaml(text) == pack, "pack round-trips through the stdlib YAML subset"
    try:
        import yaml  # optional: only used to prove the output is standard YAML
    except ImportError:
        print("   (PyYAML not installed; standard-YAML round-trip skipped)")
    else:
        assert yaml.safe_load(text) == pack, "pack is standard YAML"

    out = tmp / "marlow-vance.yaml"
    out.write_text(text, encoding="utf-8")
    lines = text.splitlines()
    keys = contract.top_level_keys(lines)
    assert not (contract.TOP_LEVEL_REQUIRED - keys.keys())
    for key in contract.LIST_SECTIONS:
        assert contract.has_list_item(lines, key), key
    for key in contract.BLOCK_SECTIONS:
        assert contract.has_block_content(lines, key), key
    assert not any(p in text for p in contract.FORBIDDEN_MECHANICAL_PHRASES)
    parsed = packet_builder.parse_simple_yaml(out)
    assert parsed["id"] == "marlow-vance" and parsed["reasoning_style"] and parsed["prompt_overlay"]
    packet = packet_builder.build_instruction_packet(packet_builder.NEUTRAL_TASK, parsed)
    assert "Persona id: marlow-vance" in packet and "Overlay prompt:" in packet, "the activation packet builder still reads a v2 pack"
    print("ok")


def test_grounding_rules(tmp: Path) -> None:
    check("7. grounding: unknown evidence ids and unmarked inferences fail validation")
    store, ids = build_store(tmp)
    analysis = fixture_analysis(store, ids)
    bad = copy.deepcopy(analysis)
    bad["stances"].append({"topic": "bridges", "position": "bridges are for cowards", "evidence": ["u-deadbeef-9"]})
    bad["under_pressure"].append({"behavior": "throws chairs"})
    pack, _ = pe.assemble(store, bad)
    errors = pe.validate_pack(pack, store)
    assert any("unknown evidence ids" in e for e in errors), errors
    assert any("needs evidence ids or inferred" in e for e in errors), errors
    ok = copy.deepcopy(analysis)
    ok["under_pressure"].append({"behavior": "probably checks the logbook first", "inferred": True})
    pack, _ = pe.assemble(store, ok)
    assert not pe.validate_pack(pack, store)
    bad_example = copy.deepcopy(analysis)
    bad_example["example_utterances"] = [{"evidence": ids["essay-fix-the-boat"]}]
    try:
        pe.assemble(store, bad_example)
    except SystemExit as exc:
        assert "not an utterance id" in str(exc)
    else:
        raise AssertionError("examples must reference corpus utterances")
    guarded = dict(pack, guardrails=["no"])
    assert any("guardrails" in e for e in pe.validate_pack(guarded, store))
    print("ok")


def test_budget_trimming(tmp: Path) -> None:
    check("8. an over-budget extended layer is trimmed into the store, never silently lost")
    store, ids = build_store(tmp)
    analysis = fixture_analysis(store, ids)
    pack, report = pe.assemble(store, analysis, budgets={"extended": 700})
    assert report["trimmed_to_store"], "something was trimmed"
    assert report["budget"]["extended"]["estimated_tokens"] < pe.assemble(store, analysis)[1]["budget"]["extended"]["estimated_tokens"]
    assert report["trimmed_to_store"][0].startswith("relationships"), "lowest priority goes first"
    small, _ = pe.assemble(store, dict(analysis, core=dict(analysis["core"], identity="x " * 900)))
    assert any("layers.core" in e for e in pe.validate_pack(small, store)), "core over budget is an error"
    print("ok")


def test_cli_assemble_writes_history(tmp: Path) -> None:
    check("9. CLI assemble keeps analysis history, pack history and writes the user pack")
    store, ids = build_store(tmp)
    analysis_file = tmp / "analysis.json"
    analysis_file.write_text(json.dumps(fixture_analysis(store, ids)), encoding="utf-8")
    out = tmp / "personas" / "marlow-vance.yaml"
    args = ["assemble", "marlow-vance", "--root", str(tmp), "--analysis", str(analysis_file), "--out", str(out)]
    code, stdout = quiet(pe.main, args)
    assert code == 0, stdout
    assert json.loads(stdout)["ok"]
    code, _ = quiet(pe.main, args)
    assert code == 0
    assert len(list((store.dir / "packs").glob("*.yaml"))) == 2
    assert len(list((store.dir / "analysis" / "history").glob("*.json"))) == 1
    assert store.analysis_path.is_file()
    code, stdout = quiet(pe.main, ["validate", str(out), "--store", "marlow-vance", "--root", str(tmp)])
    assert code == 0, stdout
    assert [h["event"] for h in store.manifest()["history"]].count("assemble") == 2
    print("ok")


def test_backward_compat_and_migration(tmp: Path) -> None:
    check("10. bundled v1 packs validate unchanged and migrate losslessly to v2")
    paths = sorted(PERSONALITIES_DIR.glob("*.yaml"))
    code, stdout = quiet(pe.main, ["validate", *map(str, paths)])
    assert code == 0, stdout
    for path in paths:
        v1 = pe.load_pack_file(path)
        assert "schema_version" not in v1
        v2 = pe.migrate_v1(v1)
        assert not pe.validate_pack(v2, None), path.name
        assert all(v2[k] == v for k, v in v1.items() if k != "provenance"), "every v1 field survives"
        assert v2["provenance"]["extraction"]["migrated_from_schema"] == 1
        text = pe.to_yaml(v2)
        assert pe.load_yaml(text) == v2
        lines = text.splitlines()
        for key in contract.BLOCK_SECTIONS:
            assert contract.has_block_content(lines, key), (path.name, key)
        assert pe.migrate_v1(v2) is v2, "migration is idempotent"
    dababy = pe.migrate_v1(pe.load_pack_file(PERSONALITIES_DIR / "dababy.yaml"))
    assert dababy["layers"]["core"]["budget_tokens"] > pe.DEFAULT_BUDGETS["core"] and "note" in dababy["layers"]["core"], "overruns are recorded, not hidden"
    out = tmp / "yoda.yaml"
    code, _ = quiet(pe.main, ["migrate", str(PERSONALITIES_DIR / "yoda.yaml"), "--out", str(out)])
    assert code == 0 and pe.load_pack_file(out)["schema_version"] == 2
    print("ok")


def test_yaml_emitter_is_standard_yaml(_tmp: Path) -> None:
    check("11. YAML emitter output is standard YAML for awkward strings")
    cases = ["a, b", "it's", "x: y", "x #y", "- dash", "[a]", "{a}", "yes", "No", "1.5", "007", "2024-01-01",
             "@x", "!x", "&x", "*x", "|x", ">x", "trailing:", "?x", "'q' b", '"q" b', "tab\tx", "null", "~",
             " lead", "trail ", "multi\nline", "multi\nline\n", "\nlead nl", "a\n\n\nb", "", "é 中"]
    try:
        import yaml
    except ImportError:
        yaml = None
    for case in cases:
        doc = {"k": case, "l": [case, {"m": case}]}
        text = pe.to_yaml(doc)
        assert pe.load_yaml(text) == doc, (case, text)
        if yaml is not None:
            assert yaml.safe_load(text) == doc, (case, text)
    print("ok" if yaml else "ok (stdlib loader only; PyYAML not installed)")


def test_offline_and_versioned() -> None:
    check("12. tool stays offline and carries the package version")
    source = SCRIPT.read_text(encoding="utf-8")
    for banned in ("import urllib", "import http", "import socket", "import requests", "openrouter", "OPENAI_API_KEY"):
        assert banned not in source, banned
    meta = json.loads((ROOT_DIR / "src" / "package.json").read_text(encoding="utf-8"))
    assert pe.TOOL_VERSION == meta["version"], "script version follows src/package.json"
    schema = pe.load_schema()
    assert schema["x-personify-version"] == meta["version"]
    print("ok")


def main() -> None:
    print("=== extract-persona store/corpus/schema test ===")
    os.environ.pop("PERSONIFY_RESEARCH_DIR", None)
    tests = (
        test_store_dedupe_and_provenance, test_attribution_and_incremental_index, test_coverage_gate,
        test_stylometry, test_retrieval, test_assemble_v2_pack, test_grounding_rules, test_budget_trimming,
        test_cli_assemble_writes_history, test_backward_compat_and_migration, test_yaml_emitter_is_standard_yaml,
    )
    for test in tests:
        with tempfile.TemporaryDirectory() as tmp:
            test(Path(tmp))
    test_offline_and_versioned()
    print("=== extract-persona test passed ===")


if __name__ == "__main__":
    main()
