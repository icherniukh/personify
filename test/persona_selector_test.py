#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from scripts.persona_selector import (
    PersonaPack,
    PersonaSelectionRequest,
    PersonaSelector,
)


def pack(
    pack_id: str,
    *,
    summary: str = "",
    reasoning_style: list[str] | None = None,
    value_profile: list[str] | None = None,
    interaction_stance: list[str] | None = None,
    preferred_terminology: list[str] | None = None,
) -> PersonaPack:
    return PersonaPack(
        id=pack_id,
        display_name=pack_id.replace("-", " ").title(),
        summary=summary,
        voice={"tone": ""},
        interaction_stance=interaction_stance or [],
        value_profile=value_profile or [],
        reasoning_style=reasoning_style or [],
        preferred_terminology=preferred_terminology or [],
        source_path=Path(f"/packs/{pack_id}.yaml"),
    )


def test_explicit_mode_returns_requested_persona_with_rationale() -> None:
    selector = PersonaSelector(
        [
            pack("sam-harris", summary="Analytic clarity"),
            pack("leon", summary="General assistance"),
        ]
    )

    result = selector.select(
        PersonaSelectionRequest(
            mode="explicit",
            persona_id="leon",
            task="Plan a small repo cleanup.",
        )
    )

    assert result.persona_id == "leon"
    assert "explicit" in result.rationale
    assert "leon" in result.rationale


def test_random_mode_is_seeded_and_respects_include_exclude_filters() -> None:
    selector = PersonaSelector(
        [
            pack("sam-harris"),
            pack("leon"),
            pack("yoda"),
            pack("bjarne-stroustrup"),
        ]
    )
    request = PersonaSelectionRequest(
        mode="random",
        task="Pick a fresh voice for a debugging session.",
        seed="debug-seed",
        include_ids={"sam-harris", "leon", "yoda"},
        exclude_ids={"yoda"},
    )

    first = selector.select(request)
    second = selector.select(request)

    assert first.persona_id == second.persona_id
    assert first.persona_id in {"sam-harris", "leon"}
    assert first.persona_id != "yoda"
    assert "seed" in first.rationale
    assert "2 eligible" in first.rationale


def test_auto_mode_scores_pack_metadata_without_persona_specific_branches() -> None:
    selector = PersonaSelector(
        [
            pack(
                "bjarne-stroustrup",
                summary="Engineering-first lens for abstraction and maintainability.",
                reasoning_style=[
                    "weigh efficiency, abstraction, and implementation cost",
                    "treat complexity as the main enemy",
                ],
                value_profile=["prioritizes long-term maintainability"],
                preferred_terminology=["interface", "complexity", "cost"],
            ),
            pack(
                "dababy",
                summary="High-energy entertainment instinct.",
                reasoning_style=["conclusion first every time"],
                value_profile=["entertainment is leverage"],
                preferred_terminology=["momentum", "win"],
            ),
        ]
    )

    result = selector.select(
        PersonaSelectionRequest(
            mode="auto",
            task="Design an API interface with maintainability and complexity tradeoffs.",
            context="Need calm engineering judgment, not hype.",
        )
    )

    assert result.persona_id == "bjarne-stroustrup"
    assert "metadata affinity" in result.rationale
    assert "interface" in result.rationale


def test_loads_source_personality_packs_for_selection() -> None:
    selector = PersonaSelector.from_directory(Path("src/assets/personalities"))

    result = selector.select(
        PersonaSelectionRequest(
            mode="auto",
            task="Surface hidden assumptions and uncertainty in a reasoning-heavy decision.",
        )
    )

    assert result.persona_id == "sam-harris"
    assert "reasoning" in result.rationale


if __name__ == "__main__":
    test_explicit_mode_returns_requested_persona_with_rationale()
    test_random_mode_is_seeded_and_respects_include_exclude_filters()
    test_auto_mode_scores_pack_metadata_without_persona_specific_branches()
    test_loads_source_personality_packs_for_selection()
    print("=== persona selector test passed ===")
