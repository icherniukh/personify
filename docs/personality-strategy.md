# Personality Strategy

This document defines the repo’s planned approach for personality and persona handling, especially for Codex.

## Core Decision

Do **not** model personalities by spreading persona text across unrelated skills.

Use a separate, dedicated personality-oriented plugin strategy instead.

## Why a Separate Plugin

Personality is cross-cutting:

- it can apply to many domains
- it is not the same thing as the workflow logic of a skill
- it benefits from shared assets, conventions, and packaging

A separate plugin allows the repo to keep:

- domain skills focused on task execution
- persona logic reusable and centralized
- future Codex UI metadata and dependencies bundled cleanly

## Relationship to Codex Global Personality

Codex may expose a coarse global `personality` setting, but this repo should not depend on undocumented or custom semantics for that field.

Working assumption:

- global `personality` is broad style control
- detailed persona behavior belongs at the skill/plugin layer

That avoids coupling the repo to behavior that is not yet documented as a stable extension point.

## Planned Plugin Direction

Tentative plugin names:

- `personality-kit`
- or a refined `persona-forge`

Initial scope:

- `persona-forge`
- `persona-forge-online`
- a small curated set of reusable persona packs
- optional Codex/OpenAI UI metadata via `agents/openai.yaml`

Out of scope for the first version:

- turning every skill into a persona-aware skill
- encoding persona behavior in runtime-specific Claude agents
- depending on hidden Codex config internals

## Reworking `persona-forge`

Current `persona-forge` skills are prompt generators. The next step should turn them into a reusable system.

Target responsibilities:

- generate normalized persona packs
- support fast local generation and research-backed generation
- distinguish one-off prompts from reusable persona assets
- make persona outputs easy to compose with other skills later

## Persona Pack Contract

The plugin should standardize a small reusable persona format.

Planned fields:

- `id`
- `display_name`
- `summary`
- `voice`
- `reasoning_style`
- `interaction_rules`
- `guardrails`
- `task_fit`
- `anti_patterns`
- `default_prompt_wrapper`
- `provenance`
- `quality_level`

Interpretation:

- persona packs are overlays, not whole domain workflows
- they bias style and reasoning emphasis
- they must preserve usefulness over performance
- they must not silently override safety or correctness expectations from the underlying task workflow

## Composition Rule

Planned composition model:

- the **domain skill** supplies task workflow
- the **persona pack** supplies voice and reasoning flavor
- a plugin-level or prompt-level composition layer applies the persona when requested

For now, this should be documented as a convention rather than forced into a new skill-standard field.

## Why Not Skill-Level Persona Metadata Everywhere

That approach would:

- duplicate persona logic across many skills
- make maintenance harder
- blur the line between workflow knowledge and stylistic overlays
- make later pluginization more painful

Keeping personality separate is the cleaner long-term model.

## Provenance

This document condenses direction from:

- `skills/persona-forge/SKILL.md`
- `skills/persona-forge-online/SKILL.md`
- repo cleanup planning around Codex support
- earlier design material in `up_claude/`
