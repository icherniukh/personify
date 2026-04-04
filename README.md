# Promptonality

This plugin is the first repo-local boilerplate for interchangeable personality handling on the Codex side.

Claude support now exists through generated standalone skills under:

- `skills/persona-start/`
- `skills/persona-apply/`
- `skills/persona-list/`
- `skills/persona-extract/`
- `skills/persona-extract-online/`

Those are exported from the plugin source with:

```bash
python3 plugins/promptonality/scripts/export_claude_skills.py
```

Claude Code plugin support also exists as a generated package under:

- `plugins/promptonality/claude-plugin/`

Generate it with:

```bash
python3 plugins/promptonality/scripts/export_claude_plugin.py
```

## Structure

- `.codex-plugin/plugin.json`: plugin manifest
- `skills/architecture-review-core/`: neutral project architecture review workflow
- `skills/bjarne-stroustrup-architecture-review/`: personality-flavored architecture-review variant
- `skills/yoda-architecture-review/`: personality-flavored architecture-review variant
- `skills/persona-start/`: session bootstrap for any workflow or pack pairing
- `skills/persona-apply/`: one-off workflow-plus-pack composition
- `skills/persona-list/`: lists installed personality packs
- `skills/orchestrator-core/`: neutral workflow logic
- `skills/sam-harris-orchestrator/`: personality-flavored orchestrator variant
- `skills/persona-extract/`: local persona prompt generator
- `skills/persona-extract-online/`: research-backed persona prompt generator
- `assets/personalities/bjarne-stroustrup.yaml`: standalone Stroustrup personality pack
- `assets/personalities/sam-harris.yaml`: standalone personality pack
- `assets/personalities/yoda.yaml`: standalone Yoda personality pack

## Rule

Do not clone whole orchestrators just to change voice.

Keep the workflow core neutral, keep the persona in its own file, and let lightweight variants compose the two.

## Design

`promptonality` treats personality as a bounded cognitive lens rather than a decorative style layer.

That means a pack is allowed to change:

- framing priorities
- ambiguity handling
- tradeoff exposure
- compression style
- default answer structure
- voice and interaction stance

But it is not allowed to replace:

- task completion
- correctness
- safety
- operational competence

## Current Limitation

This is an explicit composition convention, not a hidden runtime import mechanism.

The current variant skill documents which base workflow and which personality pack it composes. Today that variant is implemented as a thin wrapper. That keeps the pieces separable now, while leaving room for a future loader or UI-driven selector.

## Current Model

`promptonality` currently centers on two user-facing outcomes:

- `new skill`: a skill created from scratch
- `variant`: a personality-flavored derivative of an existing workflow skill

In the current implementation, the example variants are represented by thin skills that point at:

- a neutral base workflow
- a standalone personality pack

That thin-wrapper shape is an implementation detail, not the long-term product concept.

## Usage

Command set:

- `persona-list`
- `persona-apply`
- `persona-start`
- `persona-extract`
- `persona-extract-online`

Use the neutral workflow when you want the orchestration behavior without persona flavor:

- `plugins/promptonality/skills/orchestrator-core/SKILL.md`

Use the Sam Harris variant when you want the same workflow with that overlay applied:

- `plugins/promptonality/skills/sam-harris-orchestrator/SKILL.md`

Use the `persona-start` skill when you want any promptonality workflow, variant, or workflow-plus-pack pairing to govern the rest of the session:

- `plugins/promptonality/skills/persona-start/SKILL.md`

Use the `persona-apply` skill when you want a one-off or thread-level workflow-plus-pack composition without making it the session default:

- `plugins/promptonality/skills/persona-apply/SKILL.md`

Use the installed-personality listing skill when you want to see which packs are available:

- `plugins/promptonality/skills/persona-list/SKILL.md`

or run:

```bash
python3 plugins/promptonality/scripts/persona_list.py
```

Use the neutral architecture-review workflow when you want a project-structure review without persona flavor:

