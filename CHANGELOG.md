# Changelog

Versions follow `test/test_manifest.json` → `versioning` (semver pre-1.0:
v0.MINOR.PATCH). The version source of truth is `src/package.json`; generated
host manifests are rebuilt from it with `python3 scripts/package.py build --target all`.

## 0.6.0 — extract-persona v2

New capability class: research-store-backed persona extraction and a layered
pack schema. Design note and research mapping: `docs/extract-persona.md`.

### Added
- `extract-persona` helper `scripts/persona_extract.py` (stdlib, offline, no
  model calls), packaged with the skill for every host:
  - research store per persona under `${XDG_DATA_HOME}/personify/research/<id>/`
    with raw and normalized sources, provenance records (URL, mirrors, type,
    dates, context, attribution, verbatim/paraphrase, rights note) and a manifest
    with history
  - content-hash ids and dedupe, incremental `index`, chunk corpus and a
    speaker-attributed, deduplicated utterance corpus
  - `status` coverage gate, `profile` stylometry (sentence-length
    distribution, rates, discourse markers, openers, cross-source signature
    phrases), `retrieve` BM25 with top-k and token cap
  - `assemble` (analysis JSON + measured profile + corpus → v2 pack, evidence
    checks, layer budgets, priority trimming into the store), `validate`,
    `migrate` (v1 → v2, lossless), `budget`
- Pack schema v2 (`references/persona-pack.schema.json`, validates v1 and v2):
  `core`, `idiolect`, `humor`, `stances`, `under_pressure`, `contradictions`,
  `knowledge_boundaries`, `relationships`, `voice_calibration`,
  `example_utterances` (`shape-not-lines`), `retrieval`, `layers`,
  `provenance.source_records` / `provenance.extraction`.
- `docs/extract-persona.md`; schema v2 section in
  `docs/personality-pack-contract.md`.
- `test/extract_persona_test.py` with fictional fixtures; schema validation of
  bundled packs in `test/personality_pack_contract_test.py`.
- `CHANGELOG.md`.

### Changed
- `extract-persona` skill: long-form and pressure-context source hunt, capture
  into the store, coverage gate, measured profile, depth profile with evidence
  ids, analysis JSON + `assemble` instead of hand-written YAML, update flow.
- `use-persona` / `as-persona`: how to load v2 layers and use per-turn retrieval.
- `test/run-test.sh` runs the new test. (The CI workflow step is not included yet; add `python3 test/extract_persona_test.py` after the `extractor_test.py` line in `.github/workflows/build-artifacts.yml`.)

### Compatibility
- v1 packs are unchanged and still valid. v2 packs keep every v1 field, so
  listing and activation work as before. Bundled packs were not migrated.

## Earlier versions

From `test/test_manifest.json`:

- 0.5.0 — activation benchmark reporting, bundled persona curation, and george-hotz draft pack
- 0.4.0 — yoda style test runner, versioning enforcement hook and CI check
- 0.3.1 — reduce persona repetition traps, block mechanical repetition in contract test
- 0.3.0 — persona activation packet, source workflow repackaging, CI artifact publishing
- 0.2.0 — personify plugin: portable persona source and host package generators
- 0.1.0 — initial Codex-ready skill packaging baseline
