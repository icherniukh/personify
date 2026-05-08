#!/usr/bin/env python3

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SKILLS_SRC = SRC_DIR / "skills"
PERSONALITIES_SRC = SRC_DIR / "assets" / "personalities"
CONTRACT_DOC = ROOT_DIR / "docs" / "personality-pack-contract.md"
PACKAGE_META = SRC_DIR / "package.json"

TARGET_DIRS = {
    "codex": ROOT_DIR / "codex",
    "claude": ROOT_DIR / "claude",
    "gemini": ROOT_DIR / "gemini",
}

ALL_TARGETS = list(TARGET_DIRS) + ["root"]

PERSONA_ENTRYPOINTS = {"use-persona", "as-persona", "list-personas"}
CONTRACT_SKILLS = {"list-personas", "extract-persona"}
COMMANDS = {
    "list-personas": {
        "argument_hint": "[filter-or-focus]",
        "description": "List available Personify persona packs.",
        "prompt": "Use the list-personas skill to list available Personify persona packs. User arguments: $ARGUMENTS",
    },
    "use-persona": {
        "argument_hint": "<persona> [session goal]",
        "description": "Use a Personify persona as the default voice and reasoning lens for the session.",
        "prompt": "Use the use-persona skill to activate this persona for the session. Load the matching pack and construct the Persona Activation Packet before applying it. User arguments: $ARGUMENTS",
    },
    "as-persona": {
        "argument_hint": "<persona> <task>",
        "description": "Apply a Personify persona to the current task or thread.",
        "prompt": "Use the as-persona skill to apply this persona overlay for the requested scope. Load the matching pack and construct the Persona Activation Packet before answering. User arguments: $ARGUMENTS",
    },
    "extract-persona": {
        "argument_hint": "<person-or-character> [role/use-case]",
        "description": "Create a research-backed Personify persona pack from web-grounded source material.",
        "prompt": "Use the extract-persona skill to create a research-backed Personify persona pack. User arguments: $ARGUMENTS",
    },
}


def read_meta() -> dict[str, object]:
    return json.loads(PACKAGE_META.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def package_ignore(_dir: str, names: list[str]) -> set[str]:
    return {name for name in names if name == "__pycache__" or name.endswith(".pyc")}


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=package_ignore)


def skill_names() -> list[str]:
    return sorted(path.name for path in SKILLS_SRC.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())


def bundled_personality_note() -> str:
    return (
        "\n\n## Persona Assets\n\n"
        "This packaged skill bundles the current Personify starter packs under:\n\n"
        "- `references/personality-packs/`\n\n"
        "Those files are persona assets. Bundled packs are starter assets and regression fixtures, not the boundary of the framework.\n"
    )


def persona_list_script() -> str:
    return """#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PERSONALITIES_DIR = SKILL_DIR / "references" / "personality-packs"


def parse_pack_header(path: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in {"id", "display_name", "summary", "quality_level"}:
            payload[key] = value
    return payload


def main() -> None:
    for path in sorted(PERSONALITIES_DIR.glob("*.yaml")):
        payload = parse_pack_header(path)
        print(f"{payload['id']}\\t{payload['display_name']}\\t{payload['quality_level']}\\t{payload['summary']}")


if __name__ == "__main__":
    main()
"""


def package_skills(target: Path) -> None:
    skills_dir = target / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for name in skill_names():
        src = SKILLS_SRC / name
        dst = skills_dir / name
        copy_tree(src, dst)

        if name in PERSONA_ENTRYPOINTS:
            if name in {"use-persona", "as-persona"}:
                skill_md = dst / "SKILL.md"
                skill_md.write_text(skill_md.read_text(encoding="utf-8") + bundled_personality_note(), encoding="utf-8")
            pack_dir = dst / "references" / "personality-packs"
            pack_dir.mkdir(parents=True, exist_ok=True)
            for pack in sorted(PERSONALITIES_SRC.glob("*.yaml")):
                shutil.copyfile(pack, pack_dir / pack.name)

        if name in CONTRACT_SKILLS:
            (dst / "references").mkdir(parents=True, exist_ok=True)
            shutil.copyfile(CONTRACT_DOC, dst / "references" / "personality-pack-contract.md")

        if name == "list-personas":
            script = dst / "scripts" / "persona_list.py"
            write_text(script, persona_list_script())
            script.chmod(0o755)


