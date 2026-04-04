# Personality Strategy

This document defines the repo’s approach to personality and persona handling, especially for Codex.

## Core Decision

Do **not** model personalities by spreading persona text across unrelated skills.

Use a separate personality-oriented plugin instead.

## Why a Separate Plugin

Personality is cross-cutting:

- it can apply to many domains
- it is not the same thing as workflow logic
- it benefits from shared assets, conventions, and packaging

A separate plugin lets the repo keep:

- domain skills focused on execution
- personality logic reusable and centralized
- future Codex UI metadata and dependencies bundled cleanly

## Core Idea

Treat personality as a bounded cognitive lens.

That means the plugin should not merely control tone. It should control how the same underlying workflow:

- frames the problem
- exposes assumptions
- handles ambiguity
- reveals tradeoffs
- compresses information
- prefers certain answer structures

When a user explicitly assigns a persona through `persona-apply` or `persona-start`, the surface style should also be clearly noticeable by default.
The right target is not a barely detectable accent.
The right target is recognizable voice plus recognizable framing, while still staying inside the workflow's correctness and safety bounds.

## Invariant vs Variable Layers

### Invariant

These should not change across personalities:

- task completion
- truthfulness
- safety
- operational competence
- tool discipline

### Variable

These should be allowed to change:

- voice
- framing priorities
- uncertainty style
- tradeoff style
- compression style
- answer structure
- interaction stance

This is the key design shift: personality is not just a stylistic overlay. It is a portable way to change how the same capability thinks and communicates within hard operational bounds.

In practice, that means visible style is a feature, not an embarrassment.
If the user asked for Jesse Pinkman, Yoda, or Sam Harris, the interaction should normally feel obviously flavored to someone who knows that persona.
The system can rely on the user's prior familiarity rather than stopping to explain why the wording is stylized.
Persona assignment through `persona-apply` or `persona-start` should therefore be applied unapologetically by default, not softened into a timid imitation just to preserve generic professionalism.

The portable part matters. Reusable personality packs should stay workflow-agnostic unless a domain-specific pack is explicitly the goal. Domain instructions belong in the neutral workflow or the thin variant that consumes the pack.

## Relationship to Codex Global Personality

Codex may expose a coarse global `personality` setting, but this repo should not depend on undocumented or custom semantics for that field.

Working assumption:

- global `personality` is broad style control
- detailed persona behavior belongs at the skill/plugin layer

That avoids coupling the repo to behavior that is not yet documented as a stable extension point.

For Codex, the install unit remains the plugin under `plugins/promptonality/`.

For Claude, the repo now exports standalone skills under `skills/persona-*` from that same source using:

```bash
python3 plugins/promptonality/scripts/export_claude_skills.py
```

For Claude plugin packaging, the repo also generates:

```text
plugins/promptonality/claude-plugin/
```

with:

```bash
python3 plugins/promptonality/scripts/export_claude_plugin.py
```

That keeps one conceptual system while supporting both Claude’s standalone skill installation model and its plugin package model.

## Plugin Direction

Current plugin direction:

- `promptonality`
- with `persona-extract` and `persona-extract-online` as packaged extraction skills

Current scope:

- reusable personality packs
- neutral workflow cores
- `persona-start` and `persona-apply` for dynamic composition at session or task scope
- personality catalog/listing so installed packs are discoverable
- persona extraction skills for generating new packs

Out of scope for the current version:

- dedicated pre-built variant skills that fork a workflow per persona — dynamic composition via `persona-start` covers this without static artifacts
- turning every skill into a persona-aware skill
- encoding persona behavior in Claude-specific agent files
- depending on hidden Codex config internals

## Current Implementation

The repo now includes a local plugin under:

```text
plugins/promptonality/
```

That plugin demonstrates the intended split:

- neutral workflow cores (no persona baked in)
- standalone personality pack files (applied dynamically via `persona-start` or `persona-apply`)
- persona entrypoint skills for session-wide or task-scope composition
- extraction skills for generating new personality material

