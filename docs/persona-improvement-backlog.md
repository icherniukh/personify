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
- Decide whether to ship duplicate/variant packs. `jesse-pinkman` and
  `jesse-pinkman-v1` are both active packs with similar identities. If variants
  remain bundled, document why a user would choose one over the other.
- Promote or fix `draft` packs before public release. `bjarne-stroustrup`,
  `sam-harris`, and `yoda` all claim researched or curated provenance but still
  have `quality_level: draft`.
- Add a source-grounding review for every `research-backed` pack. Several packs
  list sources or provenance notes, but the repo does not yet contain a review
  artifact that ties key voice claims to source evidence.
- Add repetition tests for mandatory expressive devices. Packs that require a
  side note, parable, rhyme, yell, or catchphrase need tests that ensure the
  device varies and does not become a template.
- Decide whether `test/packet_builder.py` should model every rich pack field or
  stay a narrow test helper. It currently composes required fields and
  `expressive_depth`, but ignores richer sections such as Jesse's
  `canonical_references` / `emotional_poles` and DaBaby's `research_basis` /
  `signature_language_markers`.

## Bjarne Stroustrup

Current state: compact and coherent, but thin.

Publish blockers:

- Upgrade source grounding before keeping the pack in the public starter set.
  The provenance says it is derived from official bio/FAQ/quotes/interviews, but
  the pack does not list the actual sources.
- Add evaluation cases. The pack is mostly engineering taste words: abstraction,
  complexity, interface, cost. It needs behavioral tests that distinguish it
  from a generic senior-engineer voice.
- Add structured sources and trait mappings, not only a prose provenance note.

Likely improvements:

- Add more language markers from Stroustrup's actual writing and talks.
- Strengthen the difference between "simplicity", "zero-overhead", "general
  purpose", "type safety", "performance", and "evolution".
- Add examples where the pack pushes back on both over-abstraction and
  under-designed local hacks.

## Sam Harris

Current state: useful analytic structure, but it risks sounding like a generic
clear-thinking consultant.

Publish blockers:

- Upgrade source grounding. The pack is marked `draft` and the provenance says
  it is handcrafted from the repo contract, not researched source material.
- Reconsider the mandatory aside. The pack requires a philosophical or epistemic
  aside in every response. That can create repetition and may hurt practical
  tasks if it fires mechanically.
- Add evaluation cases for long-form reasoning and disagreement. Current tests
  mostly assert that specific strings appear in the packet.

Likely improvements:

- Add source-backed speech markers from interviews, podcast monologues, or
  writing style.
- Make the aside conditional: encouraged when it adds explanatory value, not
  always mandatory.
- Add negative tests for overproduced "rationalist essay" drift.

## Yoda

Current state: recognizable and thoughtfully varied, but still a draft.

Publish blockers:

- Decide whether fictional-character packs are acceptable public starter packs
  for the initial release. If yes, document that they are style assets and not
  official endorsements.
- Revisit the mandatory mini-parable. It is expressive, but requiring it in
  every response can become repetitive and can bury short answers.
- Add evaluation cases that distinguish Yoda-like thematic fronting from simple
  broken English.

Likely improvements:

- Make parables optional or task-sensitive.
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

- Make "scan every response for rhyme opportunities" less mechanical.
- Add a toned-down variant or strength guidance so users can choose strong vs
  moderate execution.
- Add examples where the pack stays useful on technical or serious tasks without
  turning every answer into performance.

## Jesse Pinkman

Current state: distinctive and source-aware, but the active pack is very dense.

Publish blockers:

- Decide what to do with `jesse-pinkman-v1`. If the current pack supersedes it,
  remove or archive the older variant before publishing. If both remain, explain
  the difference in `list-personas` output or docs.
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
- Add comparison tests between the active pack and `jesse-pinkman-v1` if both
  ship.

## Jesse Pinkman v1

Current state: older variant with substantial overlap.

Publish blockers:

- Do not ship as an unexplained duplicate. Either archive it, rename it as a
  legacy example, or document exactly why it exists.

Likely improvements:

- If retained, make it meaningfully different from the active pack, for example
  "lower improvisation, more canonical references" versus the newer pack's
  "freer live execution".
