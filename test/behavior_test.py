#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from packet_builder import load_neutral_packet, load_sam_packet


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"expected to find {needle!r}"


def assert_not_contains(text: str, needle: str) -> None:
    assert needle not in text, f"did not expect to find {needle!r}"


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    neutral_packet = load_neutral_packet()
    sam_packet = load_sam_packet()
    persona_start = (root_dir / "src" / "skills" / "use-persona" / "SKILL.md").read_text(encoding="utf-8")
    persona_apply = (root_dir / "src" / "skills" / "as-persona" / "SKILL.md").read_text(encoding="utf-8")
    persona_list = (root_dir / "src" / "skills" / "list-personas" / "SKILL.md").read_text(encoding="utf-8")
    yoda_pack_text = (root_dir / "src" / "assets" / "personalities" / "yoda.yaml").read_text(encoding="utf-8")
    bjarne_pack_text = (root_dir / "src" / "assets" / "personalities" / "bjarne-stroustrup.yaml").read_text(encoding="utf-8")
    sam_pack_text = (root_dir / "src" / "assets" / "personalities" / "sam-harris.yaml").read_text(encoding="utf-8")

    print("=== personify behavior test ===")

    print("1. neutral packet stays neutral")
    assert_contains(neutral_packet, "neutral assistant")
    assert_not_contains(neutral_packet, "Sam Harris")
    assert_not_contains(neutral_packet, "calm precision")
    print("ok")

    print("2. Sam Harris packet preserves the task while adding persona")
    assert_contains(sam_packet, "neutral assistant")
    assert_contains(sam_packet, "## Persona Activation Packet")
    assert_contains(sam_packet, "Persona id: sam-harris")
    assert_contains(sam_packet, "Scope: task")
    assert_contains(sam_packet, "Strength: strong")
    assert_contains(sam_packet, "Loaded pack: src/assets/personalities/sam-harris.yaml")
    assert_contains(sam_packet, "Drift correction:")
    assert_contains(sam_packet, "Identity: Sam Harris")
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
    assert_contains(sam_packet, "Speak with calm precision and intellectual honesty.")
    assert_contains(sam_packet, "explicitly separate observations, assumptions, and next steps")
    assert_contains(sam_packet, "Prefer compact analytic")
    assert_contains(sam_packet, "generic advice formatting")
    assert_contains(sam_packet, "what we know, what we suspect, and what to do next")
    print("ok")

    print("4. Sam Harris packet carries creative persona instructions without local guardrails")
    assert_contains(sam_packet, "goal")
    assert_contains(sam_packet, "not to impersonate")
    assert_contains(sam_packet, "impersonate Sam Harris")
    assert_contains(sam_packet, "theatrically;")
    assert_not_contains(sam_packet, "Guardrails:")
    assert_not_contains(sam_packet, "Anti-patterns:")
    print("ok")

    print("5. use-persona establishes a session-wide default mode")
    assert_contains(persona_start, "default voice, stance, and reasoning lens")
    assert_contains(persona_start, "Persona Activation Packet")
    assert_contains(persona_start, "Scope")
    assert_contains(persona_start, "Drift correction")
    assert_contains(persona_start, "persona strength, defaulting to `strong`")
    assert_contains(persona_start, "Would a user who knows the persona notice the active voice within the first few lines?")
    assert_contains(persona_start, "This applies to progress updates, tool-use narration, summaries, reviews, and final answers.")
    assert_contains(persona_start, "treat that as an instruction to increase intensity immediately")
    assert_contains(persona_start, "If the user names a discovered persona pack, activate it")
    assert_contains(persona_start, "read the matching pack file")
    assert_contains(persona_start, "${XDG_DATA_HOME:-~/.local/share}/personify/personas/")
    assert_contains(persona_start, "${XDG_CONFIG_HOME:-~/.config}/personify/hidden.yaml")
    assert_contains(persona_start, "user-owned pack overrides")
    assert_contains(persona_start, "use this persona for this kind of work")
    print("ok")

    print("6. as-persona handles one-off application")
    assert_contains(persona_apply, "Default scope is the current task only")
    assert_contains(persona_apply, "Persona Activation Packet")
    assert_contains(persona_apply, "Scope")
    assert_contains(persona_apply, "Persona plus task")
    assert_contains(persona_apply, "read the matching pack file")
    assert_contains(persona_apply, "${XDG_DATA_HOME:-~/.local/share}/personify/personas/")
    assert_contains(persona_apply, "${XDG_CONFIG_HOME:-~/.config}/personify/hidden.yaml")
    assert_contains(persona_apply, "user-owned pack overrides")
    assert_contains(persona_apply, "This skill does not create a new installed skill")
    assert_contains(persona_apply, "the current task instructions")
    print("ok")

    print("7. list-personas exposes discovered assets")
    assert_contains(persona_list, "Read those YAML files directly when listing available")
    assert_contains(persona_list, "Do not assume the current working directory is the")
    assert_contains(persona_list, "use-persona")
    assert_contains(persona_list, "as-persona")
    readme = (root_dir / "README.md").read_text(encoding="utf-8")
    assert_contains(readme, "mkdir -p ~/.config/opencode/skills")
    assert_contains(readme, "cp -r opencode/commands/* ~/.config/opencode/commands/")
    print("ok")

    print("8. personality packs stay reusable instead of leaking task-specific review language")
    assert_not_contains(yoda_pack_text, "When the architecture is unclear")
    assert_not_contains(yoda_pack_text, "architectural")
    assert_not_contains(yoda_pack_text, "software structure")
    assert_not_contains(yoda_pack_text, "technical content")
    assert_not_contains(bjarne_pack_text, "when reviewing code")
    assert_not_contains(sam_pack_text, "orchestration and synthesis")
    assert_not_contains(sam_pack_text, "operational tasks")
    print("ok")

    print("=== behavior test passed ===")


if __name__ == "__main__":
    main()
