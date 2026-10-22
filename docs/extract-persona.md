# extract-persona v2: research store, measured voice, layered packs

Version: 0.6.0. Skill: `src/skills/extract-persona/SKILL.md`. Helper:
`src/skills/extract-persona/scripts/persona_extract.py` (stdlib, offline).
Schema: `src/skills/extract-persona/references/persona-pack.schema.json`.
Tests: `test/extract_persona_test.py` with fixtures in `test/fixtures/extract_persona/`.

## Before (0.5.0)

`extract-persona` was a prompt-only skill. The agent ran a few searches, fetched
the "most promising 2-3 URLs", wrote analysis in the conversation, and emitted
one flat YAML pack (the v1 contract fields plus a `provenance.sources` URL
list). Nothing it read was kept: the fetched text, the quotes and the analysis
existed only in the chat. Packs had no token plan, no machine-checkable link
between a claim and its evidence, and no schema beyond the line-based contract
test.

## Now (0.6.0)

Three products, kept apart:

| Product | Where | Purpose |
| --- | --- | --- |
| Research store | `${XDG_DATA_HOME:-~/.local/share}/personify/research/<id>/` | Everything collected, so later retrieval, re-extraction and pack updates never refetch |
| Measured profile | `<store>/profile/stylometry.json` | Sentence-building numbers and signature-phrase candidates from the subject's own lines |
| Pack (schema v2) | `${XDG_DATA_HOME:-~/.local/share}/personify/personas/<id>.yaml` | Layered, token-budgeted lens with evidence ids into the store |

### Collection

- More and longer sources: the skill asks for 6-12 sources and several thousand
  words of the subject's own speech, including long-form transcripts and at
  least one pressure or conflict context.
- Each source is recorded with URL, mirrors (`alt_urls`), title, type
  (transcript, interview, podcast, speech, writing, social-post, script,
  quote-collection, article-about, analysis, reference, other), publication
  date, retrieval time, language, context (work, casual, personal, pressure,
  conflict, public, teaching), rights/origin note, and two honesty flags:
  `attribution` (subject / mixed / about) and `voice` (verbatim / paraphrase /
  summary).
- Speaker attribution: `mixed` transcripts are split on `Name:` labels, and only
  the subject's turns (matched against aliases) become utterances. The turn they
  answered is kept as `prev_turn`. For `about` sources, only quoted spans become
  candidate lines, flagged `secondary-quote`; quotes attributed to someone else
  ("... said one deckhand") are dropped.
- The analysis adds sentence patterns, humor mechanics, stances (with
  confidence and as-of date), behaviour under pressure, contradictions,
  relationships, knowledge boundaries, voice calibration pairs and example
  utterances. Each item carries evidence ids or `inferred: true`.
- `status` is a coverage gate: source count, type variety, verbatim volume
  (default 3,000 words), a pressure context, provenance and index freshness.

### Storage for scaling

```
<store>/
  manifest.json               subject + aliases, indexed source hashes, corpus hash, counts, history
  sources.jsonl               provenance records
  sources/raw/<src-id>.txt    exactly as captured
  sources/normalized/<src-id>.txt   NFKC, straight quotes, timestamps stripped
  corpus/chunks.jsonl         ~200-word chunks: id <src-id>#cN, speakers, tokens, sha256
  corpus/utterances.jsonl     subject lines: id u-<8 hex>-N, kind, context, prev_turn, also_in
  corpus/embeddings/          reserved; manifest.embeddings stays null until used
  profile/stylometry.json
  analysis/analysis.json      latest agent analysis; analysis/history/ keeps old ones
  packs/                      every assembled pack, timestamped
```

