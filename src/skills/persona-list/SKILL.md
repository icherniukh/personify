---
name: persona-list
description: Lists discovered promptonality persona assets and summarizes what each one is for.
---

# Persona List

Use this skill when the user wants to know which promptonality persona assets are currently available.

## Source Of Truth

Source persona assets currently live under:

- `plugins/promptonality/src/assets/personalities/`

Read those YAML files directly when listing available personas.

An optional helper script may also be present:

```bash
python3 plugins/promptonality/scripts/persona_list.py
```

Only use that helper if the repo-relative path exists from your current working directory.
Do not assume the current working directory is the repository root.

## What To Report

For each discovered pack, report:

- `id`
- `display_name`
- `quality_level`
- `summary`

If useful, also point out likely pairings with current workflows such as `orchestrator-core` or `architecture-review-core`.

## Important Distinction

Listing a persona asset does not mean every possible workflow-plus-pack combination already exists as a named installed skill.

A pack can still be used in two ways:

1. Existing named skill:
   Use a prepared installed skill if one already exists.
2. Explicit composition:
   Use `persona-apply`, `persona-start`, or direct instruction to combine a compatible workflow with a discovered pack even if no dedicated wrapper has been created yet.

## Limitation

Ad-hoc composition is currently a prompt-level convention, not a compiled runtime object. That means:

- it can work without a prebuilt combo
- but it does not automatically create a new installed skill
- and it depends on the assistant correctly resolving the requested workflow and pack
