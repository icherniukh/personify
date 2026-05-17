#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from scripts.token_overhead import estimate_tokens, format_markdown_table, measure_pack

SAM_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "sam-harris.yaml"


def test_estimate_tokens_uses_documented_character_heuristic() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2


def test_measure_pack_reports_incremental_persona_overhead() -> None:
    measurement = measure_pack(SAM_PACK)

    assert measurement.persona_id == "sam-harris"
    assert measurement.packet_tokens > measurement.neutral_tokens
    assert measurement.overhead_tokens == measurement.packet_tokens - measurement.neutral_tokens
    assert measurement.overhead_tokens > 100


def test_format_markdown_table_includes_methodology_columns() -> None:
    measurement = measure_pack(SAM_PACK)
    table = format_markdown_table([measurement])

    assert "| Persona | Neutral tokens | With persona | Overhead |" in table
    assert "| `sam-harris` |" in table


def main() -> None:
    test_estimate_tokens_uses_documented_character_heuristic()
    test_measure_pack_reports_incremental_persona_overhead()
    test_format_markdown_table_includes_methodology_columns()


if __name__ == "__main__":
    main()
