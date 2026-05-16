# Persona Storage: Problem and Proposed Design

Tracks `personify-5xu`. Goal: a structural storage model for user-created
packs, not the `~/.personify/` + blocklist workaround.

## Audited current model

- Source of truth: `src/assets/personalities/*.yaml` (bundled packs).
- `scripts/package.py` `build_target()` → `clean_dir()` (`shutil.rmtree`) →
  rebuild copies packs into tracked host bundles at
  `<host>/skills/<skill>/references/personality-packs/*.yaml`.
- Runtime discovery is **single-root**: skills and the generated
  `persona_list.py` only look in `references/personality-packs/` relative to
  the skill dir. No user asset-root lookup exists.
- `~/.personify/` split and the blocklist are **not implemented**.
  `package.py doctor()` only emits diagnostic split-brain / cache-drift
  warnings.

### Where the wipe actually bites

Bundled packs are safe (git-tracked, regenerated). The failure is
**user-added** packs: a user can only add one by dropping YAML into the
installed plugin's `references/personality-packs/`, which the host **replaces
wholesale on plugin update/reinstall**. There is no durable, discoverable
location a user pack can live in.

## Requirements (invariants any fix must keep)

From `personality-strategy.md` / `personality-pack-contract.md`:

- Personas are data assets; a valid pack is addable without editing scripts,
  manifests, or skills.
- Validation applies to user packs exactly as to bundled ones.
- No per-persona wrapper skills.
- `src/` stays the platform-neutral source; hosts are generated, not forked.
- Discovery is dynamic where the host allows it.

## Options

### Option 1 — Multi-root discovery + stable user root (recommended)

A user asset root (`$PERSONIFY_HOME`, default `~/.personify/personalities/`)
becomes a **first-class discovery source**, not a blocklist. Skills and
`persona_list.py` discover from *both* the bundled `references/` root and the
user root; bundled stays generated/tracked, user packs live outside anything
the host overwrites and survive every update.

- Pros: smallest structural change that satisfies all invariants; no per-host
  divergence; user packs are first-class and persistent; testable by pointing
  discovery at a fixture root.
- Cons: requires the skill instructions + generated `persona_list.py` to take
  a root list; relies on each host exposing the user filesystem (true for
  Claude/Codex/Gemini CLIs today).
- Why not a blocklist: a blocklist still co-locates user packs with wiped
  content and treats them as second-class — the exact workaround to avoid.

### Option 2 — Persona CRUD surface over the user root

Layer create/list/update/delete on top of Option 1 via the *existing*
entrypoint skills (extend `extract-persona`/`list-persona`s; no new
per-persona skills). Write target becomes `$PERSONIFY_HOME`, not `src/`.

- Pros: complete UX for the asset model; natural home for `personify-50q`
  (schema v1) and `personify-xe5` (community packs).
- Cons: more design surface; depends on Option 1 landing first.
- Position: the follow-on to Option 1, not a competing choice.

### Option 3 — Platform-native data layer per host

Use each host's durable plugin/extension data dir for user packs.

- Pros: most "native"; survives updates by host contract.
- Cons: reintroduces per-host divergence the source model exists to avoid;
  largest cost; defer unless a host forbids arbitrary filesystem roots.

## Recommendation

**Option 1 now, Option 2 next, Option 3 only if forced.** Make multi-root
discovery the structural fix: bundled packs ship generated; user packs live in
a stable `$PERSONIFY_HOME` that no update touches; discovery and validation
treat both roots identically.

### Migration sketch (design only — build deferred)

1. Define `$PERSONIFY_HOME` (default `~/.personify/personalities/`); document
   precedence (user root overrides bundled on id collision, or error — decide
   in schema v1).
2. `scripts/persona_list.py` + its generated variant: accept an ordered root
   list; iterate bundled `references/` then user root.
3. `list-personas` / `use-persona` / `as-persona` SKILL.md: load by id from
   the merged set; never assume a single dir.
4. Contract test: validate every discovered pack from both roots; add a
   fixture user root.
5. No change to `clean_dir`/`build_target` (bundled pipeline stays); user root
   is never built or wiped by `package.py`.

## Doc fix surfaced

`persona-injection.md:38` calls generated host packages "ignored build
outputs"; they are git-tracked (`.gitignore:6`). Fix when landing related work.
