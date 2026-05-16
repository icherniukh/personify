# Persona Injection: Effectiveness and Proposed Design

Tracks `personify-671`. This proposes a better injection design and an
experiment to prove it, building on `persona-injection.md` (current model) and
`persona-injection-research.md` (mechanism options).

## 1. personify vs a raw system prompt

Prepending "act like X" to a system prompt is a one-shot string. personify is a
composition system around a validated asset. Concrete differences:

| Dimension | Raw system-prompt prepend | personify |
|---|---|---|
| Source | Ad hoc free text | Contract-validated YAML asset (`personality-pack-contract.md`) |
| Structure | Unstructured | Task → compact Activation Packet → full overlay, fixed order |
| Scope | Whole session, implicit | Explicit: task / thread / session |
| Recovery | None — drifts to neutral silently | Drift-correction rule: reload pack, restore markers |
| Provenance | None | `provenance` + `quality_level`, source-grounded |
| Portability | Per-host copy/paste | One source, generated for Claude/Codex/Gemini |
| Boundaries | Implicit | Explicit "cannot override" list (safety, AGENTS.md, facts) |

The thesis to validate: the *structured composition*, not the persona text
alone, is what produces a reliable functional delta. Section 4 tests this.

## 2. Per-platform injection map (how and when)

Source: `src/skills/*/SKILL.md` + `src/assets/personalities/*.yaml`, generated
by `scripts/package.py` / `scripts/export_*.py` into tracked host packages.

| Host | Entry surface | When persona is injected | Pack read from |
|---|---|---|---|
| Claude | Plugin skill (`use-persona`/`as-persona`) | On skill invocation; session-scoped for `use-persona` | `<skill>/references/personality-packs/<id>.yaml` |
| Codex | Plugin skill + generated command md | Command routes to skill; same load step | same, relative to skill dir |
| Gemini | Extension command + `GEMINI.md` anchor | Command routes to skill; `GEMINI.md` keeps composition rule resident | same, relative to skill dir |

Common path: resolve id → read YAML → compose (task first, packet second,
overlay third) → hold compact active-mode state for the scope.

## 3. Proposed design — Resolved Activation Packet

Current weaknesses (`persona-injection.md:159-172`): activation depends on the
model (a) inferring/re-reading a file path mid-session and (b) holding
carry-forward state that silently decays in long contexts.

Proposal, in priority order, all asset-first and host-neutral:

1. **Resolve-then-inline.** At activation, the skill renders the packet with
   pack content *inlined* (voice markers, reasoning habits, overlay) so no
   later file re-read is required. The file path stays only as a re-anchor
   pointer, not the live dependency.
2. **Machine-checkable packet schema.** Freeze the Activation Packet field set
   and order; add a contract/behavior assertion so generated host commands and
   tests render the identical shape (extends `personality_pack_contract_test`).
3. **Explicit re-anchor protocol.** Define a turn-level rule: before a
   nontrivial reply, if active-mode markers are not in working context,
   re-emit the resolved packet. This replaces "hope the model remembers."
4. **Composition-rule host anchor (narrow).** Per host, keep only the
   *composition rule* resident (Gemini `GEMINI.md`, Claude skill description,
   Codex metadata) — never persona content — so the host recalls *how* to
   compose without per-persona artifacts.
5. **Defer MCP/sidecar.** Justified only when user-defined asset roots
   (`personify-5xu`) or deterministic parsing demand it; decision criteria:
   external roots shipped AND model-side resolution proven unreliable in §4.

Explicitly rejected: per-persona wrapper skills (violates the asset-first
invariant; see `personality-strategy.md:154`).

## 4. Effectiveness experiment (proof, not assertion)

Extend the existing harness to a **3-arm** comparison instead of 2:

- **A — neutral**: `load_neutral_packet()` (task only).
- **B — naive prepend**: new `packet_builder.load_naive_prepend_packet(pack)`
  ("You are <display_name>. Respond as them." + raw pack dump, no structured
  composition).
- **C — Resolved Activation Packet**: `build_instruction_packet()`.

Reuse `sam_style_test.py`'s judge scaffold (do not mutate the green smoke
test — clone to `test/injection_effectiveness_test.py`). Judge scores A/B/C on
task success, functional delta, recognizability, reasoning delta over
`sam_cases.json` (+ `yoda_cases.json`). Supports `--dry-run` with no API key.

**Hypothesis / pass bar:** C ≥ B on functional + reasoning delta with equal
task success, and C materially > B on at least one. If B ≈ C, the structure
adds no value and the design should simplify toward the prepend. Prior signal:
`personify-1bv` reasoning-delta judge moved 4→5 with structured Sam.

## 5. Doc fix surfaced

`persona-injection.md:38` says generated host packages are "ignored build
outputs" — they are git-tracked (`.gitignore:6`). Correct that line when
landing this work.
