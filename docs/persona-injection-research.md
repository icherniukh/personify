# Persona Injection Research

This note records the current decision and remaining research path for making
persona activation more reliable across Codex, Claude, Gemini, OpenCode, and Pi.

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
- OpenCode gets generated skills and command markdown for manual install.
- Pi gets a package manifest and generated skills.

The invariant is the source model under `src/`, not identical output shape.

## Decision

Keep the deterministic Persona Activation Packet as the default activation model.

That means activation should always follow the same sequence:

1. resolve the selected pack,
2. read the pack file,
3. construct the Persona Activation Packet,
4. apply task and project instructions first,
5. apply the persona overlay second,
6. carry or discard active-mode state according to the requested scope.

This is the right default because it preserves Personify's core promise: personas
are data assets, not per-persona wrapper code. It is also the easiest path to
test because the packet can be rendered in fixtures, checked for expected
fields, and compared against neutral or baseline prompts.

## Improvement Track

The next improvement should be evidence-driven, not rhetorical.

Use the activation benchmark with at least three prompt treatments:

1. **Neutral Baseline**
   The task runs with no persona overlay.
2. **Plain Prepend Baseline**
   The task runs with a simple instruction such as "Respond like Sam Harris" or
   "Use the Jesse Pinkman persona" before the user task.
3. **PAP + Self-Check**
   The task runs with the full Personify packet, loaded pack fields, scope, and
   per-reply drift-correction check.

Judge all three on:

- task success
- persona recognizability
- functional delta from neutral
- reasoning or framing delta
- repetition control
- whether the output stays useful after the persona overlay

The plain prepend baseline is allowed to be weak. A weak plain baseline is part
of the measurement, not a reason to fail the run. The strict requirement is that
PAP preserves task quality and earns an overall advantage over plain prepend.

The claim to prove is narrow: PAP plus self-check should hold persona fidelity
and reasoning/style delta better than a plain prepend while preserving task
quality.

Run a smoke version without API calls:

```bash
python3 test/activation_benchmark.py --dry-run --persona sam-harris --case hidden-assumption
```

Run a focused live comparison:

```bash
python3 test/activation_benchmark.py --api openrouter --persona sam-harris --case hidden-assumption --repeats 1
```

Run the full benchmark matrix when release confidence matters:

```bash
python3 test/activation_benchmark.py --api openrouter --persona all --repeats 3
```

By default, live benchmark runs write both machine-readable and human-readable
outputs under the repo-local ignored `benchmark-runs/` directory:

```text
benchmark-runs/<run-id>.jsonl
benchmark-runs/<run-id>.md
```

The markdown report is the human review surface. It records provider, generator
model, judge model, and model-pair name in a run metadata table. Each trial then
uses grouped tables for case details, judge checks, score comparison, validation
status, and neutral / plain prepend / PAP answer comparison. The JSONL file is
kept as the replay/debug log.

OpenRouter model rotation is configured in:

```text
config/activation_benchmark_models.json
```

When `--model`, `--judge-model`, `OPENROUTER_MODEL`, and
`OPENROUTER_JUDGE_MODEL` are not set, the runner rotates to the next configured
OpenRouter pair and stores rotation state under `benchmark-runs/`. Add a new
entry to the config's `openrouter.pairs` list to extend the rotation.

Override the rotation for one run with:

```bash
OPENROUTER_MODEL=moonshotai/kimi-k2.6 \
OPENROUTER_JUDGE_MODEL=x-ai/grok-4.3 \
python3 test/activation_benchmark.py --api openrouter --persona all --repeats 3
```

## Option 1: Deterministic Activation Packet

Generate or specify a compact Persona Activation Packet from the selected YAML
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

Status: selected default.

## Option 2: Host Context Anchors

Use host-specific persistent context surfaces to keep the general Personify
composition rule nearby.

Examples:

- Gemini: strengthen `GEMINI.md` as a persistent extension-level explanation of
  composition behavior.
- Claude: tune plugin skill descriptions and docs for namespaced skill use.
- Codex: tune plugin metadata, commands, and skill descriptions so invocation is
  clearer.
- OpenCode and Pi: keep generated commands explicit about pack resolution,
  packet construction, and scope.

Benefits:

- improves recall of what Personify is
- does not change the asset model
- works alongside option 1

Risks:

- static context cannot dynamically switch the active persona by itself
- host behavior differs and can drift
- context anchors can become stale if they duplicate source docs

Status: implement narrowly where generated packages already have command or
context surfaces.

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

Status: defer until external asset roots or deterministic composition become
painful enough to justify the machinery.

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

Status: reject as the default model. Per-persona wrappers should only exist as
compatibility shims if a host runtime forces that shape.

## Research Sources

- OpenAI Codex skills documentation:
  https://developers.openai.com/codex/skills
- Claude Code plugin documentation:
  https://code.claude.com/docs/en/plugins
- Gemini CLI extension reference:
  https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md
- Gemini `GEMINI.md` documentation:
  https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md
