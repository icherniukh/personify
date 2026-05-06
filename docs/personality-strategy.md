# Personality Strategy

This document defines the product promise for `promptonality`.

## Core Promise

`promptonality` is not a catalog of famous-persona skills.

It is a framework for treating personas as portable assets that can be created,
updated, validated, packaged, and composed with many workflows.

The bundled personas are starter assets and regression fixtures. They prove the
asset format and the composition path. They are not the boundary of the system.
The normal user path should be:

1. Start with bundled example packs.
2. Add or generate private persona packs.
3. Update those packs over time.
4. Compose any valid pack with a compatible workflow.
5. Keep generated install surfaces in sync without hand-maintaining forks.

If the framework requires code changes or a new wrapper skill for every persona,
the framework has failed its own promise.

## Fundamental Guarantees

The project should make these things true:

- A persona is a data asset, not a hardcoded behavior branch.
- A valid persona pack can be added without editing test scripts, manifests, or
  workflow skills.
- Pack discovery is dynamic wherever the host runtime allows it.
- Pack validation applies to every discovered pack, including user-created packs.
- Built-in packs are examples, not special cases.
- Workflows and persona packs evolve independently.
- Generated Claude, Codex, and Gemini surfaces are derived outputs, not authored
  forks.
- Composition is explicit: base workflow first, persona asset second.
- Host model and platform boundaries remain outside the persona asset.
- Persona assets do not carry local guardrail or restriction sections.

The strategic question is not "which personas are bundled?" It is "can this
system reliably carry any well-formed persona asset through discovery,
composition, evaluation, and packaging?"

## Why a Plugin

Personality is cross-cutting:

- it can apply to many domains
- it is not the same thing as workflow logic
- it benefits from shared assets, validation, generators, and packaging
- users need a place to store and evolve their own packs

A separate plugin keeps domain skills focused on execution while giving persona
assets a coherent home.

## Persona Assets

A persona pack is a bounded cognitive lens. It should influence how a workflow:

- frames the problem
- exposes assumptions
- handles ambiguity
- reveals tradeoffs
- compresses information
- chooses answer structures
- speaks and interacts with the user

A pack is not:

- a full workflow
- a replacement for domain logic
- a static installed skill
- a one-off prompt fragment with no schema
- a bundled-only product feature
- a restriction list

Reusable packs should stay workflow-agnostic unless the persona is intentionally
domain-specific. Domain instructions belong in workflow cores or task-specific
instructions, not in general persona assets.

Pack-level guardrails were intentionally removed. They made personas less
creative, and the host model already supplies the necessary behavioral
boundaries. The framework should enforce quality by validating structure and
evaluating actual outputs, not by adding local restriction sections to every
pack.

## Asset Lifecycle

The framework should support this lifecycle:

1. **Create**
   Generate or write a pack using the personality-pack contract.
2. **Store**
   Keep packs in an asset directory with stable ids and provenance.
3. **Validate**
   Check every pack against the contract, not a hardcoded allowlist.
4. **Discover**
   List available packs from the active asset roots.
5. **Compose**
   Apply a selected pack to a workflow or task.
6. **Evaluate**
   Test whether the pack changes reasoning, framing, and voice in useful ways.
7. **Iterate**
   Update the pack as a living asset without rebuilding the framework.
8. **Package**
   Export generated surfaces from source assets.

This lifecycle is the project. The bundled pack list is just seed data.

## Invariant vs Variable Layers

### Host Layer

These are not encoded inside persona packs:

- task completion
- truthfulness
- platform policy boundaries
- operational competence
- tool discipline

The base workflow and host assistant own these guarantees. Persona packs should
not restate them as local restriction sections.

### Variable

These are allowed to change by persona:

- voice
- framing priorities
- uncertainty style
- tradeoff style
- compression style
- answer structure
- interaction stance
- emotional temperature
- rhetorical habits

Visible style is a feature when the user asks for it. The target is recognizable
voice plus recognizable framing, still inside correctness and safety bounds.

## Composition Model

Composition has two required layers:

