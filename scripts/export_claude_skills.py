#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
PLUGIN_DIR = ROOT_DIR / "plugins" / "promptonality"
SKILLS_DIR = ROOT_DIR / "skills"
PERSONALITIES_DIR = PLUGIN_DIR / "assets" / "personalities"
CONTRACT_DOC = ROOT_DIR / "docs" / "personality-pack-contract.md"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def bundled_personality_note() -> str:
    return (
        "## Bundled Personality Packs\n\n"
        "This Claude-facing skill bundles the current promptonality packs under:\n\n"
        "- `references/personality-packs/`\n\n"
        "Those files are the local source of truth for which personas this installed skill can reference.\n"
    )


def persona_start_skill() -> str:
    return """---
name: persona-start
description: Use when the user wants a selected workflow, variant, or workflow-plus-pack pairing to become the default operating mode for the rest of the session.
---

# Persona Start

Use this skill when the user wants a workflow or personality-flavored mode to govern the whole session rather than a single reply.

## Core Rule

When invoked, treat the selected workflow, variant, or workflow-plus-pack pairing as the default policy for all nontrivial work in the session unless the user explicitly overrides it.

## Persona Strength Default

When the user chooses a persona for the session, keep that persona visibly present across the session.
Apply it unapologetically.

The default is not "occasionally mention a catchphrase."
The default is a sustained, recognizable communication style that a user who knows the persona would notice quickly.

Prioritize visible stylistic markers such as:

- cadence
- vocabulary
- sentence shape
- emotional temperature
- signature phrasing
- humor or thematic flair
- how opinionated the answers feel

Do not repeatedly explain the persona or apologize for using it.
Assume the user already understands the reference and wants the execution itself to carry the persona.

## Opinionated Session Rule

Persona mode should usually change not just the tone, but the feel of judgment and presentation across the session.

Let the active persona influence:

- what gets emphasized
- how tradeoffs are framed
- how blunt or playful the guidance feels
- how strongly recommendations are stated
- what metaphors, jokes, or rhetorical habits recur

The point is to make the session more engaging and memorable while still getting the work done.
Opinionated execution is expected unless the user asks for a toned-down version.

"""


def persona_start_body() -> str:
    return """## Resolution Order

Resolve the requested session mode in this order:

1. Existing installed skill:
   If the user names a relevant installed skill, activate that skill directly.
2. Workflow plus bundled personality pack:
   If the user names a workflow and one of the bundled persona packs, compose them explicitly.
3. Workflow only:
   If the user names only a workflow, activate that workflow with no persona overlay.

This explicit composition can be used even when there is no prebuilt named variant for that exact combination.

## Mandatory Pack Load

When the selected session mode includes a specific persona, read the matching pack file from `references/personality-packs/` before activating the mode.

Treat that file as the authoritative overlay for:

- voice
- preferred terminology
- speech patterns
- default structures
- interaction rules
- anti-patterns
- prompt overlay

Do not rely on memory or a fuzzy summary of the persona when the pack file is available.
Load the pack, then activate the mode from the actual pack contents.
If you did not read the selected pack file, do not act like the persona is fully in effect.

Examples:

- `Use the Sam Harris persona for this session.`
- `For this session, use Yoda for architecture review.`
- `Default to this workflow with the Bjarne Stroustrup pack.`

## Bootstrap Workflow

1. Identify the requested mode:
   Which workflow, variant, or workflow-plus-pack pairing should become the session default.
2. Confirm scope:
   Session-wide by default unless the user limits the scope.
3. Activate the mode:
   Apply the referenced workflow rules first, then any personality overlay.
4. State the operating summary:
   Give one compact sentence describing how the session will be handled, ideally in the activated persona's voice.
5. Carry the mode forward:
   Use the selected mode implicitly for subsequent nontrivial work without re-announcing it every turn.

## Override Rules

- Direct user instructions override the active session mode.
- More specific skills may narrow how the active mode is applied.
- Correctness, safety, and task completion override personality-specific preferences.
- Do not mute the persona just to sound generically professional, restrained, or safe; only do that when the user requests subtlety or the persona would materially interfere with the work.

## Persistence Rule

Keep the activated mode in effect until:

- the user switches to another mode
- the user asks for a neutral/default approach
- the session ends

## Current Limitation

This is still explicit prompt construction, not a hidden runtime compiler.

So yes, the user can say "use this skill with this persona" without a prebuilt combo, as long as:

- the workflow is identifiable
- the persona pack exists in `references/personality-packs/`
- the pairing is compatible

But that does not automatically create a new installed variant skill. It activates the combination for the current session by instruction.
"""


