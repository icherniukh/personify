---
name: list-personas
description: Lists discovered personify persona assets and summarizes what each one is for.
---

# List Personas

Use this skill when the user wants to know which personify persona assets are currently available.

## Source Of Truth

Source persona assets currently live under:

- `src/assets/personalities/`

Read those YAML files directly when listing available personas.

An optional helper script may also be present:

```bash
python3 scripts/persona_list.py
```

Only use that helper if the repo-relative path exists from your current working directory.
Do not assume the current working directory is the repository root.

## What To Report

For each discovered pack, report:

- `id`
- `display_name`
- `quality_level`
- `summary`

If useful, mention that any listed pack can be used for a session with `use-persona` or for one request with `as-persona`.

## Important Distinction

Listing a persona asset does not activate it automatically.

A pack can still be used in two ways:

1. Session default:
   Use `use-persona` to make it the default voice and reasoning lens for the session.
2. One task:
   Use `as-persona` to apply it to the current request or thread.

## Limitation

Persona activation is currently a prompt-level convention, not a compiled runtime object. That means:

- it can work without a prebuilt persona-specific wrapper
- it does not automatically create a new installed skill
- it depends on the assistant correctly resolving the requested pack
