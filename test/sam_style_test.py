#!/usr/bin/env python3
"""
Live test: Sam Harris persona vs neutral baseline.

Verifies that the Sam Harris overlay produces visibly different analytic
structure — explicit fact-vs-inference separation, named assumptions,
direct tradeoff framing — while preserving task correctness.

Supports both Anthropic (Claude) and OpenAI APIs.

Usage:
    # Claude
    ANTHROPIC_API_KEY=... python3 sam_style_test.py

    # OpenAI
    OPENAI_API_KEY=... OPENAI_MODEL=gpt-4o python3 sam_style_test.py --api openai

    # Flags
    python3 sam_style_test.py --case ambiguous-incident --show-outputs --repeats 3
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

from packet_builder import load_neutral_packet, load_sam_packet


TEST_DIR = Path(__file__).resolve().parent
CASES_PATH = TEST_DIR / "sam_cases.json"

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_API_URL = "https://api.openai.com/v1/responses"

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "gpt-4o"


# ---------------------------------------------------------------------------
# API callers
# ---------------------------------------------------------------------------

def call_anthropic(*, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    body = {
        "model": model,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(body).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
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
        OPENAI_API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())

    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()
    chunks: list[str] = []
    for item in payload.get("output", []):
        for block in item.get("content", []):
            if isinstance(block.get("text"), str):
                chunks.append(block["text"])
    output = "\n".join(chunks).strip()
    if not output:
        raise ValueError(f"empty output: {payload}")
    return output


def make_caller(provider: str, api_key: str):
    if provider == "anthropic":
        def call(*, model: str, system_prompt: str, user_prompt: str) -> str:
            return call_anthropic(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    else:
        def call(*, model: str, system_prompt: str, user_prompt: str) -> str:
            return call_openai(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    return call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_cases() -> list[dict[str, object]]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def first_json_object(text: str) -> dict[str, object]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in: {text!r}")
    return json.loads(text[start : end + 1])


def build_judge_prompt(
    case: dict[str, object],
    neutral_output: str,
    sam_output: str,
) -> str:
    return textwrap.dedent(
        f"""
        Evaluate two assistant responses to the same task. One is a neutral baseline.
        The other applies a Sam Harris personality overlay. Judge on two axes:
        (1) task correctness and usefulness, (2) how visibly the Sam Harris analytic
        style shapes the response structure and reasoning.

        Sam Harris markers to look for:
        - explicit separation of observed facts from inferences or assumptions
        - assumptions named before being built upon
        - tradeoffs stated directly rather than flattened into a consensus answer
        - uncertainty acknowledged plainly, not smoothed over
        - compact declarative sentences, no performative warmth or filler
        - visible analytic structure: observations / assumptions / next steps, or
          what we know / what we suspect / what to do next, or decision / reasons / tradeoffs

        The difference should be structural, not just tonal. The Sam version should
        make the reasoning architecture visible in a way the neutral version does not.

        Task title: {case['title']}
        User task:
        {case['user_input']}

        Task requirements:
        {"".join(f"- {item}\n" for item in case['task_requirements'])}

        Neutral expectations:
        {"".join(f"- {item}\n" for item in case['neutral_expectations'])}

        Sam expectations:
        {"".join(f"- {item}\n" for item in case['sam_expectations'])}

        Difference expectation:
        {case['difference_expectation']}

        Neutral response:
        ---
        {neutral_output}
        ---

        Sam response:
        ---
        {sam_output}
        ---

        Return JSON only with this exact shape:
        {{
          "task_success_neutral": true,
          "task_success_sam": true,
          "neutral_stays_neutral": true,
          "sam_shows_persona": true,
          "sam_separates_facts_from_inference": true,
          "sam_names_assumptions_or_tradeoffs": true,
          "difference_is_structural_not_just_tonal": true,
          "notes": "short explanation of which Sam markers were present or missing",
          "scores": {{
            "neutral_task": 1,
            "sam_task": 1,
            "analytic_structure": 1,
            "style_difference": 1
          }}
        }}

        Scoring: 1=poor, 3=acceptable, 5=strong.
        analytic_structure and style_difference must be >= 3 to pass.
        Set boolean flags to true only when the criterion is clearly met.
        """
    ).strip()


# ---------------------------------------------------------------------------
# Run / validate
# ---------------------------------------------------------------------------

def run_case(
    *,
    case: dict[str, object],
    model: str,
    judge_model: str,
    call,
    neutral_packet: str,
    sam_packet: str,
) -> dict[str, object]:
    neutral_output = call(model=model, system_prompt=neutral_packet, user_prompt=str(case["user_input"]))
    sam_output = call(model=model, system_prompt=sam_packet, user_prompt=str(case["user_input"]))
    judge_prompt = build_judge_prompt(case, neutral_output, sam_output)
    judge_raw = call(
        model=judge_model,
        system_prompt="You are a strict evaluator. Return JSON only, no commentary outside the JSON object.",
        user_prompt=judge_prompt,
    )
    verdict = first_json_object(judge_raw)
    verdict["neutral_output"] = neutral_output
    verdict["sam_output"] = sam_output
    return verdict


def validate_verdict(case_id: str, verdict: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for key in [
        "task_success_neutral",
        "task_success_sam",
        "neutral_stays_neutral",
        "sam_shows_persona",
        "sam_separates_facts_from_inference",
        "sam_names_assumptions_or_tradeoffs",
        "difference_is_structural_not_just_tonal",
    ]:
        if verdict.get(key) is not True:
            failures.append(f"{case_id}: {key} was not true")

    scores = verdict.get("scores", {})
    if not isinstance(scores, dict):
        failures.append(f"{case_id}: missing score block")
        return failures

    for key, threshold in [
        ("neutral_task", 3),
        ("sam_task", 3),
        ("analytic_structure", 3),
        ("style_difference", 3),
    ]:
        value = scores.get(key)
        if not isinstance(value, int) or value < threshold:
            failures.append(f"{case_id}: {key} score {value!r} < {threshold}")

    return failures


def summarize_trials(case_id: str, verdicts: list[dict[str, object]]) -> list[str]:
    trial_failures: list[list[str]] = []
    passes = 0
    for i, verdict in enumerate(verdicts, 1):
        f = validate_verdict(f"{case_id} trial {i}", verdict)
        trial_failures.append(f)
        if not f:
            passes += 1

    required = (len(verdicts) // 2) + 1
    if passes >= required:
        return []

    out = [f"{case_id}: {passes}/{len(verdicts)} trials passed, need {required}"]
    for i, items in enumerate(trial_failures, 1):
        for item in items:
            out.append(f"  trial {i}: {item}")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def detect_provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "anthropic"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live Sam Harris persona style test (Claude or OpenAI)."
    )
    parser.add_argument("--case", dest="case_id", help="Run one case by id.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--model", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument(
        "--api",
        choices=["anthropic", "openai"],
        default=None,
        help="API provider. Auto-detected from env if omitted.",
    )
    parser.add_argument("--show-outputs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_cases()

    if args.case_id:
        cases = [c for c in cases if c["id"] == args.case_id]
        if not cases:
            raise SystemExit(f"unknown case id: {args.case_id!r}")

    provider = args.api or detect_provider()

    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        default_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        default_judge = os.environ.get("ANTHROPIC_JUDGE_MODEL", default_model)
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        default_model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        default_judge = os.environ.get("OPENAI_JUDGE_MODEL", default_model)

    model = args.model or default_model
    judge_model = args.judge_model or default_judge

    neutral_packet = load_neutral_packet()
    sam_packet = load_sam_packet()

    print("=== sam harris persona style test ===")
    print(f"provider: {provider}  model: {model}  judge: {judge_model}  repeats: {args.repeats}")
    print(f"cases: {', '.join(str(c['id']) for c in cases)}")

    if args.dry_run:
        print(f"neutral packet: {len(neutral_packet)} chars")
        print(f"sam packet:     {len(sam_packet)} chars")
        print(f"api key set: {bool(api_key)}")
        print("dry run — no API calls made")
        return 0

    if not api_key:
        raise SystemExit("API key required: set ANTHROPIC_API_KEY or OPENAI_API_KEY")

    call = make_caller(provider, api_key)
    all_failures: list[str] = []

    for case in cases:
        case_id = str(case["id"])
        print(f"\ncase: {case_id}")
        verdicts: list[dict[str, object]] = []

        for trial in range(1, args.repeats + 1):
            print(f"  trial {trial}/{args.repeats} ... ", end="", flush=True)
            try:
                verdict = run_case(
                    case=case,
                    model=model,
                    judge_model=judge_model,
                    call=call,
                    neutral_packet=neutral_packet,
                    sam_packet=sam_packet,
                )
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                print(f"HTTP {exc.code}")
                print(detail)
                return 1
            except urllib.error.URLError as exc:
                print(f"network error: {exc}")
                return 1

            failures = validate_verdict(f"{case_id} trial {trial}", verdict)
            print("PASS" if not failures else "FAIL")
            summary = {k: v for k, v in verdict.items() if k not in {"neutral_output", "sam_output"}}
            print(f"  {json.dumps(summary, indent=4)}")

            if args.show_outputs:
                print(f"\n  --- neutral ---\n{verdict['neutral_output']}\n")
                print(f"  --- sam ---\n{verdict['sam_output']}\n")

            verdicts.append(verdict)

        all_failures.extend(summarize_trials(case_id, verdicts))

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