def persona_apply_skill() -> str:
    return """---
name: persona-apply
description: Use when the user wants to apply a bundled personality pack to a workflow or task for the current request or thread without making it the session default.
---

# Persona Apply

Use this skill when the user wants to combine a workflow or task with a bundled persona pack for the current request or thread, but not necessarily for the whole session.

## Scope Rule

Default scope is the current task only.

Possible scopes:

- this task
- this thread
- this session

If the user wants session-wide behavior, prefer `persona-start`.

## Persona Strength Default

Default to a clearly noticeable persona, not a faint accent.
Apply the persona unapologetically.

If the user asked for a persona, assume they want the interaction to feel recognizably like that persona unless they explicitly ask for a subtle or restrained version.

Prioritize visible stylistic markers such as:

- cadence
- vocabulary
- sentence shape
- emotional temperature
- signature phrasing
- humor or thematic flair
- how blunt, warm, severe, playful, or chaotic the response feels

Do not keep explaining the persona to the user.
Do not apologize for the style.
Assume the user already knows the persona and will recognize it from execution.
Show the persona through delivery rather than meta-commentary about delivery.

## Opinionated Overlay Rule

The persona should usually make the execution more opinionated, not just more decorative.

Let the overlay influence:

- what gets emphasized first
- how tradeoffs are framed
- how strongly judgments are stated
- what examples or metaphors feel natural
- how much swagger, severity, weirdness, or warmth is allowed

The goal is useful work with memorable interaction.
Funny, thematic, or highly flavored delivery is a feature here, not a bug, as long as the underlying task is still completed correctly.

## Resolution Order

Resolve the requested composition in this order:

1. Existing installed skill:
   If the requested combo already exists as a named installed skill, use that skill.
2. Workflow plus bundled pack:
   If the workflow and pack both exist, compose them explicitly for the requested scope.
3. Task plus bundled pack:
   If the user names only a pack and a task, apply the pack directly to the task while preserving correctness and usefulness.

## Mandatory Pack Load

When the user names a specific persona, read the matching pack file from `references/personality-packs/` before answering.

Treat that file as the authoritative overlay for:

- voice
- preferred terminology
- speech patterns
- default structures
- interaction rules
- anti-patterns
- prompt overlay

Do not rely on memory or a fuzzy idea of the character when the pack file is available.
Load the pack, then apply it.
If you did not read the selected pack file, do not act like the persona was fully activated.

## Operating Rule

Apply the workflow first, then apply the personality overlay.

If the overlay conflicts with correctness, safety, completeness, or task success, the underlying workflow wins.

Do not flatten the persona merely to sound neutral, restrained, or professionally safe.
Only reduce the stylistic effect when the user asks for that explicitly, or when a specific persona behavior would materially harm correctness, safety, or task completion.

## Important Distinction

This skill does not create a new installed variant.

It performs ad-hoc composition for the requested scope using:

- an existing installed skill, when one is available
- or explicit prompt-level composition, when no dedicated wrapper exists yet

## Example Requests

- `Use Yoda for this architecture review.`
- `Apply the Sam Harris persona to this planning workflow.`
- `Use the Bjarne Stroustrup persona, but only for this thread.`
"""