def codex_command(name: str, spec: dict[str, str]) -> str:
    return f"""---
description: {spec["description"]}
argument-hint: {spec["argument_hint"]}
---

{spec["prompt"]}
"""


def gemini_command(spec: dict[str, str]) -> str:
    prompt = spec["prompt"].replace("$ARGUMENTS", "{{args}}")
    return f"""description = {json.dumps(spec["description"])}
prompt = {json.dumps(prompt)}
"""


def package_codex_commands(target: Path) -> None:
    commands_dir = target / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in sorted(COMMANDS.items()):
        write_text(commands_dir / f"{name}.md", codex_command(name, spec))


def package_gemini_commands(target: Path) -> None:
    commands_dir = target / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in sorted(COMMANDS.items()):
        write_text(commands_dir / f"{name}.toml", gemini_command(spec))


def codex_manifest(meta: dict[str, object]) -> str:
    payload = {
        "name": meta["name"],
        "version": meta["version"],
        "description": meta["description"],
        "author": meta["author"],
        "homepage": meta["homepage"],
        "repository": meta["repository"],
        "license": meta["license"],
        "keywords": meta["keywords"],
        "skills": "./skills/",
        "interface": meta["interface"],
    }
    return json.dumps(payload, indent=2) + "\n"


def claude_plugin_manifest(meta: dict[str, object]) -> str:
    payload = {
        "name": meta["name"],
        "version": meta["version"],
        "description": "Portable persona packs for Claude Code with Personify persona skills.",
        "author": {"name": meta["author"]["name"]},
        "license": meta["license"],
        "homepage": meta["homepage"],
    }
    return json.dumps(payload, indent=2) + "\n"


