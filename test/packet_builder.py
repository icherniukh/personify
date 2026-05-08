#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SAM_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "sam-harris.yaml"
JESSE_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "jesse-pinkman.yaml"
BJARNE_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "bjarne-stroustrup.yaml"
YODA_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "yoda.yaml"
NEUTRAL_TASK = """You are a neutral assistant. Complete the user's task correctly, clearly, and without applying a specific persona overlay."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_yaml_list(lines: list[str], key: str) -> list[str]:
    items: list[str] = []
    in_section = False
    base_indent = None

    for line in lines:
        if not in_section:
            if line.startswith(f"{key}:"):
                in_section = True
                base_indent = len(line) - len(line.lstrip(" "))
            continue

        if not line.strip():
            continue

        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent <= base_indent and not line.lstrip().startswith("- "):
            break

        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])

    return items


def parse_yaml_block(lines: list[str], key: str) -> str:
    in_block = False
    block_indent = None
    values: list[str] = []

    for line in lines:
        if not in_block:
            if line.startswith(f"{key}: |"):
                in_block = True
            continue

        if not line.strip():
            values.append("")
            continue

        current_indent = len(line) - len(line.lstrip(" "))
        if block_indent is None:
            block_indent = current_indent

        if current_indent < block_indent:
            break

        values.append(line[block_indent:])

    return "\n".join(values).strip()


def parse_yaml_map(lines: list[str], key: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    in_section = False
    base_indent = None

    for line in lines:
        if not in_section:
            if line.startswith(f"{key}:"):
                in_section = True
                base_indent = len(line) - len(line.lstrip(" "))
            continue

        if not line.strip():
            continue

        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent <= base_indent:
            break

        stripped = line.strip()
        if ": " in stripped:
            subkey, value = stripped.split(": ", 1)
            mapping[subkey] = value

    return mapping


def parse_simple_yaml(path: Path) -> dict[str, object]:
    lines = read_text(path).splitlines()
    data: dict[str, object] = {}

    for line in lines:
        if not line.strip() or line.startswith(" "):
            continue
        if ": " in line:
            key, value = line.split(": ", 1)
            if key not in {
                "id",
                "display_name",
                "summary",
                "quality_level",
            }:
                continue
            data[key] = value

    data["voice"] = parse_yaml_map(lines, "voice")

    for key in (
        "interaction_stance",
        "value_profile",
        "reasoning_style",
        "preferred_terminology",
        "speech_patterns",
        "default_structures",
        "interaction_rules",
    ):
        data[key] = parse_yaml_list(lines, key)

    expressive_depth: dict[str, object] = {}
    for subkey in ("side_note_style", "thematic_tangent_pattern", "focus_drift_recovery"):
        val = parse_yaml_block(lines, subkey)
        if val:
            expressive_depth[subkey] = val
    expressive_depth["thematic_signature"] = parse_yaml_list(lines, "thematic_signature")
    data["expressive_depth"] = expressive_depth

    for key in ("ambiguity_policy", "tradeoff_policy", "compression_policy"):
        data[key] = parse_yaml_block(lines, key)

    data["prompt_overlay"] = parse_yaml_block(lines, "prompt_overlay")
    return data


def build_activation_packet(pack: dict[str, object], scope: str, source_path: Path | None) -> list[str]:
    voice = pack["voice"]
    voice_markers = [f"{key}: {value}" for key, value in voice.items()]
    reasoning_habits = list(pack["reasoning_style"])
    source = str(source_path.relative_to(ROOT_DIR)) if source_path else "unknown"

    return [
        "## Persona Activation Packet",
        f"Persona id: {pack['id']}",
        f"Display name: {pack['display_name']}",
        f"Scope: {scope}",
        "Strength: strong",
        f"Loaded pack: {source}",
        "Voice markers:",
        *[f"- {item}" for item in voice_markers[:5]],
        "Reasoning habits:",
        *[f"- {item}" for item in reasoning_habits[:2]],
        "Drift correction:",
        "- If the response becomes generic, reload the pack and restore these markers before answering.",
        "",
    ]


def build_instruction_packet(
    core_text: str,
    pack: dict[str, object] | None,
    source_path: Path | None = None,
    scope: str = "task",
) -> str:
    if pack is None:
        return core_text.strip()

    sections = [
        core_text.strip(),
        "",
        *build_activation_packet(pack, scope, source_path),
        "## Personality Overlay",
        f"Identity: {pack['display_name']}",
        f"Summary: {pack['summary']}",
        "",
        "Voice:",
        *[f"- {key}: {value}" for key, value in pack["voice"].items()],
        "",
        "Interaction stance:",
        *[f"- {item}" for item in pack["interaction_stance"]],
        "",
        "Value profile:",
        *[f"- {item}" for item in pack["value_profile"]],
        "",
        "Reasoning style:",
        *[f"- {item}" for item in pack["reasoning_style"]],
        "",
        "Preferred terminology:",
        *[f"- {item}" for item in pack["preferred_terminology"]],
        "",
        "Speech patterns:",
        *[f"- {item}" for item in pack["speech_patterns"]],
        "",
        "Default structures:",
        *[f"- {item}" for item in pack["default_structures"]],
        "",
        "Ambiguity policy:",
        str(pack["ambiguity_policy"]),
        "",
        "Tradeoff policy:",
        str(pack["tradeoff_policy"]),
        "",
        "Compression policy:",
        str(pack["compression_policy"]),
        "",
        "Interaction rules:",
        *[f"- {item}" for item in pack["interaction_rules"]],
        "",
        "Overlay prompt:",
        str(pack["prompt_overlay"]),
    ]

    ed = pack.get("expressive_depth", {})
    if isinstance(ed, dict) and ed:
        sections += [
            "",
            "Expressive depth:",
            "Side note style:",
            str(ed.get("side_note_style", "")),
            "",
            "Thematic tangent pattern:",
            str(ed.get("thematic_tangent_pattern", "")),
            "",
            "Focus drift recovery:",
            str(ed.get("focus_drift_recovery", "")),
            "",
            "Thematic signature:",
            *[f"- {item}" for item in ed.get("thematic_signature", [])],
        ]

    return "\n".join(sections).strip()


def load_neutral_packet() -> str:
    return build_instruction_packet(NEUTRAL_TASK, None)


def load_sam_packet() -> str:
    return load_packet(SAM_PACK)


def load_jesse_packet() -> str:
    return load_packet(JESSE_PACK)


def load_yoda_packet() -> str:
    return load_packet(YODA_PACK)


def load_packet(pack_path: Path | None = None, task: str = NEUTRAL_TASK) -> str:
    if pack_path is None:
        return build_instruction_packet(task, None)
    return build_instruction_packet(task, parse_simple_yaml(pack_path), source_path=pack_path)


def load_architecture_neutral_packet() -> str:
    return load_packet(task="Review the architecture clearly and concretely.")


def load_bjarne_architecture_packet() -> str:
    return load_packet(BJARNE_PACK, task="Review the architecture clearly and concretely.")


def load_yoda_architecture_packet() -> str:
    return load_packet(YODA_PACK, task="Review the architecture clearly and concretely.")
