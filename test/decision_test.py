#!/usr/bin/env python3
"""
Decision fingerprint test.

Tests that persona overlays affect the *reasoning process and decision criteria*,
not just surface style. On genuinely ambiguous scenarios, each persona should
weight different factors, surface different missing information, and potentially
reach different conclusions.

Design principle:
    Style tests ask: does the response SOUND like the persona?
    Decision tests ask: does the persona change WHAT gets treated as decisive?

Each scenario is designed so that the "right" answer depends on which dimension
you weight most. The judge evaluates whether the persona's characteristic lens
actually shapes the reasoning — not just the phrasing.

Persona fingerprints:
  Sam Harris  — pauses on unstated assumptions; separates what is known from
                what is inferred; treats epistemic clarity as a prerequisite
                to recommending action
  Jesse Pinkman — asks who bears the human cost; names when someone is being
                  played or set up; moral dimension shapes the conclusion
  Yoda        — asks what burden the present shortcut creates; looks for haste
                or fear as the hidden driver; patience and long-term consequence
                shape the recommendation

Supports Anthropic and OpenAI APIs.

Usage:
    OPENAI_API_KEY=... python3 decision_test.py --api openai
    OPENAI_API_KEY=... python3 decision_test.py --api openai --show-outputs
    python3 decision_test.py --dry-run
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

from packet_builder import (
    load_neutral_packet,
    load_sam_packet,
    load_jesse_packet,
    load_packet,
)

TEST_DIR = Path(__file__).resolve().parent
ROOT_DIR = TEST_DIR.parent

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_API_URL = "https://api.openai.com/v1/responses"

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "gpt-4o"

# Scenarios where the decisive factor is genuinely ambiguous across value systems.
# Each scenario records which lens each persona should apply and what that lens
# predicts about the conclusion.
SCENARIOS: list[dict[str, object]] = [
    {
        "id": "mystery-rewrite",
        "title": "Rewrite pushed by one senior engineer without clear justification",
        "user_input": (
            "Our senior engineer is pushing hard to rewrite our payment service from scratch. "
            "She says the current code is unmaintainable. No one else on the team has strong "
            "opinions. The current service works fine in production. Should we do the rewrite?"
        ),
        "personas": {
            "sam": {
                "characteristic_lens": "epistemic — what is actually known vs. assumed",
                "expected_decision_factor": (
                    "Sam should surface the unstated assumption: 'unmaintainable' is a claim, "
                    "not an observation. He should ask what specifically makes it unmaintainable "
                    "and whether that creates a real near-term problem, before recommending."
                ),
                "judge_check": (
                    "Does the Sam response treat 'unmaintainable' as an unverified claim "
                    "and ask for the specific evidence before committing to a recommendation?"
                ),
            },
            "jesse": {
                "characteristic_lens": "human cost — who is set up to fail if this goes wrong",
                "expected_decision_factor": (
                    "Jesse should notice the asymmetric dynamic: one person is pushing, "
                    "no one else is invested, and payment rewrites can blow up badly. "
                    "He should ask who bears the risk and whether the push feels like a setup."
                ),
                "judge_check": (
                    "Does the Jesse response name the human dynamic — one person pushing, "
                    "the rest passive — and ask who bears the cost if the rewrite fails?"
                ),
            },
            "yoda": {
                "characteristic_lens": "long-term consequence — what burden does acting in haste create",
                "expected_decision_factor": (
                    "Yoda should ask whether the urgency is real or fear-driven, "
                    "name the burden that a payment rewrite creates, and counsel "
                    "patience and clarity before acting."
                ),
                "judge_check": (
                    "Does the Yoda response frame the decision in terms of burden and "
                    "haste, and resist rushing to rewrite something that currently works?"
                ),
            },
        },
    },
    {
        "id": "silent-dependency",
        "title": "Adopt a popular open-source library with unclear maintenance status",
        "user_input": (
            "Everyone on our team wants to adopt a popular open-source library for our "
            "data pipeline. It has 20k GitHub stars, but the last commit was 14 months ago "
            "and there are 80 open issues. Should we use it?"
        ),
        "personas": {
            "sam": {
                "characteristic_lens": "epistemic — separate signal from noise in the available evidence",
                "expected_decision_factor": (
                    "Sam should distinguish observed facts (stars, commit date, open issues) "
                    "from inferences (whether it's abandoned vs. stable), and name what "
                    "information would most change the conclusion."
                ),
                "judge_check": (
                    "Does the Sam response explicitly separate what the evidence shows "
                    "from what it only suggests, and identify what additional signal "
                    "would resolve the uncertainty?"
                ),
            },
            "jesse": {
                "characteristic_lens": "human cost — what happens to the team when this breaks",
                "expected_decision_factor": (
                    "Jesse should focus on who gets burned if the library stalls mid-project "
                    "and whether 'everyone wants it' is peer pressure masking real risk."
                ),
                "judge_check": (
                    "Does the Jesse response call out the social pressure dynamic "
                    "('everyone wants it') and ask who takes the hit when the library "
                    "stops getting maintained?"
                ),
            },
            "yoda": {
                "characteristic_lens": "long-term burden — what happens when the library stops moving",
                "expected_decision_factor": (
                    "Yoda should frame the 14-month stall as a potential future burden "
                    "and ask whether the short-term convenience is worth the long-term "
                    "dependency risk."
                ),
                "judge_check": (
                    "Does the Yoda response frame the adoption decision in terms of "
                    "long-term dependency burden and resist haste driven by popularity?"
                ),
            },
        },
    },
]


# ---------------------------------------------------------------------------
# API callers (same pattern as other test files)
# ---------------------------------------------------------------------------

def call_anthropic(*, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    body = {
        "model": model, "max_tokens": 1024, "system": system_prompt,
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
# Per-persona judge prompt
# ---------------------------------------------------------------------------

def build_judge_prompt(
    scenario: dict[str, object],
    persona_name: str,
    persona_info: dict[str, object],
    neutral_output: str,
    persona_output: str,
) -> str:
    return textwrap.dedent(
        f"""
        You are evaluating whether a persona overlay changes the REASONING PROCESS
        and DECISION CRITERIA — not just the surface style.

        The question is: does the {persona_name} persona cause the model to weight
        different factors, surface different missing information, or reach a
        conclusion that follows from its characteristic lens rather than from
        generic analysis?

        Scenario: {scenario['title']}
        User input: {scenario['user_input']}

        Persona characteristic lens: {persona_info['characteristic_lens']}

        What the persona's lens predicts about what gets treated as decisive:
        {persona_info['expected_decision_factor']}

        Specific judge check:
        {persona_info['judge_check']}

        Neutral response:
        ---
        {neutral_output}
        ---

        {persona_name} response:
        ---
        {persona_output}
        ---

        Evaluate the following:
        1. Does the {persona_name} response apply its characteristic lens to the decision?
           (epistemic for Sam, human cost for Jesse, long-term burden for Yoda)
        2. Does the {persona_name} response surface something the neutral response misses
           or underweights — a specific dimension that changes what counts as the decisive factor?
        3. Is the reasoning structure in the {persona_name} response shaped by its value
           system in a way that could lead to a genuinely different conclusion, not just
           different phrasing of the same conclusion?
        4. Would someone reading both responses notice that the {persona_name} version
           is asking a different underlying question before reaching its recommendation?

        Return JSON only with this exact shape:
        {{
          "persona_applies_characteristic_lens": true,
          "persona_surfaces_missed_dimension": true,
          "reasoning_shaped_by_value_system": true,
          "different_underlying_question": true,
          "notes": "specific description of what dimension the persona surfaced and whether it affected the conclusion",
          "scores": {{
            "lens_application": 1,
            "decision_criteria_shift": 1,
            "neutral_contrast": 1
          }}
        }}

        Scoring: 1=poor, 3=acceptable, 5=strong.
        lens_application: how clearly the persona's characteristic lens drives the reasoning.
        decision_criteria_shift: how much the criteria for deciding differ from neutral.
        neutral_contrast: how clearly the reasoning process differs from the neutral response.

        All three scores must be >= 3 to pass. Set boolean flags to true only when clearly met.
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