1. **Base workflow**
   The neutral task or workflow instructions that define how work gets done.
2. **Persona asset**
   A valid pack that defines voice, structure, and reasoning lens.

Entrypoint skills such as `persona-start`, `persona-apply`, and `persona-list`
provide the user interface for discovery and composition. They should load packs
from asset roots and should not assume the only valid packs are bundled ones.

Dedicated per-persona wrapper skills are out of scope by default. They duplicate
the asset model, create maintenance load, and imply that every workflow-pack
pairing needs a new installed artifact.

## Discovery Model

The intended discovery model is asset-root based.

Current repo source:

```text
plugins/promptonality/src/assets/personalities/
```

Generated packages may bundle those packs under runtime-specific reference
directories, such as:

```text
references/personality-packs/
```

Future user extension should allow additional local asset roots without editing
the plugin source. The exact host-specific mechanism can vary, but the project
promise should stay stable: users can bring their own packs, and the framework
treats them as first-class assets once discovered and validated.

## Relationship to Host Runtimes

Codex, Claude, and Gemini have different packaging mechanics. `promptonality`
should not pretend they are identical.

The repo-owned source of truth is the platform-neutral source tree:

```text
plugins/promptonality/src/
```

Generated compatibility surfaces are derived from that source:

```bash
python3 plugins/promptonality/scripts/package.py build --target all
```

Generated outputs may have different shapes, but they should preserve the same
conceptual system:

- persona assets are data
- entrypoint skills discover and load assets
- workflows remain separate
- generated packages are checked for drift

## Current Implementation

The repo includes a local plugin under:

```text
plugins/promptonality/
```

Active source skills:

- `plugins/promptonality/src/skills/persona-start/SKILL.md`
- `plugins/promptonality/src/skills/persona-apply/SKILL.md`
- `plugins/promptonality/src/skills/persona-list/SKILL.md`
- `plugins/promptonality/src/skills/persona-extract/SKILL.md`
- `plugins/promptonality/src/skills/persona-extract-online/SKILL.md`
- `plugins/promptonality/src/skills/orchestrator-core/SKILL.md`
- `plugins/promptonality/src/skills/architecture-review-core/SKILL.md`

Source asset root:

- `plugins/promptonality/src/assets/personalities/`

The files in that directory are bundled starter packs. They should be discovered
as a collection, not enumerated manually in docs or tests.

## Reworking Extraction

The extraction skills should feed the asset lifecycle.

Target responsibilities:

- generate normalized packs
- support fast local generation and research-backed generation
- distinguish one-off prompts from reusable persona assets
- write outputs in the contract shape
- make generated packs easy to add to an asset root
- preserve provenance so later evaluation knows what kind of pack it is judging

## Validation And Testing

Tests should enforce the framework promise, not just protect the current bundled
catalog.

Validation should:

- scan every pack in the active source asset root
- check required fields and non-empty sections
- reject duplicate ids
- reject malformed YAML
- verify generated packages contain the expected derived pack files
- avoid hardcoded per-pack required-field blocks
- reject reintroduction of pack-level `guardrails` or `anti_patterns` sections

Evaluation should:

- run representative prompts across selected packs and neutral baselines
- distinguish recognizability from integration quality
- detect catchphrase spam, shallow mimicry, and template reuse
- measure whether the persona changes framing and reasoning priorities
- support both bundled examples and user-created packs

The first-class test question is: "does a valid asset compose correctly and
remain useful?" Not: "did these four built-in personas pass?"

Detailed evaluation guidance lives in:

- `docs/persona-evaluation.md`

## What Is Out Of Scope

- Treating bundled personas as the product boundary.
- Requiring a static wrapper skill for every persona.
- Turning every skill into a persona-aware skill.
- Encoding persona behavior in unrelated agents.
- Depending on undocumented host runtime internals as the only extension point.
- Hand-maintaining generated package contents.

## Provenance

This document replaces the older catalog-centered framing with an asset-centered
framework promise. It keeps the earlier separation of workflow and persona logic,
but makes user extension and living persona assets the center of the project.