Current plugin skills:

Persona skills (also exported as standalone):
- `plugins/promptonality/skills/persona-start/SKILL.md`
- `plugins/promptonality/skills/persona-apply/SKILL.md`
- `plugins/promptonality/skills/persona-list/SKILL.md`
- `plugins/promptonality/skills/persona-extract/SKILL.md`
- `plugins/promptonality/skills/persona-extract-online/SKILL.md`

Neutral workflow cores (composed dynamically — no per-persona forks):
- `plugins/promptonality/skills/orchestrator-core/SKILL.md`
- `plugins/promptonality/skills/architecture-review-core/SKILL.md`

Personality assets:
- `plugins/promptonality/assets/personalities/sam-harris.yaml`
- `plugins/promptonality/assets/personalities/bjarne-stroustrup.yaml`
- `plugins/promptonality/assets/personalities/yoda.yaml`

Claude-facing exported skills (standalone, symlinked from `skills/`):

- `skills/persona-start/SKILL.md`
- `skills/persona-apply/SKILL.md`
- `skills/persona-list/SKILL.md`
- `skills/persona-extract/SKILL.md`
- `skills/persona-extract-online/SKILL.md`

Generated Claude plugin package:

- `plugins/promptonality/claude-plugin/plugin.json`
- `plugins/promptonality/claude-plugin/skills/persona-start/SKILL.md`
- `plugins/promptonality/claude-plugin/skills/persona-apply/SKILL.md`
- `plugins/promptonality/claude-plugin/skills/persona-list/SKILL.md`
- `plugins/promptonality/claude-plugin/skills/persona-extract/SKILL.md`
- `plugins/promptonality/claude-plugin/skills/persona-extract-online/SKILL.md`

## Reworking `persona-extract`

The extraction skills should feed the plugin, not sit beside it as disconnected prompt generators.

Target responsibilities:

- generate normalized personality packs
- support fast local generation and research-backed generation
- distinguish one-off prompts from reusable personality assets
- make generated outputs easy to compose with other workflows later

## Personality Pack Contract

The plugin should standardize a reusable pack format.

The contract is documented in:

- `docs/personality-pack-contract.md`

Important fields include:

- `voice`
- `interaction_stance`
- `value_profile`
- `reasoning_style`
- `default_structures`
- `ambiguity_policy`
- `tradeoff_policy`
- `compression_policy`
- `interaction_rules`
- `guardrails`
- `anti_patterns`
- `prompt_overlay`

Interpretation:

- packs are overlays, not whole workflows
- they should add positive cognitive value, not just style
- they must remain bounded by the base workflow’s correctness and task guarantees
- they should not silently override safety or operational competence

## Composition Rule

The composition model is:

- the **base workflow** supplies execution guarantees
- the **personality pack** supplies voice, structure, and reasoning lens
- `persona-start` or `persona-apply` applies the pack dynamically — no dedicated variant skill required

Composition is explicit prompt construction, not a hidden runtime feature. The user names a workflow core and a pack; `persona-start` loads both and governs the session. No static fork of the workflow skill is created or needed.

Dedicated per-persona variant skills are explicitly out of scope. They duplicate the composition mechanism, add maintenance burden, and imply a fork for every workflow-pack pairing. Dynamic application via `persona-start` covers the same ground without static artifacts.

## Why Not Persona Metadata Everywhere

Embedding persona logic into many unrelated skills would:

- duplicate personality logic across files
- make maintenance harder
- blur the line between workflow knowledge and cognitive lens
- make later pluginization more painful

Keeping personality separate is the cleaner long-term model.

## Provenance

This document condenses direction from:

- `plugins/promptonality/skills/persona-extract/SKILL.md`
- `plugins/promptonality/skills/persona-extract-online/SKILL.md`
- repo cleanup work around Codex support
- earlier design material in `up_claude/`
