#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from packet_builder import (
    load_architecture_neutral_packet,
    load_neutral_packet,
    load_sam_packet,
    load_yoda_architecture_packet,
)


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"expected to find {needle!r}"


def assert_not_contains(text: str, needle: str) -> None:
    assert needle not in text, f"did not expect to find {needle!r}"


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    neutral_packet = load_neutral_packet()
    sam_packet = load_sam_packet()
    persona_start = (root_dir / "skills" / "persona-start" / "SKILL.md").read_text(encoding="utf-8")
    persona_apply = (root_dir / "skills" / "persona-apply" / "SKILL.md").read_text(encoding="utf-8")
    persona_list = (root_dir / "skills" / "persona-list" / "SKILL.md").read_text(encoding="utf-8")
    yoda_pack_text = (root_dir / "assets" / "personalities" / "yoda.yaml").read_text(encoding="utf-8")
    bjarne_pack_text = (root_dir / "assets" / "personalities" / "bjarne-stroustrup.yaml").read_text(encoding="utf-8")
    sam_pack_text = (root_dir / "assets" / "personalities" / "sam-harris.yaml").read_text(encoding="utf-8")

    print("=== promptonality behavior test ===")

    print("1. neutral packet stays neutral")
    assert_contains(neutral_packet, "Route or delegate when tool use")
    assert_contains(neutral_packet, "Every delegated task should state:")
    assert_not_contains(neutral_packet, "Sam Harris")
    assert_not_contains(neutral_packet, "calm precision")
    print("ok")

    print("2. Sam Harris packet preserves core orchestration rules")
    assert_contains(sam_packet, "Route or delegate when tool use")
    assert_contains(sam_packet, "Every delegated task should state:")
    assert_contains(sam_packet, "If the work requires more than three delegations")
    print("ok")

    print("3. Sam Harris packet adds personality-specific guidance")
    assert_contains(sam_packet, "Identity: Sam Harris")
    assert_contains(sam_packet, "Voice:")
    assert_contains(sam_packet, "style: low-theatrics, high-clarity, quietly skeptical")
    assert_contains(sam_packet, "Interaction stance:")
    assert_contains(sam_packet, "skeptical but constructive")
    assert_contains(sam_packet, "Value profile:")
    assert_contains(sam_packet, "surfaces hidden assumptions before recommendations")
    assert_contains(sam_packet, "state uncertainty plainly")
    assert_contains(sam_packet, "Default structures:")
    assert_contains(sam_packet, "observations / assumptions / next steps")
    assert_contains(sam_packet, "Ambiguity policy:")
    assert_contains(sam_packet, "Treat ambiguity as something to map explicitly")
    assert_contains(sam_packet, "Tradeoff policy:")
    assert_contains(sam_packet, "State the real tradeoff directly")
    assert_contains(sam_packet, "Compression policy:")
    assert_contains(sam_packet, "Compress by preserving decisive distinctions")
    assert_contains(sam_packet, "do not pad for warmth")
    assert_contains(sam_packet, "smugness")
    assert_contains(sam_packet, "Speak with calm precision and intellectual honesty.")
    assert_contains(sam_packet, "explicitly separate observations, assumptions, and next steps")
    assert_contains(sam_packet, "Prefer compact analytic")
    assert_contains(sam_packet, "generic advice formatting")
    assert_contains(sam_packet, "what we know, what we suspect, and what to do next")
    print("ok")

    print("4. Sam Harris packet stays task-focused rather than theatrical")
    assert_contains(sam_packet, "usefulness is primary; persona is secondary")
    assert_contains(sam_packet, "goal")
    assert_contains(sam_packet, "not to impersonate")
    assert_contains(sam_packet, "impersonate Sam Harris")
    assert_contains(sam_packet, "theatrically;")
    assert_not_contains(sam_packet, "Begin every response directly in character.")
    print("ok")

    print("5. persona-start establishes a session-wide default mode")
    assert_contains(persona_start, "default policy for all nontrivial work in the session unless the user explicitly overrides it")
    assert_contains(persona_start, "If the user names a relevant installed skill, activate that skill directly")
    assert_contains(persona_start, "If the user names a workflow and a personality pack, compose them explicitly")
    assert_contains(persona_start, "read the matching pack file from `references/personality-packs/` before activating the mode")
    assert_contains(persona_start, "does not automatically create a new installed skill")
    print("ok")

    print("6. persona-apply handles one-off composition without requiring a named variant")
    assert_contains(persona_apply, "Default scope is the current task only")
    assert_contains(persona_apply, "If the requested combo already exists as a named installed skill, use that skill")
    assert_contains(persona_apply, "read the matching pack file from `references/personality-packs/` before answering")
    assert_contains(persona_apply, "This skill does not create a new installed variant")
    assert_contains(persona_apply, "explicit prompt-level composition")
    print("ok")

    print("7. persona-list exposes installed packs and the ad-hoc composition rule")
    assert_contains(persona_list, "Read those YAML files directly when listing available")
    assert_contains(persona_list, "Do not assume the current working directory is the")
    assert_contains(persona_list, "Listing a personality pack does not mean every possible workflow-plus-pack combination already exists as a named installed skill")
    assert_contains(persona_list, "Explicit composition:")
    assert_contains(persona_list, "it can work without a prebuilt combo")
    print("ok")

    print("8. personality packs stay reusable instead of leaking workflow-specific review language")
    assert_not_contains(yoda_pack_text, "When the architecture is unclear")
    assert_not_contains(yoda_pack_text, "architectural")
    assert_not_contains(yoda_pack_text, "software structure")
    assert_not_contains(yoda_pack_text, "technical content")
    assert_not_contains(bjarne_pack_text, "when reviewing code")
    assert_not_contains(sam_pack_text, "orchestration and synthesis")
    assert_not_contains(sam_pack_text, "operational tasks")
    print("ok")

    neutral_arch_packet = load_architecture_neutral_packet()
    yoda_packet = load_yoda_architecture_packet()

    print("9. Yoda packet preserves the neutral architecture-review core")
    assert_contains(neutral_arch_packet, "System Goal")
    assert_contains(neutral_arch_packet, "Main Architectural Units")
    assert_contains(yoda_packet, "System Goal")
    assert_contains(yoda_packet, "Main Architectural Units")
    assert_contains(yoda_packet, "Recommended Changes")
    print("ok")

    print("10. Yoda packet carries explicit terminology and speech markers")
    assert_contains(yoda_packet, "Identity: Yoda")
    assert_contains(yoda_packet, "Preferred terminology:")
    assert_contains(yoda_packet, "- balance")
    assert_contains(yoda_packet, "- fear")
    assert_contains(yoda_packet, "- burden")
    assert_contains(yoda_packet, "- matters not")
    assert_contains(yoda_packet, "- the Force")
    assert_contains(yoda_packet, "Speech patterns:")
    assert_contains(yoda_packet, "often fronts the idea he wants emphasized")
    assert_contains(yoda_packet, "uses inversion in several places per response, but varies the pattern instead of repeating one template")
    assert_contains(yoda_packet, "mixes stylized lines with plain sentences so the message stays readable")
    assert_contains(yoda_packet, "use some reversed Yoda sentence structure in most responses")
    assert_contains(yoda_packet, "do not reuse the same inversion template over and over")
    assert_contains(yoda_packet, "occasional wry teacherly humor")
    assert_contains(yoda_packet, "always in motion")
    print("ok")

    print("=== behavior test passed ===")


if __name__ == "__main__":
    main()
