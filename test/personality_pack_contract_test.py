#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PERSONALITIES_DIR = ROOT_DIR / "src" / "assets" / "personalities"

TOP_LEVEL_REQUIRED = {
    "id",
    "display_name",
    "summary",
    "voice",
    "interaction_stance",
    "value_profile",
    "reasoning_style",
    "preferred_terminology",
    "speech_patterns",
    "default_structures",
    "ambiguity_policy",
    "tradeoff_policy",
    "compression_policy",
    "interaction_rules",
    "prompt_overlay",
    "provenance",
    "quality_level",
}

LIST_SECTIONS = {
    "interaction_stance",
    "value_profile",
    "reasoning_style",
    "preferred_terminology",
    "speech_patterns",
    "default_structures",
    "interaction_rules",
}

BLOCK_SECTIONS = {
    "ambiguity_policy",
    "tradeoff_policy",
    "compression_policy",
    "prompt_overlay",
}

ALLOWED_QUALITY = {"draft", "reviewed", "research-backed"}
FORBIDDEN_TOP_LEVEL = {"guardrails", "anti_patterns"}


def top_level_keys(lines: list[str]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        keys[key] = value.strip()
    return keys


def has_list_item(lines: list[str], key: str) -> bool:
    in_section = False
    base_indent = 0
    for line in lines:
        if not in_section:
            if line.startswith(f"{key}:"):
                in_section = True
                base_indent = len(line) - len(line.lstrip(" "))
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= base_indent:
            return False
        if line.strip().startswith("- "):
            return True
    return False


def has_block_content(lines: list[str], key: str) -> bool:
    in_section = False
    block_indent = None
    for line in lines:
        if not in_section:
            if line.startswith(f"{key}: |"):
                in_section = True
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if block_indent is None:
            block_indent = indent
        if indent < block_indent:
            return False
        return True
    return False


def main() -> None:
    print("=== promptonality personality pack contract test ===")
    paths = sorted(PERSONALITIES_DIR.glob("*.yaml"))
    assert paths, f"no packs found in {PERSONALITIES_DIR}"

    seen_ids: set[str] = set()
    for path in paths:
        print(f"checking {path.name}")
        lines = path.read_text(encoding="utf-8").splitlines()
        keys = top_level_keys(lines)

        missing = sorted(TOP_LEVEL_REQUIRED - keys.keys())
        assert not missing, f"{path.name}: missing required fields: {', '.join(missing)}"

        forbidden = sorted(FORBIDDEN_TOP_LEVEL & keys.keys())
        assert not forbidden, f"{path.name}: forbidden restriction fields present: {', '.join(forbidden)}"

        pack_id = keys["id"]
        assert pack_id == path.stem, f"{path.name}: id {pack_id!r} must match filename stem {path.stem!r}"
        assert pack_id not in seen_ids, f"duplicate pack id: {pack_id}"
        seen_ids.add(pack_id)

        quality = keys["quality_level"]
        assert quality in ALLOWED_QUALITY, f"{path.name}: invalid quality_level {quality!r}"

        for key in sorted(LIST_SECTIONS):
            assert has_list_item(lines, key), f"{path.name}: {key} must contain at least one item"

        for key in sorted(BLOCK_SECTIONS):
            assert has_block_content(lines, key), f"{path.name}: {key} must contain block content"

    print(f"ok: {len(paths)} packs validated")


if __name__ == "__main__":
    main()
