# Persona Improvement Backlog

This is the publish-blocking review list for bundled persona packs.

The goal is not to polish every pack forever. The goal is to make the starter
set credible enough that public users understand the framework and do not treat
weak bundled packs as the ceiling of the system.

## Cross-Pack Issues

- Add output-evaluation cases for every bundled persona, not only the current
  Sam/Jesse/Yoda focused cases. The current contract test validates shape, but
  it does not prove that each pack creates a recognizable functional delta.
- Fix stale evaluation manifest entries. `test/test_manifest.json` still names
  scripts that no longer exist, including `yoda_style_test.py`,
  `decision_test.py`, and `integration_test.py`.
- Do not ship unexplained duplicate/variant packs. `jesse-pinkman-v1` was
  compared against the current `jesse-pinkman` pack and removed because v1 made
  the thematic side note mandatory in every response, while the current pack
  keeps the same core material but treats canon references and side notes as
  varied improvisation.
- Promote or fix `draft` packs before public release. `sam-harris` and `yoda`
  both claim researched or curated provenance but still have
  `quality_level: draft`.
- Add a source-grounding review for every `research-backed` pack. Several packs
  list sources or provenance notes, but the repo does not yet contain a review
  artifact that ties key voice claims to source evidence.
- Add repetition tests for expressive devices. Packs that use a side note,
  parable, rhyme, yell, or catchphrase need tests that ensure the device varies
  and does not become a template.
- Decide whether `test/packet_builder.py` should model every rich pack field or
  stay a narrow test helper. It currently composes required fields and
  `expressive_depth`, but ignores richer sections such as Jesse's
  `canonical_references` / `emotional_poles` and DaBaby's `research_basis` /
  `signature_language_markers`.

## Sam Harris

Current state: useful analytic structure, but it risks sounding like a generic
clear-thinking consultant.

Publish blockers:

- Upgrade source grounding. The pack is marked `draft` and the provenance says
  it is handcrafted from the repo contract, not researched source material.
- Keep the philosophical aside optional and value-driven. The pack previously
  required it in every response, which created repetition risk and could hurt
  practical tasks if it fired mechanically.
- Add evaluation cases for long-form reasoning and disagreement. Current tests
  mostly assert that specific strings appear in the packet.

Likely improvements:

- Add source-backed speech markers from interviews, podcast monologues, or
  writing style.
- Add repetition-control tests for the aside so it appears when useful without
  becoming a predictable template.
- Add negative tests for overproduced "rationalist essay" drift.

## Yoda

Current state: recognizable and thoughtfully varied, but still a draft.

Publish blockers:

- Decide whether fictional-character packs are acceptable public starter packs
  for the initial release. If yes, document that they are style assets and not
  official endorsements.
- Keep the mini-parable optional and task-sensitive. It is expressive, but
  requiring it in every response can become repetitive and can bury short
  answers.
- Add evaluation cases that distinguish Yoda-like thematic fronting from simple
  broken English.

Likely improvements:

- Add tests for concise answers where no parable is needed and longer answers
  where the parable adds real value.
- Add examples for concise technical answers where the persona remains visible
  without forcing a story.
- Recheck source claims and cite the exact material behind the speech-pattern
  summary.
- Add or repair the missing Yoda style runner if `yoda_cases.json` remains part
  of the evaluation surface.

## Hikaru Nakamura

Current state: the best positioned non-fiction starter pack.

Publish blockers:

- Add evaluation cases for verdict-first reasoning, fast pivoting, and
  constructive bluntness.
- Verify quote/source quality. Some listed sources are stronger than others;
  keep primary interviews and high-quality coverage, downgrade quote databases
  where possible.
- Map key claims such as the Kasparov/coaching confidence material to specific
  sources instead of leaving them only in prose.

Likely improvements:

- Add more real streamer cadence markers without turning them into catchphrase
  spam.
- Add chess-domain and non-chess-domain examples to prove the pack generalizes.
- Add tests for "blunt but constructive" so it does not become generic harshness.

## DaBaby

Current state: vivid and heavily developed, but high-risk for repetition and
overperformance.

Publish blockers:

- Review whether this should be in the public starter set before the mechanism
  and persona-quality docs are stronger. It is expressive enough to showcase the
  framework, but also easiest to misuse or parody badly.
- Add repetition-control tests for all-caps outbursts, rhymes, profanity, and
  catchphrase reuse.
- Verify source grounding and remove weak or low-quality sources if better
  sources are available.

Likely improvements:

- Keep rhyme/outburst behavior opportunistic rather than mechanical.
- Add a toned-down variant or strength guidance so users can choose strong vs
  moderate execution.
- Add examples where the pack stays useful on technical or serious tasks without
  turning every answer into performance.

## Jesse Pinkman

Current state: distinctive and source-aware, but the active pack is very dense.

Publish blockers:

- Keep `jesse-pinkman-v1` removed from the active asset set. The current pack
  supersedes it because it removes mandatory side-note behavior and adds
  explicit variation controls.
- Add tests for variation. The pack explicitly says not to replay a fixed
  checklist, but the amount of canonical material creates checklist risk.
- Revisit mandatory profanity/catchphrase frequency. The current pack says some
  markers should appear naturally in most responses; that needs evaluation to
  avoid flattening every task into the same register.
- Convert provenance from a prose source note into structured source URLs,
  quotes, and trait mappings.

Likely improvements:

- Keep the human-cost lens; it is the strongest functional delta.
- Reduce duplicate instructions between `canonical_references`,
  `speech_patterns`, `interaction_rules`, and `prompt_overlay`.
