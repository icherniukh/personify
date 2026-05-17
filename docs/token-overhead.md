# Token Overhead

Personify applies a persona by adding a Persona Activation Packet and the
selected YAML pack fields to the task instructions. That extra prompt context is
useful, but it is not free.

## Methodology

The current measurement is deterministic and dependency-free:

1. Build the neutral instruction packet from `test/packet_builder.py`.
2. Build the same task with each persona pack applied.
3. Estimate tokens as `ceil(character_count / 4)`.
4. Report persona overhead as `with_persona - neutral`.

This is an estimate, not model-tokenizer output. It is meant for package-level
comparison and regression tracking without binding the repo to one provider's
tokenizer.

Regenerate the table with:

```bash
python3 scripts/token_overhead.py --markdown
```

## Current Estimates

| Persona | Neutral tokens | With persona | Overhead |
| --- | ---: | ---: | ---: |
| `bjarne-stroustrup` | 31 | 930 | +899 |
| `dababy` | 31 | 2984 | +2953 |
| `hikaru-nakamura` | 31 | 1715 | +1684 |
| `jesse-pinkman` | 31 | 3027 | +2996 |
| `leon` | 31 | 2047 | +2016 |
| `sam-harris` | 31 | 1195 | +1164 |
| `yoda` | 31 | 1478 | +1447 |
