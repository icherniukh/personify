---
name: persona-extract
description: Local extraction skill for turning a person or character into a normalized promptonality personality pack.
---

# Persona Extract

Distill any well-documented public figure, historical person, or fictional character into a normalized `promptonality` personality pack that can be injected into a base workflow. The primary deliverable is pack YAML, not a freeform one-shot prompt.

## Inputs Required

Ask the user for any missing inputs before proceeding:

- **Person/Character**: [NAME] — public figure, historical person, or fictional character
- **Role/Use-case**: [e.g. "rigorous senior code reviewer", "creative brainstorming partner"]
- **Extra emphasis** *(optional)*: specific traits to highlight
- **Base workflow** *(optional but recommended)*: the neutral skill or job this personality will be applied to

## Seven-Step Process

Work through all seven steps. Steps 1–6 are your internal analysis (show them). Step 7 is the deliverable.

### Step 1: Persona Overview
2–3 sentences capturing the essential identity and canonical essence — who they are as the world knows them, what they're most known for, and what makes them unmistakable.

### Step 2: Core Principles & Thinking Style
Bullet list of driving commitments, values, and cognitive habits drawn from their works, writings, interviews, or canonical media. Be specific — "values empirical evidence over authority" beats "smart and curious."

### Step 3: Key Illustrative Quotes & Behaviors
3–5 short signature quotes (or precise paraphrases if exact quotes aren't reliably sourced) plus a one-sentence description of how they typically behaved in specific situations. Choose examples that reveal personality in action. Never force or fabricate — if uncertain, paraphrase and note it.

### Step 4: Communication Style
Exact tone, vocabulary habits, sentence rhythm, level of directness, characteristic use (or deliberate absence) of humor, analogies, and emotional temperature. Be precise: "terse, Socratic questions with long silences before answering" is more useful than "thoughtful."

### Step 5: Signature Language Markers
Extract the concrete surface markers that make this persona immediately recognizable:

- preferred terminology and recurring metaphors
- canonical references, comparisons, or namedrops they would naturally reach for
- signature syntax and sentence-shape patterns
- cadence markers, openings, pivots, and emphasis habits
- what must appear regularly for the voice to stay recognizable
- what should be trimmed only if it harms clarity or usefulness

For characters with distinctive speech, be explicit. "Wise teacher" is not enough for Yoda. Capture inversion, idiom, and canonical terminology as separate extraction targets.
For loud or highly stylized personas, do not stop at "tone." Capture how they rant, snap, compare, joke, yell, pivot, or nearly drift into full character before getting back on task.

### Step 6: Role Adaptation Rules
How to translate their real/fictional strengths into this specific job. Where their personality makes the role better, how it varies its moves, and what positive behaviors make the output land.

### Step 7: Personality Pack YAML

Generate the full `promptonality` pack YAML using the repo contract. Requirements:

- Include concrete fields for:
  - `id` — kebab-case machine identifier
  - `display_name`
  - `summary` — one-line pack description
  - `voice`
  - `interaction_stance` — list of strings
  - `value_profile` — list of strings (positive value the pack adds)
  - `reasoning_style` — list of strings
  - `preferred_terminology` — list of strings
  - `speech_patterns` — list of strings
  - `default_structures` — list of strings
  - `ambiguity_policy`
  - `tradeoff_policy`
  - `compression_policy`
  - `interaction_rules` — list of strings
  - `prompt_overlay`
  - `provenance` — set `source_type: curated` and add a `notes` line describing the source basis
  - `quality_level: draft`
- Treat signature language markers as first-class extraction targets, not incidental wording.
- The `prompt_overlay` should reinforce the pack; it should not be the only place where distinctive speech survives.
- For vivid personas, build the pack so the style can be applied unapologetically. Do not extract a timid, cleaned-up version just because it sounds more professional.
- If the character naturally uses references, comparisons, callbacks, world-specific language, or dramatic emphasis, preserve that behavior in structured fields and reinforce it in `prompt_overlay`.
- Keep the pack operational. The persona must improve how the job gets done, not just how it sounds.
- Do not include `guardrails`, `anti_patterns`, or other restriction sections. They were removed on purpose because they made persona packs less creative; the host model already supplies the needed behavioral boundaries.

### Step 8: Write the file

Write the YAML to:

```
src/assets/personalities/<id>.yaml
```

relative to the source root (e.g. `plugins/promptonality/src/assets/personalities/yoda.yaml`). Do not only output it to conversation — the file is the deliverable. Confirm the path after writing.

If useful, you may append a short optional note to the conversation showing how this pack would pair with a specific base workflow.

## Quality Rules

- Preserve the person or character's own expressive range instead of adding external caution language
- Never fabricate quotes — paraphrase with a note if exact wording is uncertain
- If the persona has signature terminology or syntax, capture it explicitly in `preferred_terminology` and `speech_patterns`
- Do not flatten a distinctive speaker into generic traits like "wise," "direct," or "analytical"
- For strong characters, bias toward slightly too recognizable rather than too sanitized
- Preserve canonical reference habits and comparison style when they are part of what makes the voice land
- The extracted pack must feel like the real person quietly doing the job — precise, consistent, genuinely useful
- Personality is a cognitive lens, not a costume
