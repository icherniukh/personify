#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from export_claude_skills import generate as generate_claude_skills


ROOT_DIR = Path(__file__).resolve().parents[3]
PLUGIN_DIR = ROOT_DIR / "plugins" / "promptonality"
CLAUDE_PLUGIN_DIR = PLUGIN_DIR / "claude-plugin"
CODEX_PLUGIN_JSON = PLUGIN_DIR / ".codex-plugin" / "plugin.json"
CLAUDE_SKILLS_DIR = ROOT_DIR / "skills"
PERSONA_SKILLS = (
    "persona-start",
    "persona-apply",
    "persona-list",
    "persona-extract",
    "persona-extract-online",
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def package_ignore(_dir: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name == "__pycache__" or name.endswith(".pyc"):
            ignored.add(name)
    return ignored


def included_files(root: Path) -> list[Path]:
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def export_manifest() -> str:
    codex_manifest = json.loads(CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))
    payload = {
        "name": codex_manifest["name"],
        "version": codex_manifest["version"],
        "description": "Portable personality packs for Claude Code with persona-list, persona-apply, persona-start, persona-extract, and persona-extract-online.",
        "author": codex_manifest["author"]["name"],
        "license": codex_manifest["license"],
        "homepage": codex_manifest["homepage"],
        "tags": [
            "persona",
            "personality",
            "workflow",
            "session",
            "skills",
        ],
        "skills": list(PERSONA_SKILLS),
        "compatibility": {
            "claudeCode": ">=0.1.0",
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def export_readme() -> str:
    return """# Promptonality Claude Plugin

Generated Claude Code plugin package for `promptonality`.

This package is produced from the repo source with:

```bash
python3 plugins/promptonality/scripts/export_claude_plugin.py
```

Included skills:

- `persona-list`
- `persona-apply`
- `persona-start`
- `persona-extract`
- `persona-extract-online`

Source of truth:

- `plugins/promptonality/`
- `skills/persona-*/`

Regenerate this package after source changes before installing or publishing it.
"""


def sync_skill(skill_name: str) -> None:
    src = CLAUDE_SKILLS_DIR / skill_name
    dst = CLAUDE_PLUGIN_DIR / "skills" / skill_name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=package_ignore)


def check_skill(skill_name: str) -> bool:
    src = CLAUDE_SKILLS_DIR / skill_name
    dst = CLAUDE_PLUGIN_DIR / "skills" / skill_name
    if not dst.exists():
        return False
    src_files = included_files(src)
    dst_files = included_files(dst)
    if src_files != dst_files:
        return False
    for relative_path in src_files:
        if (src / relative_path).read_text(encoding="utf-8") != (dst / relative_path).read_text(encoding="utf-8"):
            return False
    return True


def generate(check_only: bool) -> bool:
    ok = True

    if check_only:
        ok = generate_claude_skills(True) and ok
    else:
        generate_claude_skills(False)

    plugin_json_target = CLAUDE_PLUGIN_DIR / "plugin.json"
    readme_target = CLAUDE_PLUGIN_DIR / "README.md"
    plugin_json_content = export_manifest()
    readme_content = export_readme()

    if check_only:
        ok = plugin_json_target.is_file() and plugin_json_target.read_text(encoding="utf-8") == plugin_json_content and ok
        ok = readme_target.is_file() and readme_target.read_text(encoding="utf-8") == readme_content and ok
    else:
        write_text(plugin_json_target, plugin_json_content)
        write_text(readme_target, readme_content)

    skills_root = CLAUDE_PLUGIN_DIR / "skills"
    if not check_only:
        skills_root.mkdir(parents=True, exist_ok=True)
        for child in skills_root.iterdir():
            if child.is_dir() and child.name not in PERSONA_SKILLS:
                shutil.rmtree(child)

    for skill_name in PERSONA_SKILLS:
        if check_only:
            ok = check_skill(skill_name) and ok
        else:
            sync_skill(skill_name)

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Export promptonality as a Claude Code plugin package.")
    parser.add_argument("--check", action="store_true", help="Verify the generated Claude plugin package is in sync.")
    args = parser.parse_args()
    return 0 if generate(args.check) else 1


if __name__ == "__main__":
    sys.exit(main())
