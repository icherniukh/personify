---
name: persona-list
description: Lists the installed promptonality personality packs and summarizes what each one is for.
---

# Persona List

Use this skill when the user wants to know which promptonality personalities are currently installed.

## Source Of Truth

Installed personalities live under:

- `plugins/promptonality/assets/personalities/`

Read those YAML files directly when listing available personalities.

An optional helper script may also be present:

```bash
python3 plugins/promptonality/scripts/persona_list.py
```

Only use that helper if the repo-relative path exists from your current working directory.
Do not assume the current working directory is the repository root.

## What To Report

For each installed pack, report:

- `id`
- `display_name`
- `quality_level`
- `summary`

If useful, also point out likely pairings with current packaged workflows or variants.

## Important Distinction

Listing a personality pack does not mean every possible workflow-plus-pack combination already exists as a named variant skill.

A pack can still be used in two ways:

1. Existing named variant:
   Use a prepared wrapper such as `sam-harris-orchestrator`.
2. Explicit composition:
   Use `persona-apply`, `persona-start`, or direct instruction to combine a compatible workflow with an installed pack even if no dedicated wrapper has been created yet.

## Limitation

Ad-hoc composition is currently a prompt-level convention, not a compiled runtime object. That means:

- it can work without a prebuilt combo
- but it does not automatically create a new installed variant skill
- and it depends on the assistant correctly resolving the requested workflow and pack
