# Personality Pack Contract

This document defines the repo’s contract for interchangeable personality packs in Codex-oriented plugin packaging.

## Core Idea

A personality pack is a bounded cognitive lens.

It is not:

- a full workflow
- a standalone orchestrator
- a replacement for domain logic
- a pure style skin with no functional value

Its job is to change how the same underlying workflow frames, structures, compresses, and communicates work.

The pack itself should stay domain-neutral unless a domain-specific persona is explicitly the point. Workflow-specific instructions belong in the workflow or variant skill, not in the reusable pack.

## Invariant Layer

These things should stay stable across personalities:

- task completion
- truthfulness
- safety expectations
- operational competence
- tool discipline

The base workflow owns those guarantees.

## Personality-Variable Layer

These things are allowed to vary by personality:

- voice and rhetorical temperature
- framing priorities
- uncertainty handling
- tradeoff exposure
- compression style
- default answer structures
- conversational stance toward ambiguity

This is where personality should add value.

## Composition Model

Composition uses three layers:

1. **Base workflow**
   A neutral skill that defines how the work gets done.
2. **Personality pack**
   A standalone file that defines the lens applied to that workflow.
3. **Variant skill**
   A skill that declares: base workflow + chosen personality pack. In the current implementation, this may be represented as a thin wrapper.

An optional fourth layer is allowed:

4. **Session-start skill**
   A skill that declares that a workflow, variant, or workflow-plus-pack pairing should become the default operating mode for the rest of the session unless the user overrides it.

If a personality conflicts with correctness, safety, or task completion, the base workflow wins.

## File Location

Within a plugin, store personality packs under:

```text
assets/personalities/<id>.yaml
```

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
  - do not pad
  - prefer careful decomposition over slogans
guardrails:
  - usefulness over imitation
  - correctness overrides persona flavor
anti_patterns:
  - smugness
  - faux profundity
prompt_overlay: |
  Short reusable overlay text applied after the base workflow.
provenance:
  source_type: curated
  notes: First-pass local pack
quality_level: draft
```

## Field Semantics

- `id`: Stable machine-readable identifier.
- `display_name`: User-facing label.
- `summary`: One-line explanation of the pack.
- `voice`: Surface communication qualities.
- `interaction_stance`: The interpersonal stance the pack should take toward the user and the problem.
- `value_profile`: The positive reasoning and presentation value this personality should add.
- `reasoning_style`: Cognitive habits the pack should bias toward.
- `preferred_terminology`: Terms, metaphors, and vocabulary the pack should preferentially use when they fit naturally.
- `speech_patterns`: Signature syntax, cadence, and sentence-shape cues that make the surface voice recognizably belong to this personality.
- `default_structures`: Answer shapes the pack should prefer when they fit the task.
- `ambiguity_policy`: How the pack should behave when evidence is incomplete or mixed.
- `tradeoff_policy`: How the pack should expose tradeoffs and competing considerations.
- `compression_policy`: What should survive summarization and what should be stripped away.
- `interaction_rules`: Concrete response behavior rules.
- `guardrails`: Limits that keep the pack useful.
- `anti_patterns`: Failure modes to avoid.
- `prompt_overlay`: Composable prompt text, written to layer on top of a base workflow.
- `provenance`: Where the pack came from and how trustworthy it is.
- `quality_level`: Draft, reviewed, or research-backed maturity marker.

## Design Rule

The pack should add positive value, not just constraints.

Good personality packs do not merely say:

- do not be theatrical
- do not break usefulness
- do not overdo the persona

They also say:

- what kinds of distinctions this personality surfaces
- what kinds of structure it prefers
- what kinds of syntax and cadence make it sound unmistakably like itself
- what becomes clearer when this lens is applied

When tuning a distinctive voice, prefer this direction:

- make the personality clearly recognizable first
- then trim only the parts that reduce clarity, correctness, or task usefulness

Do not start from fear of overexpression and flatten the pack into generic competence.

## Runtime Assumption

This contract is a repo-level convention first.

Current Codex support in this repo should treat personality composition as explicit packaging and prompt construction, not as a hidden runtime feature. Variant skills should point at the pack they compose with, rather than embedding the whole persona inline.
