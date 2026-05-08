# Persona Injection Model

This document explains how `personify` applies a persona today.

## Short Version

`personify` does not install a hidden runtime compiler and does not rewrite the
host system prompt.

It packages skills and commands that tell the assistant to:

1. resolve a persona id,
2. load the matching YAML pack,
3. combine the user's task instructions with that pack,
4. keep the selected pack active for the requested scope.

The result is prompt-level composition. The persona becomes operating context for
the assistant, not a new model, policy layer, or privileged instruction channel.

## Source Layers

The authored source lives in:

```text
src/
```

The important source files are:

```text
src/skills/use-persona/SKILL.md
src/skills/as-persona/SKILL.md
src/skills/list-personas/SKILL.md
src/skills/extract-persona/SKILL.md
src/assets/personalities/*.yaml
```

Generated host packages are ignored build outputs. They are recreated with:

```bash
python3 scripts/package.py build --target all
```

The generated packages copy the same source skills and bundle the current starter
persona packs under runtime-local reference paths such as:

```text
references/personality-packs/
```

## What Gets Injected

A persona pack is a YAML asset. The contract requires sections for:

- identity and summary
- voice
- interaction stance
- value profile
- reasoning style
- preferred terminology
- speech patterns
- default structures
- ambiguity, tradeoff, and compression policies
- interaction rules
- prompt overlay
- provenance and quality level

When a persona is applied, those fields are treated as an overlay on top of the
task. The current test harness models that overlay with two explicit sections:
a compact activation packet and the fuller personality overlay.

```text
<task instructions>

## Persona Activation Packet
Persona id: <id>
Display name: <display_name>
Scope: <task | thread | session>
Strength: strong
Loaded pack: <path>
Voice markers:
- <marker>
Reasoning habits:
- <habit>
Drift correction:
- <reload/restore rule>

## Personality Overlay
Identity: <display_name>
Summary: <summary>
Voice:
...
Overlay prompt:
...
```

That packet is a test representation and composition convention, not a separate
production runtime. It is useful because it makes the intended composition order
explicit: task first, compact persona anchor second, full persona overlay third.

## Session-Wide Activation

`use-persona` is the session bootstrap skill.

When invoked, it tells the assistant to treat the selected pack as the default
voice, stance, and reasoning lens for later nontrivial replies. It also tells
the assistant to keep a compact active-mode state in mind:

- active persona id and loaded pack path
- persona strength
- a few voice markers
- one or two structural habits
- drift-correction rule

This state is conversational state. It depends on the host assistant continuing
to follow the skill's instructions across the session. If the state is lost, the
skill instructs the assistant to reload the pack and restore the active mode.

## One-Off Application

`as-persona` applies a pack to one task or thread.

The default scope is the current task. If the user wants the style to persist
across the session, `use-persona` is the better entrypoint.

## What Personify Cannot Override

Persona packs do not override:

- system or developer instructions
- user instructions that are more specific than the persona mode
- host safety and policy boundaries
- tool permissions
- factual accuracy requirements
- project instructions such as `AGENTS.md`

The persona can change delivery, emphasis, structure, and rhetorical habits. It
cannot make forbidden actions allowed or make false claims acceptable.

## Host Runtime Behavior

The host runtimes package and discover the same concepts differently.

Claude Code plugins discover skills and commands from plugin directories. Claude
also copies installed marketplace plugins into a local plugin cache, so packaged
files should be self-contained and should not rely on paths outside the plugin.

Gemini extensions package context files, commands, and related files into an
installable extension. Personify generates Gemini commands that route requests
to the same persona skills.

Codex plugins expose a plugin manifest, skills, and commands for the Codex
runtime. Personify generates the Codex package from the same source tree rather
than treating Codex as the source of truth.

Because these hosts differ, Personify's invariant is source-level composition,
not identical filesystem layout in every generated package.

## Current Limitations

The main limitation is reliability of carry-forward state. Session-wide persona
activation is only as durable as the host conversation context and the model's
adherence to the loaded skill instructions.

Known improvement areas:

- make pack resolution less dependent on the model inferring file paths
- use the activation packet consistently in generated host commands and tests
- support user-defined asset roots without editing generated packages
- improve generated commands so they pass clearer scope and persona arguments
- add evaluation cases that test whether persona state survives multi-turn work
- document host-specific install/update/cache behavior before public release

## Practical Mental Model

Think of Personify as a structured prompt overlay system with packaging around
it.

It gives the assistant a validated persona asset and explicit instructions for
how to apply it. The host model still decides the next tokens, follows higher
priority instructions first, and remains responsible for doing the task
correctly.
