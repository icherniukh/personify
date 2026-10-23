---
name: extract-persona
description: Create a research-backed Personify persona pack from web-grounded source material.
---

# Research Persona

Grounds every claim in researched source material before generating a normalized Personify persona pack. Use when fidelity and accuracy matter more than speed, or when the subject is obscure enough that training data alone is unreliable.

Extraction has three products, kept apart on purpose:

1. **Research store**: every captured source (raw and normalized text, provenance), a chunked corpus and a deduplicated, speaker-attributed utterance corpus, under `${XDG_DATA_HOME:-~/.local/share}/personify/research/<id>/`. Collect more than the pack needs; the store is what later retrieval, re-extraction and pack updates read, so nothing has to be fetched twice.
2. **Measured profile**: sentence-building statistics and signature-phrase candidates computed from the subject's own lines.
3. **Pack**: a layered, token-aware persona pack (schema v2) whose distinctive claims point at evidence ids in the store.

The bundled helper `scripts/persona_extract.py` (Python 3 stdlib, offline, no model calls) does the storage, indexing, measurement, assembly and validation. You do the searching, fetching, reading and judgment. Design notes and the research behind each field: `docs/extract-persona.md` in the Personify repo. Schema: `references/persona-pack.schema.json`.

```bash
X="python3 <this skill dir>/scripts/persona_extract.py"
$X init <id> --name "<Display Name>" --alias "<speaker label>" --kind real-person|fictional --role "<use-case>"
$X add-source <id> <file|-> --url <url> --type <type> --attribution subject|mixed|about --context <context> [--published YYYY-MM-DD]
$X index <id>          # incremental: only new or changed sources
$X status <id>         # coverage gate
$X profile <id>        # stylometry + signature-phrase candidates
$X retrieve <id> "<query>"   # BM25 over utterances and chunks
$X assemble <id> --analysis analysis.json   # builds, validates and writes the v2 pack
$X validate <pack.yaml> --store <id>
$X migrate <old-pack.yaml> --out <new-pack.yaml>   # v1 -> v2, keeps every v1 field
```

## Inputs Required

Ask the user for any missing inputs before proceeding:

- **Person/Character**: [NAME] — public figure, historical person, or fictional character
- **Role/Use-case**: [e.g. "rigorous senior code reviewer", "creative brainstorming partner"]
- **Extra emphasis** *(optional)*: specific traits to highlight
- **Use-case** *(optional but recommended)*: the kind of work this persona should be useful for

## Phase 1: Research

Before any analysis, gather source material. Run searches in parallel where possible.

### 1A. Breadth Search
Search for an overview of the person/character's public identity, reputation, and what they're most known for:
- `"[NAME] personality traits` / `[NAME] thinking style` / `[NAME] philosophy`
- For fictional characters: `[NAME] [show/book] character analysis`

### 1B. Primary Source Hunt
Search for direct quotes, interviews, writings, and documented behaviors:
- `[NAME] quotes` / `[NAME] interview` / `[NAME] in their own words`
- `[NAME] letters` / `[NAME] speeches` / `[NAME] writings` (where applicable)
- For fictional characters: look for writer/creator commentary and canonical scenes

### 1C. Behavioral Documentation
Search for how they actually behaved in specific high-stakes or characteristic situations:
- `[NAME] how they worked` / `[NAME] management style` / `[NAME] decision making`
- `[NAME] famous anecdotes` / `[NAME] collaborators describe`

### 1D. Long-Form Speech Hunt
Short quotes show what someone said; long-form speech shows how they build sentences. Look for:
- podcast, interview and talk transcripts; speeches; AMAs; long posts or essays in their own words
- for fictional characters: scripts, subtitles and episode transcripts
- at least one source where they are under pressure: a hostile interview, a debate, a hearing, a public argument, a crisis