- Ids are content-derived (`src-` + 12 hex of the normalized text's sha256), so
  re-adding the same text is a no-op that records the extra URL, and ids stay
  stable across runs and machines.
- Utterances are deduplicated by normalized word sequence across sources; a
  repeat records `also_in`, which is also cross-source evidence for a
  signature phrase.
- `index` is incremental (only sources whose hash is not yet indexed);
  `index --rebuild` reproduces the same corpus hash.
- `retrieve` is BM25 over utterances and chunks with a top-k and a token cap.
  It is the hook for per-turn injection (a tool call from `use-persona` /
  `as-persona`). Embeddings can be added later behind the same command.

### Pack schema v2

A v2 pack is a v1 pack plus new sections, so every existing reader keeps
working (`persona_list.py`, `test/packet_builder.py`, the contract test). The
same JSON Schema validates v1 and v2; v2 adds grounding and budget checks.

```yaml
schema_version: 2
id / display_name / summary / voice          # v1, core layer
core:                                        # always in prompt
  identity: |-                               # 2-3 sentences
  voice_markers: [...]                       # 3-5
  reasoning_habits: [...]                    # 1-2
interaction_stance ... prompt_overlay        # v1 lens, standard layer
idiolect:                                    # extended layer from here
  signature_phrases: [{phrase, evidence, frequency?, use}]
  sentence_patterns: [{pattern, evidence | inferred}]
  discourse_markers: [...]
  stylometry: {basis, basis_words, sentence_words_p50, sentence_words_p90,
               short_sentence_share, question_rate, exclamation_rate,
               contractions_per_100, first_person_per_100, top_openers}
humor: {mechanisms: [{mechanism, evidence}], frequency, targets, lands_when}
under_pressure: [{behavior, evidence}]
stances: [{topic, position, confidence, as_of?, evidence}]
voice_calibration: [{sounds_like, not_like}]
example_utterances: {usage: shape-not-lines, note, items: [{text, evidence: u-..., context}]}
contradictions: [{tension, evidence}]
knowledge_boundaries: {knows, does_not_know, as_of}
relationships: [{who, relation, evidence}]
retrieval:                                   # retrievable layer
  {store, corpus_sha, chunks, utterances, method: bm25, embeddings: null,
   top_k <= 5, max_injected_tokens, command, inject_when}
layers:
  core:     {budget_tokens: 450,  load: always}
  standard: {budget_tokens: 1600, load: default}
  extended: {budget_tokens: 1600, load: on-request}
  retrievable: {load: per-turn}
provenance: {source_type, created_by, sources, source_records, extraction, notes}
quality_level: research-backed
```

Rules enforced by `assemble` / `validate`:

- every evidence id must exist in the store; an item without evidence needs
  `inferred: true`
- example texts are copied from the corpus by id, so they are verbatim by
  construction
- core over budget is an error; extended over budget is trimmed lowest
  priority first (relationships, contradictions, stances, examples, signature
  phrases, ...) and the trimmed items stay in `analysis.json`
- `guardrails` / `anti_patterns` stay forbidden (repo rule)
- token estimates use the repo's `ceil(chars / 4)` rule (`docs/token-overhead.md`)

### Backward compatibility and migration

- All seven bundled v1 packs validate unchanged against the schema.
- `persona_extract.py migrate <pack> --out <pack>` adds `schema_version: 2`,
  `core` (from summary, the first speech patterns and reasoning habits),
  `layers` and `provenance.extraction.migrated_from_schema: 1`, and keeps every
  v1 field. It is idempotent. If a layer is already over its default budget,
  migration raises that layer's `budget_tokens` to the measured size and adds a
  `note`, so the overrun is visible instead of failing. Migration is not applied
  to the bundled packs in this change.
- The packs are read and written with a small stdlib YAML subset because CI
  has no YAML dependency. Output is checked against PyYAML in tests when PyYAML
  is installed.

## Research-to-field mapping

S-ids and C-ids refer to source and claim IDs in a separate LLM-persona research
base (not part of this repo). "Strength" is the research base's own label.
**H** marks a field or number that is my design inference or hypothesis, not a
tested result.

| Field / behaviour | Research basis | Strength / status | Notes |
| --- | --- | --- | --- |
| Over-complete research store, long-form transcripts, collect more than needed | the maintainer's existing-persona request (background research, transcript collection, token-aware pack); S245 ChatHaruhi (script-derived memories); S011 Character-LLM (experience reconstruction) | moderate, abstract-only | **H**: the 3,000-word verbatim floor is a guess sized for stylometry, not a measured threshold |
| `attribution`, `voice` (verbatim/paraphrase), `secondary-quote` | Existing Quality Rules ("never use a quote you couldn't find"); `docs/persona-evaluation.md` source-grounding layer; S184 (generated persona attributes drift from reality) | repo rule + moderate | Makes "verbatim or marked paraphrase" checkable instead of promised |
| Rights / origin note, no platform scraping | S251 YouTube ToS, S252 caption API (own videos only), S249 Whisper for audio you may use, S250 transcript library, S253 impersonation and profiling limits | strong (terms read in full) | The skill tells the agent not to scrape; the tool only ingests files |
| `idiolect.stylometry` (sentence length distribution, rates, openers, markers) | S248 (Biber features separate human and LLM style; instruction tuning widens the gap); S244 (LLMs miss informal personal style; demonstrations help little) | strong / moderate, abstract | **H**: these surface features steer generation; S244/S248 show they measure the gap, not that stating them closes it |
| `signature_phrases` with cross-source recurrence | existing skill Step 5; the research base's humor-in-context eval ("packs breed catchphrases"); S090 (sample phrases copied verbatim) | opinion + moderate | `use: sparingly / regularly / signature` exists to stop catchphrase spam |
| `example_utterances` with `usage: shape-not-lines`, 3-8 items with varied contexts | C016 *mixed*: S091 (random, diverse demos beat matched), S092 (demos help in-character rate but responses reuse ~35% more reference tokens), S090 | moderate, mixed | Diversity by context is the S091 lever; the "shape not lines" label is the S090/S092 copying counter |
| `retrieval` (BM25, top_k ≤ 5, token cap, `inject_when`) | C045 *mixed*: S092, S245, S246 (boundary-aware retrieval), S247 (BM25 beat dense retrievers in most settings; more than 5 documents could hurt; retrieval-only loses informativeness) | moderate, partly snippet-depth | BM25 first, embeddings later is S247-led. **H**: per-turn retrieval helps real-person coding-agent personas (tested studies are mostly fictional characters) |
| `knowledge_boundaries` (`knows`, `does_not_know`, `as_of`) | S011 (protective scenes against out-of-character knowledge), S246 (knowledge-boundary failures), S247 (temporal hallucination) | moderate | |
| `stances` with evidence, confidence, as-of | S099 CharacterBench (knowledge, persona, morality dimensions), S049 InCharacter, S001/S005 (personas don't add knowledge, so positions must come from sources) | moderate / strong | `as_of` because stances change over time |
| `under_pressure`, `contradictions` | S097 PICon (chained interrogation exposes contradictions and evasions), C020 *refuted*, S018 drift | strong | Recording real contradictions keeps the pack from flattening the person and gives evaluation a reference |
| `relationships` | S099 (memory and persona dimensions); S031 Character Card V2 lorebook | moderate / weak | lowest trim priority, retrievable |
| `humor.mechanisms / frequency / targets / lands_when` | the research base's humor-and-finesse analysis §1-2 (mechanisms, craft toolkit) and §6 (finesse); S105 GTVH; S116 joke structure; S137/S138/S153 (affiliative beats aggressive; humor can hurt in tasks) via C027 *mixed* | mixed | `lands_when` is positive guidance, not a restriction list |
| `voice_calibration` (sounds like / not like) | S017 "the void" (under-written characters fall back to the default assistant); S248 (instruction-tuned register differs from human) | opinion / strong | **H**: contrast pairs steer away from assistant register. Kept stylistic so it doesn't become a guardrail section |
| `core` layer, always loaded, ~450 tokens | S061/S059 (stable prompt prefix gets cached), S018 and FINDINGS R1 §4 (re-anchor in long sessions), S241 thin slices (impressions form fast) | strong (caching) / moderate | **H**: 450 tokens. Migrated bundled packs measure 169-468 core tokens; only DaBaby (~468) is over |
| `standard` / `extended` / `retrievable` tiers with budgets and priority trimming | S029/S030 Character.AI Prompt Poet (prioritized truncation); C017 *mixed*: S085, S087, S089 (dense or long prompts degrade) vs S086 (2026 models hold thousands of constraints) | weak (vendor) / mixed | **H**: 1,600 / 1,600 token budgets; migrated bundled packs measure 783-2,657 tokens for the standard fields, so DaBaby, Jesse and Leon are over |
| Structured sections (YAML) rather than prose | C015 *mixed* (S083, S084: format matters, no universal winner; S090, S027 vendor advice) | mixed | The schema is a storage format; rendering to prompt text stays the activation skill's job |
| Field-level provenance (`source_records`, `extraction.corpus_sha`) | `docs/persona-evaluation.md` layer 2; `docs/persona-improvement-backlog.md` ("no review artifact ties key voice claims to source evidence"); S161 (personify itself) | repo need | Enables a future source-grounding judge (known gap in `test/test_manifest.json`) |

## Open questions and limits

- Fetching stays with the host agent's web tools; the helper never touches the
  network. No transcript fetcher or speech-to-text is bundled.
- No model calls anywhere. Nothing here was evaluated with a model: whether v2
  packs read as more faithful than v1 is untested. A PersonaGym/PICon-style
  comparison (S047, S097) is the obvious next eval and needs paid or local runs.
- Stylometry features are English-centric (word regex, marker lexicons).
- Utterance extraction relies on `Name:` speaker labels; other transcript formats
  need preprocessing or `--attribution subject` on pre-cut text.
- `use-persona` / `as-persona` describe how to load v2 layers and call
  `retrieve`, but there is no runtime that enforces it; it is instruction-level,
  like the rest of activation.
- The real-person policy limits are noted in the skill (S253). Whether to ship
  real-person packs publicly is a product decision, not a schema one.
