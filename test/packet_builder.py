#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_SKILL = ROOT_DIR / "skills" / "orchestrator-core" / "SKILL.md"
SAM_PACK = ROOT_DIR / "assets" / "personalities" / "sam-harris.yaml"
JESSE_PACK = ROOT_DIR / "assets" / "personalities" / "jesse-pinkman.yaml"
ARCH_REVIEW_CORE = ROOT_DIR / "skills" / "architecture-review-core" / "SKILL.md"
BJARNE_PACK = ROOT_DIR / "assets" / "personalities" / "bjarne-stroustrup.yaml"
YODA_PACK = ROOT_DIR / "assets" / "personalities" / "yoda.yaml"


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
        "guardrails",
        "anti_patterns",
    ):
        data[key] = parse_yaml_list(lines, key)

    for key in ("ambiguity_policy", "tradeoff_policy", "compression_policy"):
        data[key] = parse_yaml_block(lines, key)

    data["prompt_overlay"] = parse_yaml_block(lines, "prompt_overlay")
    return data


def build_instruction_packet(core_text: str, pack: dict[str, object] | None) -> str:
    if pack is None:
        return core_text.strip()

    sections = [
        core_text.strip(),
        "",
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
        "Guardrails:",
        *[f"- {item}" for item in pack["guardrails"]],
        "",
        "Anti-patterns:",
        *[f"- {item}" for item in pack["anti_patterns"]],
        "",
        "Overlay prompt:",
        str(pack["prompt_overlay"]),
    ]
    return "\n".join(sections).strip()


def load_neutral_packet() -> str:
    return build_instruction_packet(read_text(CORE_SKILL), None)


def load_sam_packet() -> str:
    return load_packet(CORE_SKILL, SAM_PACK)


def load_jesse_packet() -> str:
    return load_packet(CORE_SKILL, JESSE_PACK)


def load_packet(core_path: Path, pack_path: Path | None = None) -> str:
    if pack_path is None:
        return build_instruction_packet(read_text(core_path), None)
    return build_instruction_packet(read_text(core_path), parse_simple_yaml(pack_path))


def load_architecture_neutral_packet() -> str:
    return load_packet(ARCH_REVIEW_CORE)


def load_bjarne_architecture_packet() -> str:
    return load_packet(ARCH_REVIEW_CORE, BJARNE_PACK)


def load_yoda_architecture_packet() -> str:
    return load_packet(ARCH_REVIEW_CORE, YODA_PACK)