Use only material you are allowed to use. Prefer published transcripts. Do not scrape platforms whose terms forbid automated access (for example YouTube's terms forbid it, and its official caption API only serves videos you can edit); a transcript the user supplies, or a local speech-to-text run on audio the user may use, is fine. Record the rights or origin in `--rights-note` when there is no public URL.

### 1E. Capture Into the Store
For every useful page, transcript or document (aim for 6-12 sources and several thousand words of the subject's own speech, more than the pack will use):
1. Save the text to a file (or pipe it on stdin) and run `add-source` with its URL, type, publication date if known, and context (`work`, `casual`, `personal`, `pressure`, `conflict`, `public`, `teaching`).
2. Set `--attribution` honestly:
   - `subject`: the whole text is their own words (essay, post, speech)
   - `mixed`: a speaker-labelled transcript (`Name: text` lines); add the label they appear under with `init --alias`
   - `about`: someone else's writing about them; only quoted spans become candidate lines, flagged `secondary-quote`
3. Set `--voice paraphrase` or `summary` when the text is not their exact words.
4. Run `index`. Re-adding identical text is a no-op that records the extra URL. Later sessions can add sources and re-index without refetching anything.

Also extract, while reading:
- Verbatim quotes (copy exactly, note source URL)
- Described behaviors and reactions
- Recurring themes across multiple sources
- Signature terminology, metaphors, or repeated turns of phrase
- Distinctive syntax or cadence markers that make the voice recognizable
- Opinions and stances, with the line that shows them
- What they know well, and what they would not know (era, field, events after the latest source)
- Key relationships and how they talk about those people
- How they react when challenged, criticized or rushed
- Where they contradict themselves

### Research Quality Check
Run `status <id>` and fix what it flags before analysis. It checks:
- [ ] At least 3 distinct primary or secondary sources consulted, of at least 2 types
- [ ] Enough of the subject's own verbatim words (default 3,000) to measure style
- [ ] At least one pressure or conflict context
- [ ] Every source has a URL or an origin/rights note, and everything is indexed

And by hand:
- [ ] All quotes are verbatim or explicitly marked as paraphrases
- [ ] Sources span different contexts (work, personal, under pressure) where available
- [ ] For fictional characters: canonical sources prioritized over fan analysis

If a check cannot be met (an obscure subject, no transcripts), say so in `provenance.notes` and mark the pack `draft`.

## Phase 2: Analysis (show your work)

With source material in hand, work through each step and cite sources inline.

### Step 1: Persona Overview
2–3 sentences capturing essential identity and canonical essence. Cite the sources that shaped this summary.

### Step 2: Core Principles & Thinking Style
Bullet list of driving commitments, values, and cognitive habits — each traceable to at least one researched source. Mark inferences explicitly: *(inferred from [source])*.

### Step 3: Key Illustrative Quotes & Behaviors
3–5 quotes pulled directly from research. Format:

> "Exact quote here." — Source, context

If exact wording is uncertain, mark it: *(paraphrase — [source] describes this as...)*

Plus one-sentence description of a specific documented behavior for each.

### Step 4: Communication Style
Precise characterization of tone, vocabulary, sentence rhythm, directness, humor type (or its absence), and emotional temperature — grounded in the quotes and sources collected, not impressions.

### Step 5: Signature Language Markers
List the concrete linguistic markers that should survive extraction:

- preferred terminology and recurring metaphors
- canonical references, comparisons, or namedrops they naturally reach for
- signature syntax or sentence-order patterns
- cadence habits, pivots, openings, and emphasis lines
- what should appear regularly for recognizability
- what should be trimmed only if it reduces clarity or task usefulness

For distinctive fictional voices, this step is mandatory. Do not reduce a character like Yoda to "wise" and "patient" while dropping inversion and canonical terminology.
For loud, stylized, or emotionally reactive figures, also capture how they rant, jab, joke, yell, spiral, or nearly drift into full character before returning to the point.

### Step 5b: Measured Profile
Run `profile <id>` and read the numbers before writing style claims. It reports sentence-length distribution (p10/p50/p90 and histogram), short-sentence share, question and exclamation rates, commas per sentence, pronoun and contraction rates, discourse markers, hedges, intensifiers, common sentence openers, and signature-phrase candidates: n-grams that recur across sources, with utterance ids.

- Confirm or reject your impressions against the numbers. "Long winding sentences" with a p50 of 6 words is wrong.
- Candidates are leads, not conclusions. Keep the ones that read as the person's own phrasing; drop topic words.
- Use `retrieve <id> "<topic>"` to pull the subject's actual lines on a topic before writing a stance.

### Step 5c: Depth Profile
Each item below needs evidence ids from the store (`src-…`, `src-…#cN` chunk, or `u-…` utterance), or `"inferred": true` when it is your inference:
- **Sentence patterns**: syntax, rhythm, how they open, pivot and land a point
- **Humor mechanics**: which mechanisms (self-deprecation, deadpan, exaggeration, callbacks, wordplay), at whom, how often, and when it lands
- **Stances**: topic, position, confidence, and as-of date
- **Under pressure**: what they do when challenged
- **Contradictions**: tensions between what they say and do, kept rather than smoothed over
- **Relationships** and **knowledge boundaries**
- **Voice calibration**: pairs of "sounds like" versus "not like" lines, to steer away from generic assistant voice
- **Example utterances**: 3-8 utterance ids that show range (calm, pressured, funny, explaining). The assembler copies their text from the corpus, so they are always verbatim.

### Step 6: Role Adaptation Rules
How researched traits translate into this specific role. Where their actual documented strengths make the role better, how they vary their moves, and what positive behaviors make the output land.

## Phase 3: Output

### Step 7: Analysis JSON

Write the analysis as JSON (for example `analysis.json`). It holds your judgment; the assembler adds measured data, corpus pointers, provenance and the layer plan.

- v1 lens fields, unchanged from earlier packs:
  - `display_name`, `summary` (one-line pack description), `voice` (map: tone, style, pacing)
  - `interaction_stance`, `value_profile` (positive value the pack adds), `reasoning_style`, `preferred_terminology`, `speech_patterns`, `default_structures`, `interaction_rules`: lists of strings
  - `ambiguity_policy`, `tradeoff_policy`, `compression_policy`, `prompt_overlay`: text
- `core`: `identity` (2-3 sentences), `voice_markers` (3-5), `reasoning_habits` (1-2). This is the always-loaded layer; keep it under its budget (default about 450 tokens together with name, summary and voice).
- `idiolect`: `signature_phrases` (`phrase`, `evidence`, `use`: sparingly/regularly/signature), `sentence_patterns` (`pattern`, `evidence`), optional `discourse_markers`. If you omit signature phrases, the top measured candidates are used.
- `humor`: `mechanisms` (`mechanism`, `evidence`), `frequency`, `targets`, `lands_when`
- `stances`, `under_pressure`, `contradictions`, `relationships`: lists of objects with `evidence` ids or `"inferred": true`
- `knowledge_boundaries`: `knows`, `does_not_know`, `as_of`
- `voice_calibration`: `sounds_like` / `not_like` pairs
- `example_utterances`: `[{"evidence": "u-…", "context": "…"}]`
- optional `provenance.notes`, `retrieval_inject_when`

Requirements:
- Every distinctive speech claim should be traceable to research or clearly marked as inference.
- Preserve signature language markers in structured fields; do not bury them only inside `prompt_overlay`.
- For vivid personas, build the pack so the style can be applied unapologetically instead of being laundered into tasteful neutrality.
- If research shows recurring references, comparisons, callbacks, slogans, world-specific language, or dramatic emphasis, preserve that behavior explicitly.
- The pack must stay job-usable. Usefulness remains primary.
- Do not include `guardrails`, `anti_patterns`, or other restriction sections. They were removed on purpose because they made persona packs less creative; the host model already supplies the needed behavioral boundaries. `voice_calibration` is a style contrast, not a restriction list.

### Step 8: Assemble, validate and write the file

```bash
$X assemble <id> --analysis analysis.json
```

`assemble` merges your analysis with the measured profile and the corpus, then validates the result against `references/persona-pack.schema.json` and the evidence ids in the store. It fails on unknown evidence ids, unmarked inferences, forbidden fields, or a core layer over budget. When the extended layer is over budget it drops the lowest-priority items (relationships, then contradictions, then stances, ...) from the pack and reports them; they stay in the store's `analysis/analysis.json` and remain retrievable. Every analysis and pack version is kept under the store's `analysis/history/` and `packs/`.

The resulting pack (schema v2) keeps every v1 field, so existing listing and activation keep working, and adds:

- `schema_version: 2`, `core`, `idiolect` (with measured `stylometry`), `humor`, `stances`, `under_pressure`, `contradictions`, `knowledge_boundaries`, `relationships`, `voice_calibration`
- `example_utterances` with `usage: shape-not-lines`: the lines show rhythm and stance; they are not lines to paste
- `retrieval`: where the corpus lives, its hash and size, the BM25 retrieve command, a top-k and a token cap for per-turn injection
- `layers`: which fields load always (`core`), by default (`standard`), on request (`extended`) or per turn from the corpus (`retrievable`), with token budgets
- `provenance`: `source_type: research-backed`, the `sources` URL list, per-source `source_records`, `extraction` metadata (tool version, corpus hash), and a `notes` line
- `quality_level: research-backed`

The pack is written to the persistent user persona directory:

```
${XDG_DATA_HOME:-~/.local/share}/personify/personas/<id>.yaml
```

This directory is user-owned and survives plugin updates. Do not write newly extracted user packs into bundled skill directories or `src/assets/personalities/` unless the user explicitly asks to change the project’s bundled starter packs.

If the new pack uses the same `id` as a bundled pack, it becomes the user override for that persona during listing and activation. Do not only output it to conversation — the file is the deliverable. Confirm the path after writing.

### Updating an existing pack

- New material: `add-source`, `index`, `profile`, edit the stored `analysis/analysis.json`, then `assemble <id>` again. Nothing already captured is refetched.
- An older (v1) pack without a store: `migrate <pack> --out <pack>` adds `core`, `layers` and extraction metadata and keeps every v1 field. Then research it into a store when there is time.

## Quality Rules

- Never use a quote you couldn't find in research — paraphrase with source attribution or omit
- If sources conflict on a trait, note the conflict and default to the majority or most primary source
- If the persona has distinctive syntax, terminology, or cadence, extract those explicitly
- Do not flatten strong voices into generic summary adjectives
- For strong characters, bias toward slightly too recognizable rather than too sanitized
- Preserve researched reference habits and comparison style when they are part of why the persona lands
- Personality is a cognitive lens, not a costume
- Example utterances are shape, not lines: never instruct the persona to reuse them verbatim
- Real people: model voice and reasoning habits for the task; do not present invented statements as things they said, and do not collect private or sensitive personal information
- Sources belong in `provenance.sources` in the file; after writing, briefly confirm the path