- `plugins/promptonality/skills/architecture-review-core/SKILL.md`

Use the Stroustrup architecture variant when you want the same review with a systems-language design lens:

- `plugins/promptonality/skills/bjarne-stroustrup-architecture-review/SKILL.md`

Use the Yoda architecture variant when you want the same review with a patient, essentials-first lens:

- `plugins/promptonality/skills/yoda-architecture-review/SKILL.md`

Use the personality extraction skills when you want to generate new persona prompts or packs:

- `plugins/promptonality/skills/persona-extract/SKILL.md`
- `plugins/promptonality/skills/persona-extract-online/SKILL.md`

Composition rule:

- start from the neutral workflow
- apply the personality pack after that
- if personality conflicts with task success, correctness wins

`persona-start` rule:

- start from the session bootstrap layer when the user wants a workflow, variant, or workflow-plus-pack pairing to govern the whole session
- make the selected mode the default for subsequent nontrivial work
- let direct user instructions override the active session mode

Example session starters:

- `Use the Sam Harris orchestrator for this session.`
- `For this session, use Yoda architecture review.`
- `Default to architecture-review-core with the Bjarne Stroustrup pack.`

`persona-apply` rule:

- yes, you can say `use this skill with this personality` even if no dedicated wrapper exists yet
- today that works by explicit composition at prompt/session level
- it does not automatically create a new named installed variant

Current pack:

- `plugins/promptonality/assets/personalities/bjarne-stroustrup.yaml`
- `plugins/promptonality/assets/personalities/sam-harris.yaml`
- `plugins/promptonality/assets/personalities/yoda.yaml`

## Testing

Run the plugin smoke test with:

```bash
bash plugins/promptonality/test/run-test.sh
```

Verify the Claude-facing export is in sync with:

```bash
python3 plugins/promptonality/scripts/export_claude_skills.py --check
```

Verify the Claude plugin package is in sync with:

```bash
python3 plugins/promptonality/scripts/export_claude_plugin.py --check
```

Run the live model test with:

```bash
OPENAI_API_KEY=... OPENAI_MODEL=... \
python3 plugins/promptonality/test/live_model_test.py --repeats 3
```

Run a single case with:

```bash
OPENAI_API_KEY=... OPENAI_MODEL=... \
python3 plugins/promptonality/test/live_model_test.py --case incident-triage --repeats 3
```

Run the architecture persona comparison with:

```bash
OPENAI_API_KEY=... OPENAI_MODEL=... \
python3 plugins/promptonality/test/architecture_live_test.py --repeats 3
```

This validates:

- required files exist
- `plugin.json` parses and matches the plugin package contract
- the Sam Harris pack includes the required contract fields
- the Sam Harris variant points at the neutral core and standalone pack
- the `persona-start` skill can activate any packaged workflow or pack pairing at session scope
- the personality-listing script reports the installed packs from the plugin assets directory
- the plugin manifest matches the folder name and valid skill paths
- the plugin remains independent from Rue
- the composed Sam Harris instruction packet preserves core routing behavior while adding the expected overlay traits

The smoke test does **not** call a live model. It tests the repo's package shape, composition logic, and resulting instruction text.

The live model test is the meaningful behavior check. It composes the neutral and Sam Harris instruction packets, sends both to a real model for the same fixed tasks, and then asks a judge pass whether:

- both answers still solve the task
- the neutral version stays neutral
- the Sam Harris version shows the intended cognitive lens
- the difference is real without turning into parody

Because live model judgments vary from run to run, the recommended mode is `--repeats 3`, which uses a majority result instead of trusting a single pass.

The architecture comparison test does the same thing for:

- neutral architecture review
- Bjarne Stroustrup architecture review
- Yoda architecture review

That test is meant to answer the harder question: whether the persona changes the review in a functionally opinionated way rather than merely changing tone.

It requires a working `OPENAI_API_KEY`, a model name in `OPENAI_MODEL`, and sufficient API quota.
