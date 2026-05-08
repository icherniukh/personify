# Persona Injection Research

This note records the current design options for making persona activation more
reliable across Codex, Claude, and Gemini.

## Current State

Personify currently uses prompt-level composition.

`use-persona` loads a selected pack and tells the assistant to keep a compact
active-mode state in conversational memory. `as-persona` uses the same pack
loading model but scopes it to the current task or thread.

The repo already states the main limitation: this is explicit prompt
construction, not a hidden runtime compiler or compiled persona object.

Generated packages preserve the same source model but differ by host:

- Codex gets `.codex-plugin/plugin.json`, skills, and generated command
  markdown.
- Claude gets `.claude-plugin/plugin.json`, a marketplace manifest, and skills.
- Gemini gets `gemini-extension.json`, `GEMINI.md`, commands, and skills.

The invariant is the source model under `src/`, not identical output shape.

## Option 1: Deterministic Activation Packet

Generate or specify a compact "Persona Activation Packet" from the selected YAML
pack:

- identity
- source pack path
- three to five voice markers
- one or two reasoning habits
- scope: task, thread, or session
- drift-correction rule
- prompt overlay

Then make `use-persona` and `as-persona` tell the host to render and apply that
packet consistently.

Benefits:

- lowest implementation risk
- host-neutral
- keeps personas as data assets
- avoids per-persona wrapper skills
- easy to test with packet-based fixtures

Risks:

- still depends on model compliance
- session-wide state can drift in long contexts
- user-defined external asset roots remain awkward

Recommendation: implement first.

## Option 2: Host Context Anchors

Use host-specific persistent context surfaces to keep the general Personify
composition rule nearby.

Examples:

- Gemini: strengthen `GEMINI.md` as a persistent extension-level explanation of
  composition behavior.
- Claude: tune plugin skill descriptions and docs for namespaced skill use.
- Codex: tune plugin metadata, commands, and skill descriptions so invocation is
  clearer.

Benefits:

- improves recall of what Personify is
- does not change the asset model
- works alongside option 1

Risks:

- static context cannot dynamically switch the active persona by itself
- host behavior differs and can drift
- context anchors can become stale if they duplicate source docs

Recommendation: implement narrowly after option 1.

## Option 3: MCP Or Sidecar Composer

Ship a small tool or MCP server that lists packs, validates them, and returns a
rendered activation packet for a selected persona.

Benefits:

- deterministic parsing
- better multi-root discovery
- better future support for user-owned asset roots
- easier to expose exact packet contents for debugging

Risks:

- more install complexity
- adds tool-call overhead to a path that should feel lightweight
- still cannot silently rewrite every future turn unless the host exposes a
  reliable session-state API

Recommendation: defer until external asset roots or deterministic composition
become painful enough to justify the machinery.

## Option 4: Generated Per-Persona Skills

Generate one skill per pack, such as `use-yoda` or `use-sam-harris`.

Benefits:

- strongest trigger reliability
- easy for host runtimes to discover

Risks:

- violates Personify's asset-first promise
- turns every new persona into a generated wrapper artifact
- creates drift and host-specific bloat
- makes bundled personas look like the product boundary

Recommendation: do not use this as the default model.

## Near-Term Plan

1. Define a Persona Activation Packet format in the docs and tests.
2. Update `use-persona` and `as-persona` to name that packet explicitly.
3. Update packet tests so rich pack fields are either composed or deliberately
   excluded.
4. Strengthen Gemini `GEMINI.md` and generated command prompts as host context
   anchors.
5. Re-evaluate MCP only after user-defined asset roots are designed.

## Research Sources

- OpenAI Codex skills documentation:
  https://developers.openai.com/codex/skills
- Claude Code plugin documentation:
  https://code.claude.com/docs/en/plugins
- Gemini CLI extension reference:
  https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md
- Gemini `GEMINI.md` documentation:
  https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md
