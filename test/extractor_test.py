#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PERSONA_EXTRACT = ROOT_DIR / "skills" / "persona-extract" / "SKILL.md"
PERSONA_EXTRACT_ONLINE = ROOT_DIR / "skills" / "persona-extract-online" / "SKILL.md"


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"expected to find {needle!r}"


def main() -> None:
    local_text = PERSONA_EXTRACT.read_text(encoding="utf-8")
    online_text = PERSONA_EXTRACT_ONLINE.read_text(encoding="utf-8")

    print("=== promptonality extractor test ===")

    print("1. local extractor is pack-first")
    assert_contains(local_text, "normalized `promptonality` personality pack")
    assert_contains(local_text, "The primary deliverable is pack YAML")
    assert_contains(local_text, "`speech_patterns`")
    assert_contains(local_text, "`preferred_terminology`")
    assert_contains(local_text, "Wise teacher\" is not enough for Yoda")
    assert_contains(local_text, "name: persona-extract")
    print("ok")

    print("2. online extractor preserves research-backed speech extraction")
    assert_contains(online_text, "normalized `promptonality` personality pack")
    assert_contains(online_text, "Signature terminology, metaphors, or repeated turns of phrase")
    assert_contains(online_text, "Distinctive syntax or cadence markers that make the voice recognizable")
    assert_contains(online_text, "Do not reduce a character like Yoda to \"wise\" and \"patient\"")
    assert_contains(online_text, "Preserve signature language markers in structured fields")
    assert_contains(online_text, "name: persona-extract-online")
    print("ok")

    print("=== extractor test passed ===")


if __name__ == "__main__":
    main()
