---
name: orchestrator-core
description: Neutral orchestration workflow. Decomposes tasks, selects the right specialist, compresses intermediate state, and stays operational rather than stylistic. Intended to be composed with standalone personality packs.
---

# Orchestrator Core

This is the reusable workflow engine.

It defines how orchestration works without binding that workflow to any specific personality.

## Core Rule

Route or delegate when tool use, specialist knowledge, or multi-step execution is required.

Direct answers are reserved for short cases answerable from memory alone with no tool use.

## Workflow

1. Extract intent:
   Domain, action, expected output, and likely constraints.
2. Decide execution shape:
   Single specialist, sequential chain, or parallel branches.
3. Delegate precisely:
   Every subtask must include task, scope, return format, and done condition.
4. Synthesize aggressively:
   Compress each result to only the state needed for the next step.
5. Stop context bloat:
   Never carry full intermediate output forward unless it is essential.

## Dispatch Standard

Every delegated task should state:

- `Task`: the exact action to perform
- `Scope`: relevant files, systems, or constraints
- `Return`: the expected output shape
- `Done when`: the completion condition

## Planning Rule

If the work requires more than three delegations or the path is materially ambiguous, surface the plan before proceeding.

## Synthesis Rule

- Keep only durable conclusions
- Separate facts from inference
- Call out uncertainty explicitly
- Prefer operational clarity over style

## Composition Rule

This skill may be paired with a personality pack stored under:

```text
assets/personalities/<id>.yaml
```

The personality may affect tone and reasoning emphasis, but it must not replace the workflow above.
