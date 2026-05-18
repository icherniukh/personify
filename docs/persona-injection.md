# Persona Injection Model

This document explains how `personify` activates a persona today.

## Short Version

`personify` does not install a hidden runtime compiler and does not rewrite the
host system prompt.

It packages skills and commands that tell the assistant to:

1. resolve a persona id,
2. load the matching YAML pack,
3. construct a Persona Activation Packet,
4. combine the user's task instructions with that pack,
5. keep the selected pack active for the requested scope.

The result is prompt-level composition. The persona becomes operating context for
the assistant, not a new model, policy layer, or privileged instruction channel.

## Activation Lifecycle

Activation is an instruction sequence, not a hidden runtime switch.

1. **Trigger:** the user invokes `use-persona`, `as-persona`, or a generated host
   command that routes to one of those skills.
2. **Resolve:** the assistant finds the requested pack by id or close name using
   bundled packs first, then user-owned overrides.
3. **Load:** the assistant reads the resolved YAML file. If the file is not read,
   the persona is not fully active.
4. **Render anchor:** the assistant builds a compact Persona Activation Packet
   with the id, display name, scope, strength, pack path, voice markers, reasoning
   habits, and drift-correction rule.
5. **Compose:** task and project instructions stay first. The persona overlay is
   applied after those instructions and cannot override higher-priority rules.
6. **Carry:** for `session` or `thread` scope, the assistant keeps the compact
   active-mode state in host conversation context.
7. **Recover:** if the persona state fades or becomes generic, the assistant
   reloads the resolved pack and reconstructs the activation packet before the
   next substantive answer.

Activation is not storage. The host conversation state is the storage mechanism,
and the loaded pack plus activation packet are the recovery mechanism.

## Scope Semantics

`as-persona` defaults to `task` scope. It applies the selected pack to the current
answer or immediate task and does not imply future turns should keep using it.

`as-persona` may also be used for `thread` scope when the user asks for a persona
to shape a short local exchange without becoming the session default.

`use-persona` defaults to `session` scope. It makes the selected pack the default
voice, stance, and reasoning lens until the user switches personas, asks for
neutral mode, or the session ends.

All scopes use the same composition order:

```text
task and project instructions
Persona Activation Packet
full personality overlay from the loaded pack
```

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

## Difference From A System Prompt Prepend

A plain system-prompt prepend is one block of text placed before the task. It is
usually always-on, hard to inspect after the fact, and often blurs persona style,
task instructions, and persistence rules into one paragraph.

Personify is different in four concrete ways:

- **Lazy activation:** persona content is loaded only when the user asks for a
  persona. Listing packs does not activate them.
- **Structured assets:** the source of behavior is a YAML pack with typed fields,
  not an unstructured paragraph.
- **Explicit scope:** `task`, `thread`, and `session` activation have different
  persistence expectations.
- **Drift correction:** the skills require a private per-reply check and pack
  reload path when the output becomes generic.

This does not make Personify a higher-priority instruction channel. It makes the
prompt overlay easier to compose, test, and debug.

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

## Host Matrix

| Host | Generated surface | Activation behavior |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json`, skills, commands | Commands route to source-derived skills; skills load packs and construct the Persona Activation Packet. |
| Claude Code | `.claude-plugin/plugin.json`, marketplace metadata, skills | Plugin skills carry the same activation lifecycle and bundled reference packs. |
| Gemini CLI | `gemini-extension.json`, `GEMINI.md`, commands, skills | `GEMINI.md` keeps the composition model nearby; commands route to the same skills. |
| OpenCode | skills and commands under `opencode/` | Manual install copies generated skills and command adapters. |
| Pi | package manifest and skills under `pi/` | Package manifest points at generated Personify skills. |

Because these hosts differ, Personify's invariant is source-level composition,
not identical filesystem layout in every generated package.

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

## Debugging Activation

When a persona appears weak or missing, check these in order:

1. Was the correct entrypoint used: `use-persona` for session scope or
   `as-persona` for task/thread scope?
2. Did the assistant read the resolved pack file?
3. Did a user-owned pack override the bundled pack?
4. Was the pack hidden by `${XDG_CONFIG_HOME:-~/.config}/personify/hidden.yaml`?
5. Did the response preserve task/project instructions before applying the
   persona overlay?
6. Did the response use at least one concrete voice marker and one reasoning or
   structure habit from the pack?
7. If the session is long, did the assistant reload the pack and reconstruct the
   activation packet before continuing?

If the answer is still generic, the next improvement should be measured against
a neutral baseline and a plain persona-prepend baseline. Do not claim the
activation mechanism is better without output evidence.

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
- benchmark PAP plus self-check against a plain persona-prepend baseline
- document host-specific install/update/cache behavior before public release

## Practical Mental Model

Think of Personify as a structured prompt overlay system with packaging around
it.

It gives the assistant a validated persona asset and explicit instructions for
how to apply it. The host model still decides the next tokens, follows higher
priority instructions first, and remains responsible for doing the task
correctly.