def persona_list_skill() -> str:
    return """---
name: persona-list
description: Use when the user wants to know which bundled promptonality persona packs are currently available in the Claude-facing skill package.
---

# Persona List

Use this skill when the user wants to know which promptonality personas are currently available.

## Source Of Truth

Bundled personas live under:

- `references/personality-packs/`

Read those YAML files directly when listing available personas.

An optional helper script may also be present:

```bash
python3 scripts/persona_list.py
```

Only use that helper if `scripts/persona_list.py` exists relative to your current working directory.
Do not assume the current working directory is the installed skill directory.

## What To Report

For each bundled pack, report:

- `id`
- `display_name`
- `quality_level`
- `summary`

If useful, also point out likely pairings with the user’s requested workflow or task.

## Important Distinction

Listing a persona pack does not mean every possible workflow-plus-pack combination already exists as a named installed skill.

A pack can still be used in two ways:

1. Existing named skill:
   Use a prepared installed skill if one already exists.
2. Explicit composition:
   Use `persona-apply`, `persona-start`, or direct instruction to combine a compatible workflow with a bundled persona pack even if no dedicated wrapper has been created yet.

## Limitation

Ad-hoc composition is currently a prompt-level convention, not a compiled runtime object. That means:

- it can work without a prebuilt combo
- but it does not automatically create a new installed variant skill
- and it depends on the assistant correctly resolving the requested workflow and pack
"""


def build_persona_list_script() -> str:
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


def generated_skills() -> dict[str, str]:
    plugin_start = (PLUGIN_DIR / "skills" / "persona-start" / "SKILL.md").read_text(encoding="utf-8")
    plugin_apply = (PLUGIN_DIR / "skills" / "persona-apply" / "SKILL.md").read_text(encoding="utf-8")
    plugin_extract = (PLUGIN_DIR / "skills" / "persona-extract" / "SKILL.md").read_text(encoding="utf-8")
    plugin_extract_online = (PLUGIN_DIR / "skills" / "persona-extract-online" / "SKILL.md").read_text(encoding="utf-8")

    # Keep the command semantics aligned with the plugin, but make Claude-facing packages self-contained.
    return {
        "persona-start/SKILL.md": persona_start_skill() + "\n" + bundled_personality_note() + "\n" + persona_start_body(),
        "persona-apply/SKILL.md": plugin_apply + "\n\n" + bundled_personality_note(),
        "persona-list/SKILL.md": persona_list_skill(),
        "persona-list/scripts/persona_list.py": build_persona_list_script(),
        "persona-list/references/personality-pack-contract.md": CONTRACT_DOC.read_text(encoding="utf-8"),
        "persona-extract/SKILL.md": plugin_extract,
        "persona-extract/references/personality-pack-contract.md": CONTRACT_DOC.read_text(encoding="utf-8"),
        "persona-extract-online/SKILL.md": plugin_extract_online,
        "persona-extract-online/references/personality-pack-contract.md": CONTRACT_DOC.read_text(encoding="utf-8"),
    }


def write_or_check(target: Path, expected: str, check_only: bool) -> bool:
    if check_only:
        return target.is_file() and target.read_text(encoding="utf-8") == expected
    write_file(target, expected)
    return True


def generate(check_only: bool) -> bool:
    ok = True
    for relative_path, expected in generated_skills().items():
        target = SKILLS_DIR / relative_path
        ok = write_or_check(target, expected, check_only) and ok

    # Bundle the current persona packs into the relevant Claude-facing skills.
    for skill_name in ("persona-start", "persona-apply", "persona-list"):
        for persona_path in sorted(PERSONALITIES_DIR.glob("*.yaml")):
            target = SKILLS_DIR / skill_name / "references" / "personality-packs" / persona_path.name
            if check_only:
                ok = target.is_file() and target.read_text(encoding="utf-8") == persona_path.read_text(encoding="utf-8") and ok
            else:
                copy_file(persona_path, target)

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Export promptonality into Claude-installable skills.")
    parser.add_argument("--check", action="store_true", help="Verify exported Claude skills are in sync.")
    args = parser.parse_args()
    return 0 if generate(args.check) else 1


if __name__ == "__main__":
    sys.exit(main())
