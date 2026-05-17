# Personify

Portable persona packs for agent voice, cadence, and reasoning style.

## Install

### Claude Code

```bash
claude plugin marketplace add icherniukh/personify
claude plugin install personify@personify
```

### Codex

```bash
codex plugin marketplace add icherniukh/personify
```

### Gemini CLI

```bash
gemini extensions install https://github.com/icherniukh/personify --consent
```

### OpenCode

```bash
# Copy skills to your global OpenCode config directory
cp -r opencode/skills/* ~/.config/opencode/skills/
```

### Pi

```bash
pi install git:github.com/icherniukh/personify
```

## Commands

| Command | What it does |
| --- | --- |
| `list-personas` | Show available persona packs |
| `use-persona <persona>` | Set a persona as the default for the session |
| `as-persona <persona> <task>` | Apply a persona to one task |
| `extract-persona <name>` | Create a new pack from web-grounded research |

Examples:

```text
List available personas.
Use the Hikaru Nakamura persona for this session.
Apply the Sam Harris persona to this task.
Research a persona pack for Ada Lovelace.
```

## Contributing

Source lives in `src/`. After editing run:

```bash
python3 scripts/package.py build --target all
```

Pack format: `docs/personality-pack-contract.md`

Persona activation adds prompt context. See `docs/token-overhead.md` for the
current per-pack overhead estimate and the calculation method.

## License

MIT
