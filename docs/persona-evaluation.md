# Persona Evaluation

This document defines how `promptonality` should decide whether a persona asset
is good, useful, non-repetitive, and faithful to its intended source.

## Core Question

A good persona is not just recognizable.

It must make the response functionally better or meaningfully different while
remaining useful, accurate, and controlled.

The evaluation question is:

> Does this persona asset change framing, reasoning, structure, and voice in a
> way that is useful, non-mechanical, and supported by its source evidence?

## Evaluation Layers

Use five layers. A pack can pass one layer and fail another.

### 1. Contract Validity

The pack must be a well-formed asset:

- valid YAML
- unique `id`
- filename matches `id`
- required fields exist
- list sections are non-empty
- block sections are non-empty
- provenance is present
- `quality_level` is valid

This is a hard gate. If the pack fails this, do not evaluate style or behavior.

### 2. Source Grounding

For research-backed or public-figure packs, the pack must explain where its
claims come from.

Evaluate:

- direct quotes or concrete references support the claimed voice markers
- inferred traits are labeled as inference
- source material supports cadence, vocabulary, values, and interaction stance
- the pack avoids unsupported biography roleplay
- controversy or unsafe source behavior is bounded rather than copied

This answers: "does the pack match the actual persona it claims to model?"

### 3. Functional Delta

The persona must change more than wording.

Compare persona output against a neutral baseline on the same prompt. Score
whether the persona changes:

- what facts are considered decisive
- what assumptions are surfaced
- what risks are noticed
- how tradeoffs are framed
- what recommendation is chosen
- what order information appears in
- what gets compressed or expanded

If the neutral and persona answers make the same points in the same order with
different slang, the persona failed this layer.

### 4. Style Quality

The persona must sound recognizably like the target without becoming a gimmick.

Evaluate:

- cadence and sentence shape
- vocabulary and signature terms
- emotional temperature
- humor, metaphor, and rhetorical habits
- interaction stance toward the user
- whether style is integrated into substance

The target is recognizable voice plus usable work. Not a faint accent. Not a
catchphrase costume.

### 5. Repetition And Control

The persona must avoid mechanical reuse through expressive variety, not through
pack-level restriction lists.

Track:

- repeated catchphrases
- repeated openings and closings
- repeated metaphors
- repeated sentence shapes
- repeated source references
- excessive profanity or signature wording
- template reuse across unrelated prompts

Repetition is not automatically bad. A signature phrase can be part of a persona.
The failure is when the phrase appears because the system has no other move.

Do not fix repetition by adding `guardrails`, `anti_patterns`, or other local
restriction sections to the pack. Those sections were removed on purpose because
they made personas less creative. The model and host platform are already
restricted enough for the relevant behavioral boundaries. Evaluate outputs and
improve the positive persona material instead.

## Scoring Rubric

Use a 1-5 score per layer.

- `1`: failed, distracting, unsupported, or harmful
- `2`: weak, shallow, or inconsistent
- `3`: acceptable but not strong
- `4`: strong, useful, clearly intentional
- `5`: excellent, distinctive, functional, and controlled

Recommended pass rule:

- contract validity must pass
- source grounding must be at least 3 for research-backed packs
- functional delta must be at least 3
- style quality must be at least 4 when the user explicitly requests a persona
- repetition/control must be at least 3

## Expected Signals

A good result should show:

- the persona notices something the neutral answer did not
- the answer structure changes for a reason
- the voice is recognizable from the first lines
- signature language appears only when earned
- the response still completes the user task
- a judge can point to source-backed traits in the output
- repetition is controlled through varied positive moves, not restriction text

A bad result often shows:

- neutral answer with slang sprinkled on top
- the same catchphrase in every response
- generic confidence without persona-specific judgment
- source references used as decoration
- excessive roleplay that harms task completion
- flattening into generic assistant voice under pressure

## Enforcement Strategy

Use layered enforcement.

### Static Checks

Run on every pack:

- contract validation
- duplicate id detection
- filename/id match
- required source/provenance fields
- absence of pack-level `guardrails` and `anti_patterns`

### Packet Checks

Build composed instruction packets for selected workflow-pack pairs and verify:

- workflow guarantees remain present
- persona overlay is present
- pack-level guardrails and anti-patterns are absent
- no workflow-specific language leaks into general packs unless intended

### Model-Based Evaluation

Run fixed prompt suites through:

- neutral baseline
- persona output
- evaluator/judge prompt

Judge dimensions:

- task success
- functional delta
- persona recognizability
- source-grounded match
- repetition/control
- usefulness after persona overlay

### Longitudinal Review

Sample outputs over time and track:

- phrase frequency
- repeated references
- sentence-shape variety
- response-opening variety
- whether corrections from the user modulate behavior
- whether the persona drifts toward neutral assistant voice

This catches the failures a one-shot test misses.

## Verifying Actual Persona Match

For public figures or characters, do not judge from vibes alone.

Use an evidence file or provenance block with:

- direct quotes
- interview excerpts
- recurring phrases
- documented values
- known speech patterns
- characteristic behavioral patterns and expressive range

Then ask the evaluator:

- which output traits are directly supported?
- which traits are inferred?
- which traits are unsupported?
- what source-backed behavior is missing?
- what behavior is overused or caricatured?

The pack should improve by tightening this loop: source evidence, pack claims,
generated output, judged mismatch, pack revision.

## Product Promise

The framework should make persona quality observable and enforceable.

Users should be able to add a pack and answer:

- Is it valid?
- Does it sound right?
- Is it useful?
- Does it change the reasoning?
- Is it repetitive?
- Is it supported by source evidence?
- What should be edited next?

That is the evaluation bar.
