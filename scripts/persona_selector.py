#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


SelectionMode = Literal["explicit", "auto", "random"]

METADATA_FIELDS = (
    "summary",
    "interaction_stance",
    "value_profile",
    "reasoning_style",
    "preferred_terminology",
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "in",
    "is",
    "it",
    "need",
    "not",
    "of",
    "or",
    "the",
    "this",
    "to",
    "with",
}


@dataclass(frozen=True)
class PersonaPack:
    id: str
    display_name: str
    summary: str
    voice: dict[str, str]
    interaction_stance: list[str]
    value_profile: list[str]
    reasoning_style: list[str]
    preferred_terminology: list[str]
    source_path: Path | None = None


@dataclass(frozen=True)
class PersonaSelectionRequest:
    mode: SelectionMode
    task: str
    context: str = ""
    persona_id: str | None = None
    seed: str | int | None = None
    include_ids: set[str] | None = None
    exclude_ids: set[str] | None = None


@dataclass(frozen=True)
class PersonaSelectionResult:
    persona_id: str
    rationale: str


class PersonaSelector:
    def __init__(self, packs: list[PersonaPack]) -> None:
        if not packs:
            raise ValueError("PersonaSelector requires at least one persona pack")
        self._packs = sorted(packs, key=lambda pack: pack.id)
        self._by_id = {pack.id: pack for pack in self._packs}
        if len(self._by_id) != len(self._packs):
            raise ValueError("persona pack ids must be unique")

    @classmethod
    def from_directory(cls, directory: Path) -> "PersonaSelector":
        paths = sorted(directory.glob("*.yaml"))
        if not paths:
            raise ValueError(f"no persona packs found in {directory}")
        return cls([load_pack(path) for path in paths])

    def select(self, request: PersonaSelectionRequest) -> PersonaSelectionResult:
        if request.mode == "explicit":
            return self._select_explicit(request)
        if request.mode == "random":
            return self._select_random(request)
        if request.mode == "auto":
            return self._select_auto(request)
        raise ValueError(f"unsupported persona selection mode: {request.mode}")

    def _select_explicit(self, request: PersonaSelectionRequest) -> PersonaSelectionResult:
        if not request.persona_id:
            raise ValueError("explicit persona selection requires persona_id")
        pack = self._by_id.get(request.persona_id)
        if pack is None:
            raise ValueError(f"unknown persona id: {request.persona_id}")
        return PersonaSelectionResult(
            persona_id=pack.id,
            rationale=f"explicit selection requested persona id {pack.id}",
        )

    def _select_random(self, request: PersonaSelectionRequest) -> PersonaSelectionResult:
        eligible = self._eligible_packs(request)
        if not eligible:
            raise ValueError("no persona packs match include/exclude filters")

        seed_material = str(request.seed) if request.seed is not None else request.task + "\n" + request.context
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        index = int(digest[:12], 16) % len(eligible)
        pack = eligible[index]
        return PersonaSelectionResult(
            persona_id=pack.id,
            rationale=(
                f"random selection used seed {seed_material!r} across "
                f"{len(eligible)} eligible persona packs after include/exclude filters"
            ),
        )

    def _select_auto(self, request: PersonaSelectionRequest) -> PersonaSelectionResult:
        eligible = self._eligible_packs(request)
        if not eligible:
            raise ValueError("no persona packs match include/exclude filters")

        query_tokens = tokenize(request.task + " " + request.context)
        scored = [(score_pack(pack, query_tokens), pack) for pack in eligible]
        scored.sort(key=lambda item: (-item[0].score, item[1].id))
        best_score, best_pack = scored[0]
        terms = ", ".join(best_score.matched_terms[:5]) if best_score.matched_terms else "no exact term overlap"
        return PersonaSelectionResult(
            persona_id=best_pack.id,
            rationale=(
                f"auto selection used metadata affinity from summary, stance, values, "
                f"reasoning, and terminology; matched {terms}"
            ),
        )

    def _eligible_packs(self, request: PersonaSelectionRequest) -> list[PersonaPack]:
        include_ids = request.include_ids
        exclude_ids = request.exclude_ids or set()
        return [
            pack
            for pack in self._packs
            if (include_ids is None or pack.id in include_ids) and pack.id not in exclude_ids
        ]


@dataclass(frozen=True)
class PackScore:
    score: int
    matched_terms: list[str]


def score_pack(pack: PersonaPack, query_tokens: set[str]) -> PackScore:
    metadata = metadata_text(pack)
    pack_tokens = tokenize(metadata)
    matched = sorted(query_tokens & pack_tokens)
    return PackScore(score=len(matched), matched_terms=matched)


def metadata_text(pack: PersonaPack) -> str:
    parts: list[str] = []
    for field in METADATA_FIELDS:
        value = getattr(pack, field)
        if isinstance(value, list):
            parts.extend(value)
        else:
            parts.append(value)
    return " ".join(parts)


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9][a-z0-9-]*", text.lower()))
    expanded: set[str] = set()
    for token in tokens:
        if token in STOPWORDS or len(token) < 3:
            continue
        expanded.add(token)
        expanded.update(part for part in token.split("-") if len(part) >= 3 and part not in STOPWORDS)
    return expanded


def load_pack(path: Path) -> PersonaPack:
    lines = path.read_text(encoding="utf-8").splitlines()
    data = parse_top_level_yaml(lines)
    return PersonaPack(
        id=required_scalar(data, "id", path),
        display_name=required_scalar(data, "display_name", path),
        summary=required_scalar(data, "summary", path),
        voice=dict(data.get("voice", {})),
        interaction_stance=list(data.get("interaction_stance", [])),
        value_profile=list(data.get("value_profile", [])),
        reasoning_style=list(data.get("reasoning_style", [])),
        preferred_terminology=list(data.get("preferred_terminology", [])),
        source_path=path,
    )


def required_scalar(data: dict[str, object], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}: missing scalar field {key}")
    return value


def parse_top_level_yaml(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.startswith(" ") or ":" not in line:
            index += 1
            continue
        key, raw_value = line.split(":", 1)
        raw_value = raw_value.strip()

        if raw_value:
            data[key] = raw_value
            index += 1
            continue

        nested, index = parse_nested_block(lines, index + 1)
        data[key] = nested
    return data


def parse_nested_block(lines: list[str], start: int) -> tuple[object, int]:
    items: list[str] = []
    mapping: dict[str, str] = {}
    index = start

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if not line.startswith(" "):
            break

        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip('"'))
        elif ":" in stripped and not items:
            key, value = stripped.split(":", 1)
            mapping[key] = value.strip().strip('"')
        index += 1

    if items:
        return items, index
    return mapping, index


if __name__ == "__main__":
    selector = PersonaSelector.from_directory(Path("src/assets/personalities"))
    result = selector.select(
        PersonaSelectionRequest(
            mode="auto",
            task="Choose a persona for a reasoning-heavy task with ambiguity.",
        )
    )
    print(f"{result.persona_id}: {result.rationale}")
