#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import math
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


ROOT_DIR = Path(__file__).resolve().parents[1]
PERSONALITIES_DIR = ROOT_DIR / "src" / "assets" / "personalities"
PACKET_BUILDER = ROOT_DIR / "test" / "packet_builder.py"


@dataclass(frozen=True)
class TokenMeasurement:
    persona_id: str
    neutral_tokens: int
    packet_tokens: int
    overhead_tokens: int


def estimate_tokens(text: str) -> int:
    """Return a deterministic rough estimate using the documented chars/4 rule."""
    if not text:
        return 0
    return math.ceil(len(text) / 4)


def _load_packet_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("personify_packet_builder", PACKET_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load packet builder from {PACKET_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure_pack(pack_path: Path) -> TokenMeasurement:
    builder = _load_packet_builder()
    neutral_packet = builder.load_packet()
    persona_packet = builder.load_packet(pack_path)
    pack = builder.parse_simple_yaml(pack_path)
    neutral_tokens = estimate_tokens(neutral_packet)
    packet_tokens = estimate_tokens(persona_packet)
    return TokenMeasurement(
        persona_id=str(pack["id"]),
        neutral_tokens=neutral_tokens,
        packet_tokens=packet_tokens,
        overhead_tokens=packet_tokens - neutral_tokens,
    )


def measure_all_packs(personalities_dir: Path = PERSONALITIES_DIR) -> list[TokenMeasurement]:
    return [measure_pack(path) for path in sorted(personalities_dir.glob("*.yaml"))]


def format_markdown_table(measurements: list[TokenMeasurement]) -> str:
    lines = [
        "| Persona | Neutral tokens | With persona | Overhead |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in measurements:
        lines.append(
            f"| `{item.persona_id}` | {item.neutral_tokens} | "
            f"{item.packet_tokens} | +{item.overhead_tokens} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate Personify persona activation packet token overhead.")
    parser.add_argument("--markdown", action="store_true", help="Print a markdown table.")
    args = parser.parse_args()

    measurements = measure_all_packs()
    if args.markdown:
        print(format_markdown_table(measurements))
    else:
        for item in measurements:
            print(
                f"{item.persona_id}\tneutral={item.neutral_tokens}\t"
                f"with_persona={item.packet_tokens}\toverhead=+{item.overhead_tokens}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
