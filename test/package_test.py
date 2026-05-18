#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT_DIR / "codex" / ".codex-plugin" / "plugin.json"
ROOT_CLAUDE_MARKETPLACE = ROOT_DIR / ".claude-plugin" / "marketplace.json"
PACKAGE_META = ROOT_DIR / "src" / "package.json"
LICENSE = ROOT_DIR / "LICENSE"
EXPECTED_COMMANDS = (
    "as-persona",
    "extract-persona",
    "list-personas",
    "use-persona",
)


def main() -> None:
    print("=== personify package test ===")
    payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    meta = json.loads(PACKAGE_META.read_text(encoding="utf-8"))

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
    assert (PLUGIN_JSON.parent.parent / payload["skills"].removeprefix("./")).is_dir()
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
    skills_dir = ROOT_DIR / "codex" / "skills"
    skill_dirs = [path for path in skills_dir.iterdir() if path.is_dir()]
    assert sorted(path.name for path in skill_dirs) == sorted(EXPECTED_COMMANDS)
    for skill_dir in skill_dirs:
        assert (skill_dir / "SKILL.md").is_file(), f"missing SKILL.md in {skill_dir.name}"
        assert not (skill_dir / "references" / "personality-packs" / "jesse-pinkman-v1.yaml").exists()
    print("ok")

    print("5. command adapters")
    for command_name in EXPECTED_COMMANDS:
        codex_command = ROOT_DIR / "codex" / "commands" / f"{command_name}.md"
        gemini_command = ROOT_DIR / "gemini" / "commands" / f"{command_name}.toml"
        opencode_command = ROOT_DIR / "opencode" / "commands" / f"{command_name}.md"
        assert codex_command.is_file()
        assert gemini_command.is_file()
        assert opencode_command.is_file()
        if command_name in {"use-persona", "as-persona"}:
            for command_file in (codex_command, gemini_command, opencode_command):
                command_text = command_file.read_text(encoding="utf-8")
                assert "resolve the matching pack" in command_text
                assert "construct the Persona Activation Packet" in command_text
                assert "apply the requested scope" in command_text
    gemini_context = " ".join((ROOT_DIR / "gemini" / "GEMINI.md").read_text(encoding="utf-8").split())
    assert "resolve the pack, construct the Persona Activation Packet, and apply the requested scope" in gemini_context
    print("ok")

    print("6a. opencode skill layout")
    opencode_skills_dir = ROOT_DIR / "opencode" / "skills"
    assert opencode_skills_dir.is_dir()
    assert sorted(p.name for p in opencode_skills_dir.iterdir() if p.is_dir()) == sorted(EXPECTED_COMMANDS)
    for skill_name in EXPECTED_COMMANDS:
        assert (opencode_skills_dir / skill_name / "SKILL.md").is_file()
    print("ok")

    print("6b. pi skill layout")
    pi_skills_dir = ROOT_DIR / "pi" / "skills"
    assert pi_skills_dir.is_dir()
    assert sorted(p.name for p in pi_skills_dir.iterdir() if p.is_dir()) == sorted(EXPECTED_COMMANDS)
    for skill_name in EXPECTED_COMMANDS:
        assert (pi_skills_dir / skill_name / "SKILL.md").is_file()
    pi_pkg = json.loads((ROOT_DIR / "pi" / "package.json").read_text(encoding="utf-8"))
    assert "pi-package" in pi_pkg["keywords"]
    assert pi_pkg["pi"]["skills"] == ["./skills"]
    print("ok")

    print("6c. root pi manifest")
    root_pkg = json.loads((ROOT_DIR / "package.json").read_text(encoding="utf-8"))
    assert "pi-package" in root_pkg["keywords"]
    assert root_pkg["pi"]["skills"] == ["./pi/skills"]
    print("ok")

    print("7. release metadata")
    assert LICENSE.is_file(), "missing LICENSE file"
    assert "MIT License" in LICENSE.read_text(encoding="utf-8")
    marketplace = json.loads(ROOT_CLAUDE_MARKETPLACE.read_text(encoding="utf-8"))
    assert marketplace["name"] == meta["name"]
    assert marketplace["owner"]["name"] == meta["author"]["name"]
    assert marketplace["plugins"][0]["name"] == meta["name"]
    assert marketplace["plugins"][0]["source"] == "./claude"
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    repo_slug = meta["repository"].removeprefix("https://github.com/")
    assert f"claude plugin marketplace add {repo_slug}" in readme
    assert f"codex plugin marketplace add {repo_slug}" in readme
    print("ok")

    print("=== package test passed ===")


if __name__ == "__main__":
    main()