def claude_marketplace(meta: dict[str, object]) -> str:
    payload = {
        "name": meta["name"],
        "description": "Installable Claude Code plugin for portable persona packs.",
        "owner": {"name": meta["author"]["name"]},
        "plugins": [
            {
                "name": meta["name"],
                "description": "Portable persona packs for Claude Code with Personify persona skills.",
                "source": "./",
                "category": "productivity",
                "tags": ["persona", "personality", "voice", "session"],
            }
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def root_claude_marketplace(meta: dict[str, object]) -> str:
    payload = {
        "name": meta["name"],
        "description": "Installable Claude Code plugin for portable persona packs.",
        "owner": {"name": meta["author"]["name"]},
        "plugins": [
            {
                "name": meta["name"],
                "description": "Portable persona packs for Claude Code with Personify persona skills.",
                "source": "./claude",
                "category": "productivity",
                "tags": ["persona", "personality", "voice", "session"],
            }
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def root_codex_marketplace(meta: dict[str, object]) -> str:
    payload = {
        "name": meta["name"],
        "description": "Installable Codex plugin for portable persona packs.",
        "owner": {"name": meta["author"]["name"]},
        "plugins": [
            {
                "name": meta["name"],
                "description": "Portable persona packs for Codex with Personify persona skills.",
                "source": "./codex",
            }
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def root_gemini_manifest(meta: dict[str, object]) -> str:
    payload = {"name": meta["name"], "version": meta["version"], "contextFile": "gemini/GEMINI.md"}
    return json.dumps(payload, indent=2) + "\n"


def claude_readme() -> str:
    return """# Personify Claude Plugin

Generated Claude Code plugin package for `personify`.

This directory is build output. Regenerate it with:

```bash
python3 scripts/package.py build --target claude
```
"""


def gemini_manifest(meta: dict[str, object]) -> str:
    return json.dumps({"name": meta["name"], "version": meta["version"], "contextFile": "GEMINI.md"}, indent=2) + "\n"


def gemini_context() -> str:
    return """# Personify Extension

`personify` provides portable persona packs for agent voice and reasoning style.

Use `list-personas` to see bundled packs. Use `as-persona` for one task or
`use-persona` for a whole session.

When applying a persona, load the matching pack and construct the compact
Persona Activation Packet described by the packaged skill before answering.
"""


def gemini_readme() -> str:
    return """# Personify Gemini Extension

Generated Gemini CLI extension package for `personify`.

This directory is build output. Regenerate it with:

```bash
python3 scripts/package.py build --target gemini
```
"""


def build_root() -> None:
    meta = read_meta()
    write_text(ROOT_DIR / ".claude-plugin" / "marketplace.json", root_claude_marketplace(meta))
    write_text(ROOT_DIR / ".codex-plugin" / "marketplace.json", root_codex_marketplace(meta))
    write_text(ROOT_DIR / "gemini-extension.json", root_gemini_manifest(meta))


def check_root() -> bool:
    meta = read_meta()
    checks = [
        (ROOT_DIR / ".claude-plugin" / "marketplace.json", root_claude_marketplace(meta)),
        (ROOT_DIR / ".codex-plugin" / "marketplace.json", root_codex_marketplace(meta)),
        (ROOT_DIR / "gemini-extension.json", root_gemini_manifest(meta)),
    ]
    ok = True
    for path, expected in checks:
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            print(f"drift: {path.relative_to(ROOT_DIR)} is missing or out of sync", file=sys.stderr)
            ok = False
    return ok


def build_target(target_name: str) -> None:
    meta = read_meta()
    target = TARGET_DIRS[target_name]
    clean_dir(target)
    package_skills(target)

    if target_name == "codex":
        write_text(target / ".codex-plugin" / "plugin.json", codex_manifest(meta))
        package_codex_commands(target)
    elif target_name == "claude":
        write_text(target / ".claude-plugin" / "plugin.json", claude_plugin_manifest(meta))
        write_text(target / ".claude-plugin" / "marketplace.json", claude_marketplace(meta))
        write_text(target / "README.md", claude_readme())
    elif target_name == "gemini":
        write_text(target / "gemini-extension.json", gemini_manifest(meta))
        write_text(target / "GEMINI.md", gemini_context())
        write_text(target / "README.md", gemini_readme())
        package_gemini_commands(target)
    else:
        raise ValueError(f"unknown target: {target_name}")


def compare_dirs(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    cmp = filecmp.dircmp(left, right, ignore=["__pycache__"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(compare_dirs(left / name, right / name) for name in cmp.common_dirs)


def check_target(target_name: str) -> bool:
    cache_dir = ROOT_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"{target_name}-", dir=cache_dir))
    original = TARGET_DIRS[target_name]
    TARGET_DIRS[target_name] = tmp
    try:
        build_target(target_name)
        return compare_dirs(tmp, original)
    finally:
        TARGET_DIRS[target_name] = original
        if tmp.exists():
            shutil.rmtree(tmp)


def doctor() -> bool:
    ok = True
    for target in TARGET_DIRS:
        if not check_target(target):
            print(f"drift: {target} package is missing or out of sync", file=sys.stderr)
            ok = False

    for home in (Path.home() / ".codex" / "skills", Path.home() / ".claude" / "skills"):
        if home.exists():
            stale = sorted(path for path in home.glob("persona-*") if path.is_dir())
            if stale:
                print(f"split-brain install: remove loose persona skills under {home}", file=sys.stderr)
                for path in stale:
                    print(f"  {path}", file=sys.stderr)
                ok = False
    cache_roots = (
        Path.home() / ".codex" / "plugins" / "cache",
        Path.home() / ".claude" / "plugins" / "cache",
    )
    for cache_root in cache_roots:
        if cache_root.exists():
            stale_caches = sorted(path for path in cache_root.rglob("personify") if path.is_dir())
            if stale_caches:
                print(f"plugin cache drift risk: refresh or remove cached personify packages under {cache_root}", file=sys.stderr)
                for path in stale_caches:
                    print(f"  {path}", file=sys.stderr)
                ok = False
    return ok


def selected_targets(value: str) -> list[str]:
    if value == "all":
        return ALL_TARGETS
    if value not in ALL_TARGETS:
        raise SystemExit(f"unknown target: {value}")
    return [value]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and check Personify platform packages.")
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ("build", "check"):
        p = sub.add_parser(command)
        p.add_argument("--target", choices=[*ALL_TARGETS, "all"], default="all")
    sub.add_parser("doctor")

    args = parser.parse_args()
    if args.command == "build":
        for target in selected_targets(args.target):
            if target == "root":
                build_root()
            else:
                build_target(target)
        return 0
    if args.command == "check":
        results = []
        for target in selected_targets(args.target):
            if target == "root":
                results.append(check_root())
            else:
                results.append(check_target(target))
        return 0 if all(results) else 1
    if args.command == "doctor":
        return 0 if doctor() else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
