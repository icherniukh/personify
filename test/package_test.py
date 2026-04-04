#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT_DIR / ".codex-plugin" / "plugin.json"


def main() -> None:
    print("=== promptonality package test ===")
    payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))

    print("1. manifest identity")
    assert ROOT_DIR.name == payload["name"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", payload["version"])
    assert isinstance(payload["description"], str) and payload["description"]
    print("ok")

    print("2. top-level manifest fields")
    for key in (
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "interface",
    ):
        assert key in payload, f"missing {key}"
    for key in ("name", "email", "url"):
        assert key in payload["author"], f"missing author.{key}"
    assert payload["skills"].startswith("./")
    assert (ROOT_DIR / payload["skills"].removeprefix("./")).is_dir()
    print("ok")

    print("3. interface metadata")
    interface = payload["interface"]
    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "websiteURL",
        "privacyPolicyURL",
        "termsOfServiceURL",
        "defaultPrompt",
        "brandColor",
    ):
        assert key in interface, f"missing interface.{key}"
    assert isinstance(interface["defaultPrompt"], list)
    assert 1 <= len(interface["defaultPrompt"]) <= 3
    assert all(isinstance(item, str) and 1 <= len(item) <= 128 for item in interface["defaultPrompt"])
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", interface["brandColor"])
    print("ok")

    print("4. skill package layout")
    skills_dir = ROOT_DIR / "skills"
    skill_dirs = [path for path in skills_dir.iterdir() if path.is_dir()]
    assert skill_dirs, "no skills found"
    for skill_dir in skill_dirs:
        assert (skill_dir / "SKILL.md").is_file(), f"missing SKILL.md in {skill_dir.name}"
    print("ok")

    print("=== package test passed ===")


if __name__ == "__main__":
    main()
