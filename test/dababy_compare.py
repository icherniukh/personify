#!/usr/bin/env python3
"""Compare DaBaby v1 vs v2 personality packs on the same prompts using Claude."""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_builder import load_packet

ROOT_DIR = Path(__file__).resolve().parents[1]
CORE_SKILL = ROOT_DIR / "src" / "skills" / "orchestrator-core" / "SKILL.md"
V1_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "dababy.yaml"
V2_PACK = ROOT_DIR / "src" / "assets" / "personalities" / "jesse-pinkman.yaml"

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

if OPENROUTER_KEY:
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    API_KEY = OPENROUTER_KEY
    MODEL = os.environ.get("OPENROUTER_MODEL", "x-ai/grok-4.20")
else:
    API_URL = "https://api.openai.com/v1/chat/completions"
    API_KEY = OPENAI_KEY or ""
    MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

TEST_PROMPTS = [
    {
        "id": "grind-advice",
        "label": "Why grind",
        "prompt": "Explain the importance of slow grind and dedication in poetic words but practically, and in less than 12 sentences",
    },
    {
        "id": "confidence-under-pressure",
        "label": "Confidence under criticism",
        "prompt": "My manager says my code isn't ready to ship. I've spent three weeks on it and I think it's solid. Who's right?",
    },
    # {
    #     "id": "decision",
    #     "label": "Direct decision",
    #     "prompt": "Should I refactor this messy codebase now, or ship the next feature first?",
    # },
]


def call_claude(system_prompt: str, user_prompt: str) -> str:
    if not API_KEY:
        raise SystemExit("No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY.")

    body = {
        "model": MODEL,
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
    choice = payload["choices"][0]
    finish_reason = choice.get("finish_reason", "unknown")
    content = (choice["message"].get("content") or "").strip()
    if not content:
        return f"[empty — finish_reason={finish_reason}]"
    return content


def wrap(text: str, width: int = 72, indent: str = "  ") -> str:
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(
                textwrap.wrap(
                    paragraph,
                    width=width,
                    initial_indent=indent,
                    subsequent_indent=indent,
                )
            )
    return "\n".join(lines)


def run() -> None:
    print(f"Loading packs from:\n  v1: {V1_PACK}\n  v2: {V2_PACK}\n")
    v1_packet = load_packet(CORE_SKILL, V1_PACK)
    v2_packet = load_packet(CORE_SKILL, V2_PACK)
    provider = "OpenRouter" if OPENROUTER_KEY else "OpenAI"
    print(f"Provider: {provider}")
    print(f"Model: {MODEL}")
    print("=" * 80)

    for case in TEST_PROMPTS:
        print(f"\n{'=' * 80}")
        print(f"PROMPT [{case['id']}]: {case['label']}")
        print(f"  \"{case['prompt']}\"")
        print(f"{'=' * 80}")

        print("\n--- V1 (existing pack) ---\n")
        v1_out = call_claude(v1_packet, case["prompt"])
        print(wrap(v1_out) if v1_out else "  [empty response]")

        time.sleep(2)

        print("\n--- V2 (new research-backed pack) ---\n")
        v2_out = call_claude(v2_packet, case["prompt"])
        print(wrap(v2_out) if v2_out else "  [empty response]")

        time.sleep(2)

    print(f"\n{'=' * 80}")
    print("done")


if __name__ == "__main__":
    run()
