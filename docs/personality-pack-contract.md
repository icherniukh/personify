# Personality Pack Contract

This document defines the contract for interchangeable persona assets.

## Core Idea

A personality pack is a bounded cognitive lens stored as data.

It is not:

- a full workflow
- a standalone orchestrator
- a replacement for domain logic
- a static installed skill
- a pure style skin with no functional value

Its job is to change how the same underlying workflow frames, structures,
compresses, and communicates work.

The pack itself should stay domain-neutral unless a domain-specific persona is
explicitly the point. Workflow-specific instructions belong in workflow cores or
task-specific instructions, not in reusable persona assets.

## Asset Promise

Packs are user-extensible assets.

The framework should be able to discover, validate, list, package, and compose
any valid pack without adding a new wrapper skill or editing framework code for
that specific persona.

Bundled packs are examples and regression fixtures. User-created packs are
first-class once they satisfy this contract.

## Invariant Layer

These things should stay stable across personalities:

- task completion
- truthfulness
- safety expectations
- operational competence
- tool discipline

The base workflow and host assistant own those guarantees.

## Personality-Variable Layer

These things may vary by personality:

- voice and rhetorical temperature
- framing priorities
- uncertainty handling
- tradeoff exposure
- compression style
- default answer structures
- conversational stance toward ambiguity
- humor, metaphor, and emotional register

This is where personality should add value.

## Composition Model

Composition uses two required layers:

1. **Base workflow**
   Neutral instructions that define how the work gets done.
2. **Personality pack**
   A standalone asset that defines the lens applied to that workflow.

Entrypoint skills such as `persona-start`, `persona-apply`, and `persona-list`
provide the user interface for discovery and composition.

Dedicated per-persona wrapper skills are not required by the model. They should
be treated as compatibility shims or historical examples unless a host runtime
forces that shape.

## No Pack-Level Guardrails

Do not add `guardrails`, `anti_patterns`, or other local restriction sections to
persona packs.

That is intentional. Pack-level guardrails made personas less creative and less
alive. The host model and platform policies already provide the needed
behavioral boundaries; the things previously restricted here were not appearing
in practice. Persona assets should focus on positive expressive material:
voice, stance, reasoning habits, references, cadence, and interaction patterns.

Quality control should happen through evaluation of outputs, not by stuffing the
pack with prohibitions.

## File Location

Within the plugin source, store bundled personality packs under:

```text
src/assets/personalities/<id>.yaml
```

Generated packages may copy those packs into runtime-specific reference
directories, such as:

```text
references/personality-packs/<id>.yaml
```

Future user extension may add additional asset roots. Those roots should use the
same contract.

## Required Fields

```yaml
id: sam-harris
display_name: Sam Harris
summary: Calm, analytic, high-clarity philosophical voice.
voice:
  tone: precise, restrained, serious
  style: low-theatrics, high-clarity
interaction_stance:
  - skeptical but constructive
  - low-affect, high-clarity
value_profile:
  - surfaces hidden assumptions before recommendations
  - separates facts from inference
  - exposes tradeoffs instead of smoothing them over
reasoning_style:
  - state uncertainty plainly
  - reduce ambiguity before proposing action
preferred_terminology:
  - balance
  - discipline
  - fear
  - burden
speech_patterns:
  - uses clipped, high-signal sentences
  - occasionally inverts sentence order for emphasis
default_structures:
  - observations / assumptions / next steps
  - facts / inferences / open questions
ambiguity_policy: |
  Treat ambiguity as something to map explicitly rather than blur past.
tradeoff_policy: |
  State the real tradeoff directly instead of presenting a flattened consensus answer.
compression_policy: |
  Compress by preserving the decisive distinctions, not by flattening them.
interaction_rules:
  - prefer careful decomposition
  - expose the reasoning structure before recommendations
  - use compact analytic phrasing when the task benefits from it
prompt_overlay: |
  Short reusable overlay text applied after the base workflow.
provenance:
  source_type: curated
  notes: First-pass local pack
quality_level: draft
```

## Field Semantics

- `id`: Stable machine-readable identifier. It should match the filename stem.
- `display_name`: User-facing label.
- `summary`: One-line explanation of the pack.
- `voice`: Surface communication qualities.
- `interaction_stance`: The interpersonal stance the pack should take.
- `value_profile`: The positive reasoning and presentation value this lens adds.
- `reasoning_style`: Cognitive habits the pack should bias toward.
- `preferred_terminology`: Terms, metaphors, and vocabulary to use when natural.
- `speech_patterns`: Signature syntax, cadence, and sentence-shape cues.
- `default_structures`: Answer shapes the pack should prefer when they fit.
- `ambiguity_policy`: How the pack behaves when evidence is incomplete or mixed.
- `tradeoff_policy`: How the pack exposes competing considerations.
- `compression_policy`: What should survive summarization.
- `interaction_rules`: Positive response behavior rules and characteristic moves.
- `prompt_overlay`: Composable prompt text layered after the base workflow.
- `provenance`: Where the pack came from and how trustworthy it is.
- `quality_level`: Draft, reviewed, or research-backed maturity marker.

## Validation Rules

Validators should operate over every discovered pack, not over a hardcoded list
of built-in personas.

Minimum validation should check:

- required fields exist
- required list sections are non-empty
- required block sections are non-empty
- `id` is unique within the active asset set
- `id` matches the filename stem
- `quality_level` uses an allowed maturity marker
- YAML parses cleanly
- generated package copies match source packs

## Design Rule

The pack should add positive value, not constraints.

Good personality packs say:

- what kinds of distinctions this personality surfaces
- what kinds of structure it prefers
- what kinds of syntax and cadence make it sound unmistakably like itself
- what becomes clearer when this lens is applied
- what it reaches for under pressure
- how it varies emphasis, rhythm, and references

When tuning a distinctive voice, prefer this direction:

- make the personality clearly recognizable first
- then trim only the parts that reduce clarity, correctness, or task usefulness

Do not start from fear of overexpression. Do not encode creativity-killing
restrictions in the pack just because a failure is imaginable.

## Runtime Assumption

This contract is a repo-level convention first.

Current Codex support in this repo should treat personality composition as
explicit packaging and prompt construction, not as a hidden runtime feature.
Entrypoint skills should point at discovered packs and compose them with the
requested workflow or task.
