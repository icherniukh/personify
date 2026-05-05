# Promptonality

`promptonality` is the repo-local plugin for portable personality packs plus neutral workflow cores.

The current model is dynamic composition:

- keep workflow logic in neutral core skills
- keep persona logic in standalone YAML packs
- use `persona-start` or `persona-apply` to combine them at session or task scope

Static per-persona wrapper skills are not the active install surface anymore. Historical examples remain under [`archive/`](./archive).

## Installation Surfaces

### Codex

Promptonality is implemented here as a repo-local plugin source:

- manifest: [`.codex-plugin/plugin.json`](./.codex-plugin/plugin.json)
- source skills: [`skills/`](./skills)
- source packs: [`assets/personalities/`](./assets/personalities)

Use this folder as the source of truth for Codex packaging work. Do not document a made-up stable `~/.codex/plugins/...` install path unless Codex runtime docs explicitly support one.

### Claude Standalone Skills

The Claude-facing standalone persona skills are exported into the repo root under:

- [`skills/persona-start/`](../../skills/persona-start)
- [`skills/persona-apply/`](../../skills/persona-apply)
- [`skills/persona-list/`](../../skills/persona-list)
- [`skills/persona-extract/`](../../skills/persona-extract)
- [`skills/persona-extract-online/`](../../skills/persona-extract-online)

Regenerate them with:

```bash
python3 plugins/promptonality/scripts/export_claude_skills.py
```

### Claude Plugin Package

The generated Claude plugin package lives under:

- [`claude-plugin/`](./claude-plugin)

Regenerate it with:

```bash
python3 plugins/promptonality/scripts/export_claude_plugin.py
```

## Current Structure

Active plugin skills:

- [`skills/orchestrator-core/SKILL.md`](./skills/orchestrator-core/SKILL.md)
- [`skills/architecture-review-core/SKILL.md`](./skills/architecture-review-core/SKILL.md)
- [`skills/persona-start/SKILL.md`](./skills/persona-start/SKILL.md)
- [`skills/persona-apply/SKILL.md`](./skills/persona-apply/SKILL.md)
- [`skills/persona-list/SKILL.md`](./skills/persona-list/SKILL.md)
- [`skills/persona-extract/SKILL.md`](./skills/persona-extract/SKILL.md)
- [`skills/persona-extract-online/SKILL.md`](./skills/persona-extract-online/SKILL.md)

Bundled personality packs:

- [`assets/personalities/sam-harris.yaml`](./assets/personalities/sam-harris.yaml)
- [`assets/personalities/bjarne-stroustrup.yaml`](./assets/personalities/bjarne-stroustrup.yaml)
- [`assets/personalities/yoda.yaml`](./assets/personalities/yoda.yaml)
- [`assets/personalities/jesse-pinkman.yaml`](./assets/personalities/jesse-pinkman.yaml)

Historical wrapper examples:

- [`archive/sam-harris-orchestrator/SKILL.md`](./archive/sam-harris-orchestrator/SKILL.md)
- [`archive/bjarne-stroustrup-architecture-review/SKILL.md`](./archive/bjarne-stroustrup-architecture-review/SKILL.md)
- [`archive/yoda-architecture-review/SKILL.md`](./archive/yoda-architecture-review/SKILL.md)

## Usage

Use the neutral cores directly when you want the workflow behavior with no persona overlay.

Use `persona-start` when you want a workflow-plus-pack combination to govern the whole session.

Use `persona-apply` when you want the overlay for one task or thread only.

Use `persona-list` when you want to inspect which packs are bundled, or run:

```bash
python3 plugins/promptonality/scripts/persona_list.py
```

Examples:

- `Use orchestrator-core with the Sam Harris pack for this session.`
- `Apply Yoda to this architecture review only.`
- `List the available promptonality packs.`
- `Generate a new personality pack for this public figure.`

Composition rule:

- base workflow first
- persona pack second
- correctness, safety, and task completion win if the overlay conflicts

## Testing

Smoke test:

```bash
bash plugins/promptonality/test/run-test.sh
```

Claude standalone export sync:

```bash
python3 plugins/promptonality/scripts/export_claude_skills.py --check
```

Claude plugin export sync:

```bash
python3 plugins/promptonality/scripts/export_claude_plugin.py --check
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
