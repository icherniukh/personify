# Promptonality

`promptonality` is a platform-agnostic source package for portable persona
assets and dynamic composition.

The project promise is asset-first:

- personas are YAML assets, not hardcoded skills
- bundled personas are starter packs and regression fixtures
- users should be able to add, update, validate, and compose their own packs
- workflows stay separate from persona assets
- generated install surfaces are derived outputs
- persona packs do not include local guardrail or restriction sections

If adding a persona requires changing framework code or creating a wrapper skill,
that is a bug in the framework direction.

## Core Model

The framework has three moving parts:

1. **Persona assets**
   YAML packs stored under an asset root.
2. **Entrypoint skills**
   `persona-list`, `persona-apply`, and `persona-start` discover and load packs.
3. **Workflows**
   Neutral workflow instructions such as orchestration or architecture review.

Composition rule:

- base workflow first
- persona asset second
- correctness, safety, and task completion win if the overlay conflicts

Static per-persona wrapper skills are not the active model. Historical examples
remain under [`archive/`](./archive).

Pack-level `guardrails`, `anti_patterns`, and similar restriction sections are
intentionally not part of the current pack shape. They made personas less
creative, while the host model already supplies the necessary behavioral
boundaries. Improve packs by strengthening positive persona material and
evaluating outputs, not by adding local prohibitions.

## Source Of Truth

Use `src/` as the authored source:

- neutral metadata: [`src/package.json`](./src/package.json)
- source skills: [`src/skills/`](./src/skills)
- source asset root: [`src/assets/personalities/`](./src/assets/personalities)

Do not treat generated Codex, Claude, Gemini, or root-level compatibility copies
as authored truth. Regenerate platform packages from source.

## Persona Assets

Bundled source packs live in:

```text
src/assets/personalities/
```

List them with:

```bash
python3 plugins/promptonality/scripts/persona_list.py
```

The list is intentionally dynamic. Do not maintain a manual catalog in this
README. New user-created or generated packs should follow the contract in:

```text
docs/personality-pack-contract.md
```

## Installation Surfaces

Build all platform packages with:

```bash
python3 plugins/promptonality/scripts/package.py build --target all
```

Generated packages are ignored build outputs:

- `codex/`
- `claude/`
- `gemini/`

Codex, Claude, and Gemini are peer adapters. None is the canonical source.

Use native local development flows for each host:

- Codex: generated `.codex-plugin/plugin.json` under `codex/`
- Claude: `claude --plugin-dir plugins/promptonality/claude`
- Gemini: `gemini extensions link plugins/promptonality/gemini`

## Active Source Skills

- [`src/skills/persona-start/SKILL.md`](./src/skills/persona-start/SKILL.md)
- [`src/skills/persona-apply/SKILL.md`](./src/skills/persona-apply/SKILL.md)
- [`src/skills/persona-list/SKILL.md`](./src/skills/persona-list/SKILL.md)
- [`src/skills/persona-extract/SKILL.md`](./src/skills/persona-extract/SKILL.md)
- [`src/skills/persona-extract-online/SKILL.md`](./src/skills/persona-extract-online/SKILL.md)
- [`src/skills/orchestrator-core/SKILL.md`](./src/skills/orchestrator-core/SKILL.md)
- [`src/skills/architecture-review-core/SKILL.md`](./src/skills/architecture-review-core/SKILL.md)

## Usage

Use `persona-list` to inspect discovered packs.

Use `persona-start` when a workflow-plus-pack combination should govern the
session.

Use `persona-apply` when the overlay should apply to one task or thread.

Examples:

- `List the available promptonality packs.`
- `Use the Hikaru Nakamura persona for this architecture review.`
- `Apply my local review-coach persona to this task.`
- `Generate a new personality pack for this public figure.`

## Testing

Smoke test:

```bash
bash plugins/promptonality/test/run-test.sh
```

Package sync checks:

```bash
python3 plugins/promptonality/scripts/package.py check --target all
python3 plugins/promptonality/scripts/package.py doctor
```

Live model comparison:

```bash
OPENAI_API_KEY=... OPENAI_MODEL=... \
python3 plugins/promptonality/test/live_model_test.py --repeats 3
```

Architecture comparison:

```bash
OPENAI_API_KEY=... OPENAI_MODEL=... \
python3 plugins/promptonality/test/architecture_live_test.py --repeats 3
```

Testing should move toward dynamic pack validation over every discovered asset,
not hardcoded checks for a fixed bundled catalog.

Persona quality evaluation is defined in:

```text
docs/persona-evaluation.md
```
