# Personify

Portable persona packs for agent voice, cadence, and reasoning style.

Personify is not a workflow catalog. It provides:

- persona pack discovery
- session-wide persona activation
- one-off persona application
- local persona-pack creation
- research-backed persona-pack creation
- Claude Code, Codex, and Gemini package adapters

## Install

### Claude Code

```bash
claude plugin marketplace add icherniukh/personify
claude plugin install personify@personify
```

Local checkout:

```bash
claude plugin marketplace add /path/to/personify
claude plugin install personify@personify
```

Session-only:

```bash
claude --plugin-dir /path/to/personify/claude
```

### Codex

Codex currently exposes marketplace management in the CLI. Add the marketplace,
then install or enable the plugin from the Codex plugin UI/runtime.

```bash
codex plugin marketplace add icherniukh/personify
```

Local checkout:

```bash
codex plugin marketplace add /path/to/personify
```

### Gemini CLI

```bash
gemini extensions install https://github.com/icherniukh/personify --consent
```

For local development:

```bash
gemini extensions link /path/to/personify/gemini --consent
```

## Commands

Personify exposes four user-facing commands/skills:

| Command | Use it for |
| --- | --- |
| `list-personas` | Show available persona packs |
| `use-persona` | Make a persona the default for the session |
| `as-persona` | Apply a persona to one task or thread |
| `extract-persona` | Create a pack from web-grounded research |

Portable natural-language examples:

```text
List available personas.
Use the Hikaru Nakamura persona for this session.
Apply the Sam Harris persona to this task.
Research a persona pack for Ada Lovelace.
```

## Source

Author source files here:

```text
src/package.json
src/skills/
src/assets/personalities/
```

Generated public packages live here and are versioned:

```text
codex/
claude/
gemini/
```

Regenerate packages after editing `src/`:

```bash
python3 scripts/package.py build --target all
```

## Validate

```bash
python3 scripts/package.py check --target all
python3 test/package_test.py
python3 test/claude_plugin_test.py
python3 test/personality_pack_contract_test.py
claude plugin validate .
claude plugin validate claude
gemini extensions validate gemini
```

## Persona Packs

Bundled packs live in:

```text
src/assets/personalities/
```

List them locally with:

```bash
python3 scripts/persona_list.py
```

Pack format is documented in:

```text
docs/personality-pack-contract.md
```

Persona packs intentionally do not use local `guardrails` or `anti_patterns`
sections. Improve them by strengthening voice, reasoning habits, examples, and
evaluation coverage.

## License

MIT
