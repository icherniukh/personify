---
name: architecture-review-core
description: Neutral architecture review workflow. Use when evaluating project structure, boundaries, abstractions, dependencies, performance implications, and maintainability risks without applying any specific personality lens.
---

# Architecture Review Core

This is the reusable architecture-review workflow.

It defines how to review a project architecture without binding the review to any specific personality.

## Core Goal

Explain whether the architecture matches the problem being solved, where the main structural risks are, and what changes would improve clarity, maintainability, and operational behavior.

## Review Method

1. Clarify the target:
   What system is being built, for whom, under what constraints, and what matters most.
2. Identify the main architectural units:
   Services, modules, data boundaries, shared libraries, deployment seams, and major ownership lines.
3. Check the abstraction quality:
   Whether the abstractions match the problem, hide the right details, and avoid accidental coupling.
4. Check runtime consequences:
   Performance, resource costs, latency, failure modes, concurrency, and scaling implications.
5. Check changeability:
   How easy it is to test, extend, replace, or migrate major parts of the system.
6. Make recommendations:
   Preserve what is structurally sound, name the sharpest risks, and propose the smallest changes with the highest leverage.

## Required Output Shape

When enough context exists, structure the review as:

- `System Goal`
- `Main Architectural Units`
- `Strengths`
- `Risks`
- `Tradeoffs`
- `Recommended Changes`

If the context is incomplete, ask for the missing architectural inputs before pretending the review is settled.

## Review Standards

- Prefer explanation over slogan
- Separate observed structure from inference
- Name coupling explicitly
- Distinguish local code problems from system-shape problems
- Preserve useful existing structure where possible

## Composition Rule

This skill may be paired with a personality pack stored under:

```text
assets/personalities/<id>.yaml
```

The personality may affect tone, emphasis, and answer structure, but it must not replace the review workflow above.
