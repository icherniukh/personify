---
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
