#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
BUNDLED_PERSONAS_DIR = SKILL_DIR / "references" / "personality-packs"
HEADER_KEYS = {"id", "display_name", "summary", "quality_level"}


def xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def user_personas_dir() -> Path:
    return xdg_data_home() / "personify" / "personas"


def hidden_personas_file() -> Path:
    return xdg_config_home() / "personify" / "hidden.yaml"


def parse_pack_header(path: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in HEADER_KEYS:
            payload[key] = value
    return payload


def parse_hidden_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()

    hidden_ids: set[str] = set()
    in_hidden_list = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "hidden:":
            in_hidden_list = True
            continue
        if in_hidden_list and stripped.startswith("- "):
            hidden_ids.add(stripped[2:].strip().strip("'\""))
            continue
        in_hidden_list = False
        if stripped.startswith("- "):
            hidden_ids.add(stripped[2:].strip().strip("'\""))
    return hidden_ids


def load_personas(*, bundled_dir: Path = BUNDLED_PERSONAS_DIR, user_dir: Path | None = None, hidden_file: Path | None = None) -> list[dict[str, str]]:
    user_dir = user_personas_dir() if user_dir is None else user_dir
    hidden_file = hidden_personas_file() if hidden_file is None else hidden_file

    personas: dict[str, dict[str, str]] = {}
    for directory in (bundled_dir, user_dir):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.yaml")):
            payload = parse_pack_header(path)
            pack_id = payload.get("id")
            if pack_id:
                personas[pack_id] = payload

    hidden_ids = parse_hidden_ids(hidden_file)
    return [personas[pack_id] for pack_id in sorted(personas) if pack_id not in hidden_ids]


def main() -> None:
    for payload in load_personas():
        print(f"{payload['id']}\t{payload['display_name']}\t{payload['quality_level']}\t{payload['summary']}")


if __name__ == "__main__":
    main()