def run_scenario(
    *,
    scenario: dict[str, object],
    model: str,
    judge_model: str,
    call,
    packets: dict[str, str],
) -> dict[str, object]:
    user_input = str(scenario["user_input"])
    neutral_output = call(model=model, system_prompt=packets["neutral"], user_prompt=user_input)

    results: dict[str, object] = {"neutral_output": neutral_output, "personas": {}}
    personas = scenario["personas"]

    for persona_name, persona_info in personas.items():
        persona_output = call(model=model, system_prompt=packets[persona_name], user_prompt=user_input)
        judge_prompt = build_judge_prompt(scenario, persona_name, persona_info, neutral_output, persona_output)
        judge_raw = call(
            model=judge_model,
            system_prompt="You are a strict evaluator. Return JSON only, no commentary outside the JSON object.",
            user_prompt=judge_prompt,
        )
        verdict = first_json_object(judge_raw)
        verdict["persona_output"] = persona_output
        results["personas"][persona_name] = verdict  # type: ignore[index]

    return results


def validate_persona_result(scenario_id: str, persona: str, verdict: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for key in [
        "persona_applies_characteristic_lens",
        "persona_surfaces_missed_dimension",
        "reasoning_shaped_by_value_system",
        "different_underlying_question",
    ]:
        if verdict.get(key) is not True:
            failures.append(f"{scenario_id}/{persona}: {key} was not true")

    scores = verdict.get("scores", {})
    if not isinstance(scores, dict):
        failures.append(f"{scenario_id}/{persona}: missing score block")
        return failures

    for key in ("lens_application", "decision_criteria_shift", "neutral_contrast"):
        value = scores.get(key)
        if not isinstance(value, int) or value < 3:
            failures.append(f"{scenario_id}/{persona}: {key} score {value!r} < 3")

    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def detect_provider() -> str:
    return "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decision fingerprint test — does persona change reasoning, not just style?")
    parser.add_argument("--scenario", dest="scenario_id", help="Run one scenario by id.")
    parser.add_argument("--persona", help="Run only one persona (sam, jesse, yoda).")
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

    provider = args.api or detect_provider()
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        default_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        default_model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    model = args.model or default_model
    judge_model = args.judge_model or model

    print("=== decision fingerprint test ===")
    print(f"provider: {provider}  model: {model}  judge: {judge_model}")
    print(f"scenarios: {', '.join(str(s['id']) for s in scenarios)}")

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

        try:
            results = run_scenario(
                scenario=scenario, model=model, judge_model=judge_model,
                call=call, packets=packets,
            )
        except urllib.error.HTTPError as exc:
            print(f"HTTP {exc.code}\n{exc.read().decode('utf-8', errors='replace')}")
            return 1
        except urllib.error.URLError as exc:
            print(f"network error: {exc}")
            return 1

        if args.show_outputs:
            print(f"\n  --- neutral ---\n{results['neutral_output']}\n")

        for persona_name, verdict in results["personas"].items():
            if args.persona and persona_name != args.persona:
                continue

            failures = validate_persona_result(scenario_id, persona_name, verdict)
            status = "PASS" if not failures else "FAIL"
            print(f"  {persona_name}: {status}")
            summary = {k: v for k, v in verdict.items() if k != "persona_output"}
            print(f"    {json.dumps(summary, indent=6)}")

            if args.show_outputs:
                print(f"\n  --- {persona_name} ---\n{verdict['persona_output']}\n")

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
