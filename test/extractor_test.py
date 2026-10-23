#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PERSONA_EXTRACT_ONLINE = ROOT_DIR / "src" / "skills" / "extract-persona" / "SKILL.md"


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"expected to find {needle!r}"


def main() -> None:
    online_text = PERSONA_EXTRACT_ONLINE.read_text(encoding="utf-8")

    print("=== personify extractor test ===")

    print("1. extractor preserves research-backed speech extraction")
    assert_contains(online_text, "normalized Personify persona pack")
    assert_contains(online_text, "Signature terminology, metaphors, or repeated turns of phrase")
    assert_contains(online_text, "Distinctive syntax or cadence markers that make the voice recognizable")
    assert_contains(online_text, "Do not reduce a character like Yoda to \"wise\" and \"patient\"")
    assert_contains(online_text, "Preserve signature language markers in structured fields")
    assert_contains(online_text, "name: extract-persona")
    print("ok")

    print("2. extractor keeps a research store, measures voice, and assembles a layered pack")
    for needle in (
        "personify/research/<id>/",
        "scripts/persona_extract.py",
        "references/persona-pack.schema.json",
        "--attribution subject|mixed|about",
        "Run `status <id>`",
        "Run `profile <id>`",
        "evidence ids",
        "inferred\": true",
        "usage: shape-not-lines",
        "$X assemble <id> --analysis analysis.json",
        "migrate <pack> --out <pack>",
        "At least one pressure or conflict context",
        "Do not include `guardrails`, `anti_patterns`",
        "${XDG_DATA_HOME:-~/.local/share}/personify/personas/<id>.yaml",
    ):
        assert_contains(online_text, needle)
    assert (ROOT_DIR / "src" / "skills" / "extract-persona" / "scripts" / "persona_extract.py").is_file()
    assert (ROOT_DIR / "src" / "skills" / "extract-persona" / "references" / "persona-pack.schema.json").is_file()
    print("ok")

    print("=== extractor test passed ===")


if __name__ == "__main__":
    main()
