#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PERSONALITIES_DIR = ROOT_DIR / "src" / "assets" / "personalities"


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
        print(f"{payload['id']}\t{payload['display_name']}\t{payload['quality_level']}\t{payload['summary']}")


if __name__ == "__main__":
    main()
