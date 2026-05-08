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

    print("=== extractor test passed ===")


if __name__ == "__main__":
    main()
