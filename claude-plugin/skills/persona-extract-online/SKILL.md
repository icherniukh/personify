---
name: persona-extract-online
description: Research-backed extraction skill for turning a person or character into a normalized promptonality personality pack.
---

# Persona Extract Online

Like `persona-extract`, but grounds every claim in researched source material before generating a normalized `promptonality` personality pack. Use when fidelity and accuracy matter more than speed, or when the subject is obscure enough that training data alone is unreliable.

## Inputs Required

Ask the user for any missing inputs before proceeding:

- **Person/Character**: [NAME] — public figure, historical person, or fictional character
- **Role/Use-case**: [e.g. "rigorous senior code reviewer", "creative brainstorming partner"]
- **Extra emphasis** *(optional)*: specific traits to highlight
- **Base workflow** *(optional but recommended)*: the neutral skill or job this personality will be applied to

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

### 1D. Fetch & Extract
For the most promising 2–3 URLs from the above searches, fetch the pages and extract:
- Verbatim quotes (copy exactly, note source URL)
- Described behaviors and reactions
- Recurring themes across multiple sources
- Signature terminology, metaphors, or repeated turns of phrase
- Distinctive syntax or cadence markers that make the voice recognizable

### Research Quality Check
Before proceeding, verify:
- [ ] At least 3 distinct primary or secondary sources consulted
- [ ] All quotes are verbatim or explicitly marked as paraphrases
- [ ] Sources span different contexts (work, personal, under pressure) where available
- [ ] For fictional characters: canonical sources prioritized over fan analysis

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

### Step 6: Role Adaptation Rules
How researched traits translate into this specific role. Where their actual documented strengths make the role better, and where guardrails are needed.

## Phase 3: Output

### Step 7: Personality Pack YAML (the deliverable)

Output a complete `promptonality` pack YAML grounded in the research. Requirements:

- Include explicit fields for:
  - `voice`
  - `interaction_stance`
  - `value_profile`
  - `reasoning_style`
  - `preferred_terminology`
  - `speech_patterns`
  - `default_structures`
  - `ambiguity_policy`
  - `tradeoff_policy`
  - `compression_policy`
  - `interaction_rules`
  - `guardrails`
  - `anti_patterns`
  - `prompt_overlay`
- Every distinctive speech claim should be traceable to research or clearly marked as inference.
- Preserve signature language markers in structured fields; do not bury them only inside `prompt_overlay`.
- For vivid personas, build the pack so the style can be applied unapologetically instead of being laundered into tasteful neutrality.
- If research shows recurring references, comparisons, callbacks, slogans, world-specific language, or dramatic emphasis, preserve that behavior explicitly.
- The pack must stay job-usable. Usefulness remains primary.

## Quality Rules

- Never use a quote you couldn't find in research — paraphrase with source attribution or omit
- If sources conflict on a trait, note the conflict and default to the majority or most primary source
- If the persona has distinctive syntax, terminology, or cadence, extract those explicitly
- Do not flatten strong voices into generic summary adjectives
- For strong characters, bias toward slightly too recognizable rather than too sanitized
- Preserve researched reference habits and comparison style when they are part of why the persona lands
- Personality is a cognitive lens, not a costume
- After delivering the pack, list the sources consulted so the user can verify
