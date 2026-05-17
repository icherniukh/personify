# Persona Selection

Persona selection is a small routing layer before persona activation. It chooses
a valid persona pack, then the existing activation flow loads that pack as the
voice and reasoning lens.

The selector returns two fields:

- `persona_id`: the pack id to activate.
- `rationale`: a short explanation of why that pack was selected.

## Explicit

Use explicit mode when the caller already knows the pack id.

```python
from pathlib import Path

from scripts.persona_selector import PersonaSelectionRequest, PersonaSelector

selector = PersonaSelector.from_directory(Path("src/assets/personalities"))
result = selector.select(
    PersonaSelectionRequest(
        mode="explicit",
        persona_id="sam-harris",
        task="Review this argument for hidden assumptions.",
    )
)
```

The result should be passed to the normal persona activation path:

```text
use-persona sam-harris
```

## Auto

Use auto mode when the caller wants the system to choose a useful pack for the
task. Auto mode scores metadata fields such as summary, stance, values,
reasoning style, and terminology. It does not use per-persona command branches.

```python
result = selector.select(
    PersonaSelectionRequest(
        mode="auto",
        task="Design an API interface with maintainability tradeoffs.",
        context="Need calm engineering judgment.",
    )
)
```

The rationale should mention the metadata affinity terms that drove the choice.

## Random

Use random mode when the caller wants a shuffle or novelty mode. Provide a seed
when reproducibility matters, especially in tests.

```python
result = selector.select(
    PersonaSelectionRequest(
        mode="random",
        task="Pick a fresh voice for debugging.",
        seed="debug-session-2026-05-16",
        include_ids={"sam-harris", "leon", "yoda"},
        exclude_ids={"yoda"},
    )
)
```

The same seed and filters produce the same result. Include and exclude filters
apply before the seeded choice is made.
