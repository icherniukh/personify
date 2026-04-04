#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CLAUDE_PLUGIN_DIR = ROOT_DIR / "claude-plugin"
PLUGIN_JSON = CLAUDE_PLUGIN_DIR / "plugin.json"
EXPECTED_SKILLS = (
    "persona-start",
    "persona-apply",
    "persona-list",
    "persona-extract",
    "persona-extract-online",
)


def main() -> None:
    print("=== promptonality Claude plugin test ===")
    payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))

    print("1. manifest identity")
    assert payload["name"] == "promptonality"
    assert re.fullmatch(r"\d+\.\d+\.\d+", payload["version"])
    assert isinstance(payload["description"], str) and payload["description"]
    print("ok")

    print("2. manifest shape")
    for key in (
        "author",
        "license",
        "homepage",
        "tags",
        "skills",
        "compatibility",
    ):
        assert key in payload, f"missing {key}"
    assert isinstance(payload["skills"], list)
    assert payload["skills"] == list(EXPECTED_SKILLS)
    assert payload["compatibility"]["claudeCode"].startswith(">=")
    print("ok")

    print("3. packaged skill layout")
    skills_dir = CLAUDE_PLUGIN_DIR / "skills"
    assert skills_dir.is_dir()
    for skill_name in EXPECTED_SKILLS:
        skill_dir = skills_dir / skill_name
        assert skill_dir.is_dir(), f"missing skill directory: {skill_name}"
        assert (skill_dir / "SKILL.md").is_file(), f"missing SKILL.md: {skill_name}"
    print("ok")

    print("4. generated support files")
    assert (CLAUDE_PLUGIN_DIR / "README.md").is_file()
    print("ok")

    print("=== Claude plugin test passed ===")


if __name__ == "__main__":
    main()
