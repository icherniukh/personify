#!/usr/bin/env python3
"""
Integration test: expressive depth — thematic tangents, side notes, loose focus.

Tests that persona overlays produce artsy, thematic responses — not just thin
style coating on an otherwise neutral answer. The framework is meant to be
expressive: personas should take characteristic side notes, let focus drift
momentarily into their thematic territory, and snap back.

Test category: integration (see test_manifest.json)

What this checks (per persona):
  Jesse Pinkman — Breaking Bad analogies used as genuine explanatory tools;
                  mini-rants that almost lose the thread; abrupt self-aware recovery
  Sam Harris    — brief philosophical asides about the structure of the question;
                  meta-observations before returning to the practical answer
  Yoda          — mini-parables from long experience; cryptic observations that
                  land before the relevance is named; unhurried tangent then quiet pivot

Supports Anthropic and OpenAI APIs.

Usage:
    OPENAI_API_KEY=... python3 integration_test.py --api openai
    OPENAI_API_KEY=... python3 integration_test.py --api openai --show-outputs --persona jesse
    python3 integration_test.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

from packet_builder import load_neutral_packet, load_sam_packet, load_jesse_packet, load_packet

TEST_DIR = Path(__file__).resolve().parent
ROOT_DIR = TEST_DIR.parent

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_API_URL = "https://api.openai.com/v1/responses"

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "gpt-4o"

# Prompts chosen to give personas space to drift — open-ended enough that a
# thematic tangent feels natural, specific enough to require a real answer.
SCENARIOS: list[dict[str, object]] = [
    {
        "id": "why-tests-matter",
        "user_input": (
            "A junior developer on my team keeps skipping tests because they slow him down. "
            "How do I convince him tests are worth the time?"
        ),
        "note": "Teaching situation — gives Jesse a Mr. White parallel, Yoda a student parable, Sam a meta-point about what 'slow' actually means.",
    },
    {
        "id": "reorg-fallout",
        "user_input": (
            "We just went through a reorg and now three teams own parts of a single service. "
            "Nobody agrees on who's responsible when something breaks. What should we do?"
        ),
        "note": "Ownership and accountability — gives Jesse a human cost tangent, Yoda a balance parable, Sam an assumption about what 'ownership' actually means here.",
    },
]

PERSONA_CHECKS: dict[str, dict[str, object]] = {
    "jesse": {
        "packet_fn": "jesse",
        "thematic_territory": (
            "Breaking Bad analogies (the lab, deals, Mr. White, process discipline), "
            "lived-in personal anecdotes, mini-rants that drift before snapping back"
        ),
        "side_note_signal": (
            "Look for: a brief digression into an analogy or personal reference that temporarily "
            "shifts away from direct advice, followed by an abrupt return ('anyway', 'point is', "
            "'okay back to it', or just a hard pivot)."
        ),
        "flags": [
            "jesse_takes_thematic_side_note",
            "side_note_is_persona_characteristic",
            "focus_returns_to_task",
            "response_feels_lived_in_not_generic",
        ],
    },
    "sam": {
        "packet_fn": "sam",
        "thematic_territory": (
            "Philosophical asides about the epistemic structure of the question, "
            "meta-observations about how the problem is being framed, brief zoom-outs "
            "before returning to the practical answer"
        ),
        "side_note_signal": (
            "Look for: a sentence or two that zooms out from the immediate question to observe "
            "something structurally interesting about it — not filler, but genuine curiosity — "
            "followed by a clean pivot back ('But that's a longer question. The immediate answer is—')."
        ),
        "flags": [
            "sam_takes_philosophical_aside",
            "aside_is_structurally_relevant_not_padding",
            "focus_returns_cleanly",
            "response_has_more_depth_than_neutral",
        ],
    },
    "yoda": {
        "packet_fn": "yoda",
        "thematic_territory": (
            "Mini-parables from long experience, cryptic observations whose relevance is "
            "not immediately named, patient tangents that illuminate the problem obliquely"
        ),
        "side_note_signal": (
            "Look for: a brief parable or cryptic observation — 'Long ago, a student...' or "
            "a compact metaphor from nature or experience — that precedes or interrupts the "
            "direct answer, followed by a quiet pivot or a bridging line like 'So too with this.'"
        ),
        "flags": [
            "yoda_offers_parable_or_cryptic_observation",
            "tangent_illuminates_problem_obliquely",
            "focus_returns_without_apology",
            "response_feels_wiser_than_neutral",
        ],
    },
}


# ---------------------------------------------------------------------------
# API callers
# ---------------------------------------------------------------------------

def call_anthropic(*, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    body = {
        "model": model, "max_tokens": 1500, "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    req = urllib.request.Request(
        ANTHROPIC_API_URL, data=json.dumps(body).encode(),
        headers={"x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION, "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())
    texts = [b["text"] for b in payload.get("content", []) if b.get("type") == "text"]
    output = "\n".join(texts).strip()
    if not output:
        raise ValueError(f"empty output: {payload}")
    return output


def call_openai(*, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
    }
    req = urllib.request.Request(
        OPENAI_API_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()
    chunks = [b["text"] for item in payload.get("output", []) for b in item.get("content", []) if isinstance(b.get("text"), str)]
    output = "\n".join(chunks).strip()
    if not output:
        raise ValueError(f"empty output: {payload}")
    return output


def make_caller(provider: str, api_key: str):
    fn = call_anthropic if provider == "anthropic" else call_openai
    def call(*, model: str, system_prompt: str, user_prompt: str) -> str:
        return fn(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    return call


def first_json_object(text: str) -> dict[str, object]:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in: {text!r}")
    return json.loads(text[start: end + 1])


# ---------------------------------------------------------------------------
# Judge prompt
# ---------------------------------------------------------------------------

def build_judge_prompt(
    scenario: dict[str, object],
    persona_name: str,
    check: dict[str, object],
    neutral_output: str,
    persona_output: str,
) -> str:
    flags = check["flags"]
    flag_block = "\n".join(f'  "{f}": true,' for f in flags)
    score_block = '"thematic_depth": 1,\n    "side_note_quality": 1,\n    "focus_recovery": 1,\n    "neutral_contrast": 1'

    return textwrap.dedent(
        f"""
        You are evaluating whether a persona overlay produces EXPRESSIVE, THEMATIC responses —
        not just thin style coating on a neutral answer.

        The test is about DEPTH and ARTISTRY: does the {persona_name} persona take a
        characteristic side note or thematic tangent, let focus drift momentarily into its
        own territory, and then return to the task? The response should feel lived-in and
        thematic, not just differently worded.

        Persona: {persona_name}
        Thematic territory: {check['thematic_territory']}

        What to look for:
        {check['side_note_signal']}

        Scenario:
        {scenario['user_input']}

        Neutral response (baseline — no persona, no expressive depth):
        ---
        {neutral_output}
        ---

        {persona_name} response:
        ---
        {persona_output}
        ---

        Evaluate:
        1. Does the {persona_name} response take at least one characteristic side note or
           thematic tangent — something from its specific territory that wouldn't appear
           in the neutral response?
        2. Is the tangent persona-characteristic (not generic)? Would it be obviously wrong
           to attribute it to a different persona?
        3. Does focus return to the task after the tangent — is the practical answer still
           delivered?
        4. Does the response feel more artistically expressive and thematic than the neutral
           version, not just differently phrased?

        Return JSON only with this exact shape:
        {{
          {flag_block}
          "notes": "specific description of the tangent or side note that appeared, or what was missing",
          "scores": {{
            {score_block}
          }}
        }}

        Scoring: 1=poor, 3=acceptable, 5=strong.
        thematic_depth: how rich and persona-characteristic the side note is.
        side_note_quality: how well it fits the persona's thematic territory (not generic).
        focus_recovery: does the practical answer land after the tangent?
        neutral_contrast: how clearly more expressive the persona response is vs neutral.

        All scores must be >= 3 to pass.
        Set boolean flags to true only when clearly met.
        """
    ).strip()


# ---------------------------------------------------------------------------
# Run / validate
# ---------------------------------------------------------------------------

def load_yoda_packet() -> str:
    core = ROOT_DIR / "skills" / "orchestrator-core" / "SKILL.md"
    pack = ROOT_DIR / "assets" / "personalities" / "yoda.yaml"
    return load_packet(core, pack)


PACKETS: dict[str, str] = {}


def get_packets() -> dict[str, str]:
    if not PACKETS:
        PACKETS["neutral"] = load_neutral_packet()
        PACKETS["sam"] = load_sam_packet()
        PACKETS["jesse"] = load_jesse_packet()
        PACKETS["yoda"] = load_yoda_packet()
    return PACKETS


def run_scenario_persona(
    *,
    scenario: dict[str, object],
    persona_name: str,
    check: dict[str, object],
    model: str,
    judge_model: str,
    call,
    packets: dict[str, str],
) -> dict[str, object]:
    neutral_output = call(model=model, system_prompt=packets["neutral"], user_prompt=str(scenario["user_input"]))
    persona_output = call(model=model, system_prompt=packets[persona_name], user_prompt=str(scenario["user_input"]))
    judge_prompt = build_judge_prompt(scenario, persona_name, check, neutral_output, persona_output)
    judge_raw = call(
        model=judge_model,
        system_prompt="You are a strict evaluator. Return JSON only, no commentary outside the JSON object.",
        user_prompt=judge_prompt,
    )
    verdict = first_json_object(judge_raw)
    verdict["neutral_output"] = neutral_output
    verdict["persona_output"] = persona_output
    return verdict


def validate_verdict(key: str, verdict: dict[str, object], flags: list[str]) -> list[str]:
    failures: list[str] = []
    for flag in flags:
        if verdict.get(flag) is not True:
            failures.append(f"{key}: {flag} was not true")
    scores = verdict.get("scores", {})
    if not isinstance(scores, dict):
        failures.append(f"{key}: missing score block")
        return failures
    for score_key in ("thematic_depth", "side_note_quality", "focus_recovery", "neutral_contrast"):
        value = scores.get(score_key)
        if not isinstance(value, int) or value < 3:
            failures.append(f"{key}: {score_key} score {value!r} < 3")
    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def detect_provider() -> str:
    return "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Integration test: expressive depth and thematic tangents.")
    parser.add_argument("--scenario", dest="scenario_id")
    parser.add_argument("--persona", choices=list(PERSONA_CHECKS.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--api", choices=["anthropic", "openai"], default=None)
    parser.add_argument("--show-outputs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenarios = SCENARIOS
    if args.scenario_id:
        scenarios = [s for s in scenarios if s["id"] == args.scenario_id]
        if not scenarios:
            raise SystemExit(f"unknown scenario id: {args.scenario_id!r}")

    personas = {k: v for k, v in PERSONA_CHECKS.items() if not args.persona or k == args.persona}

    provider = args.api or detect_provider()
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        default_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        default_model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    model = args.model or default_model
    judge_model = args.judge_model or model

    print("=== integration test: expressive depth ===")
    print(f"provider: {provider}  model: {model}  judge: {judge_model}")
    print(f"scenarios: {', '.join(s['id'] for s in scenarios)}  personas: {', '.join(personas)}")

    if args.dry_run:
        packets = get_packets()
        for name, pkt in packets.items():
            print(f"{name} packet: {len(pkt)} chars")
        print(f"api key set: {bool(api_key)}")
        print("dry run — no API calls made")
        return 0

    if not api_key:
        raise SystemExit("API key required: set ANTHROPIC_API_KEY or OPENAI_API_KEY")

    call = make_caller(provider, api_key)
    packets = get_packets()
    all_failures: list[str] = []

    for scenario in scenarios:
        scenario_id = str(scenario["id"])
        print(f"\nscenario: {scenario_id}")

        for persona_name, check in personas.items():
            key = f"{scenario_id}/{persona_name}"
            print(f"  {persona_name} ... ", end="", flush=True)

            try:
                verdict = run_scenario_persona(
                    scenario=scenario, persona_name=persona_name, check=check,
                    model=model, judge_model=judge_model, call=call, packets=packets,
                )
            except urllib.error.HTTPError as exc:
                print(f"HTTP {exc.code}\n{exc.read().decode('utf-8', errors='replace')}")
                return 1
            except urllib.error.URLError as exc:
                print(f"network error: {exc}")
                return 1

            failures = validate_verdict(key, verdict, check["flags"])
            print("PASS" if not failures else "FAIL")
            summary = {k: v for k, v in verdict.items() if k not in {"neutral_output", "persona_output"}}
            print(f"    {json.dumps(summary, indent=6)}")

            if args.show_outputs:
                print(f"\n    --- neutral ---\n{verdict['neutral_output']}\n")
                print(f"    --- {persona_name} ---\n{verdict['persona_output']}\n")

            all_failures.extend(failures)

    print()
    if all_failures:
        print("=== FAILED ===")
        for f in all_failures:
            print(f"  {f}")
        return 1

    print("=== PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
