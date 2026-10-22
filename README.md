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
# Copy skills and commands to your global OpenCode config directory
mkdir -p ~/.config/opencode/skills
cp -r opencode/skills/* ~/.config/opencode/skills/
mkdir -p ~/.config/opencode/commands
cp -r opencode/commands/* ~/.config/opencode/commands/
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
| `extract-persona <name>` | Research a person or character into a reusable source store and build a layered, evidence-mapped pack |

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

Pack format: `docs/personality-pack-contract.md` (schema v1 and v2:
`src/skills/extract-persona/references/persona-pack.schema.json`)

Persona extraction (research store, stylometry, layered packs): `docs/extract-persona.md`

Changes: `CHANGELOG.md`

Activation model: `docs/persona-injection.md`

Persona activation adds prompt context. See `docs/token-overhead.md` for the
current per-pack overhead estimate and the calculation method.

## License

MIT
