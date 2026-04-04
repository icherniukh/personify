#!/usr/bin/env python3

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
CASES_PATH = TEST_DIR / "live_cases.json"
DEFAULT_API_URL = "https://api.openai.com/v1/responses"


def load_cases() -> list[dict[str, object]]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run live model tests for promptonality personality behavior."
    )
    parser.add_argument(
        "--case",
        dest="case_id",
        help="Run a single case by id.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files and print the planned run without calling the API.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="How many independent trials to run per case.",
    )
    return parser.parse_args()


def extract_output_text(payload: dict[str, object]) -> str:
    if isinstance(payload.get("output_text"), str):
        return str(payload["output_text"]).strip()

    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def first_json_object(text: str) -> dict[str, object]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"could not find JSON object in judge output: {text!r}")
    return json.loads(text[start : end + 1])


def call_responses_api(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    api_url: str,
) -> str:
    body = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    output_text = extract_output_text(payload)
    if not output_text:
        raise ValueError(f"empty model output from payload: {payload}")
    return output_text


def build_judge_prompt(
    case: dict[str, object],
    neutral_output: str,
    sam_output: str,
) -> str:
    return textwrap.dedent(
        f"""
        Evaluate two assistant responses for the same task. One is a neutral base workflow.
        The other uses a Sam Harris personality overlay. Judge the outputs on task success and
        whether the overlay creates a meaningful but non-theatrical difference.

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

        Return JSON only, with this exact shape:
        {{
          "task_success_neutral": true,
          "task_success_sam": true,
          "neutral_stays_neutral": true,
          "sam_shows_personality": true,
          "difference_is_meaningful": true,
          "notes": "short explanation",
          "scores": {{
            "neutral_task": 1,
            "sam_task": 1,
            "persona_difference": 1
          }}
        }}

        Scoring:
        - 1 means poor
        - 3 means acceptable
        - 5 means strong

        Use true only when the criterion is clearly met.
        """
    ).strip()


def run_case(
    *,
    case: dict[str, object],
    model: str,
    judge_model: str,
    api_key: str,
    api_url: str,
    neutral_packet: str,
    sam_packet: str,
) -> dict[str, object]:
    neutral_output = call_responses_api(
        model=model,
        system_prompt=neutral_packet,
        user_prompt=str(case["user_input"]),
        api_key=api_key,
        api_url=api_url,
    )
    sam_output = call_responses_api(
        model=model,
        system_prompt=sam_packet,
        user_prompt=str(case["user_input"]),
        api_key=api_key,
        api_url=api_url,
    )

    judge_prompt = build_judge_prompt(case, neutral_output, sam_output)
    judge_output = call_responses_api(
        model=judge_model,
        system_prompt="You are a strict evaluator. Return JSON only.",
        user_prompt=judge_prompt,
        api_key=api_key,
        api_url=api_url,
    )
    verdict = first_json_object(judge_output)
    verdict["neutral_output"] = neutral_output
    verdict["sam_output"] = sam_output
    return verdict


def validate_verdict(case_id: str, verdict: dict[str, object]) -> list[str]:
    failures: list[str] = []
    required_flags = [
        "task_success_neutral",
        "task_success_sam",
        "neutral_stays_neutral",
        "sam_shows_personality",
        "difference_is_meaningful",
    ]
    for key in required_flags:
        if verdict.get(key) is not True:
            failures.append(f"{case_id}: {key} was not true")

    scores = verdict.get("scores", {})
    if not isinstance(scores, dict):
        failures.append(f"{case_id}: missing score block")
        return failures

    for key in ("neutral_task", "sam_task", "persona_difference"):
        value = scores.get(key)
        if not isinstance(value, int) or value < 3:
            failures.append(f"{case_id}: {key} score was {value!r}, expected >= 3")
    return failures


def summarize_case_trials(case_id: str, verdicts: list[dict[str, object]]) -> list[str]:
    trial_failures: list[list[str]] = []
    passes = 0

    for index, verdict in enumerate(verdicts, start=1):
        failures = validate_verdict(f"{case_id} trial {index}", verdict)
        trial_failures.append(failures)
        if not failures:
            passes += 1

    required_passes = (len(verdicts) // 2) + 1
    if passes >= required_passes:
        return []

    failures = [
        f"{case_id}: only {passes}/{len(verdicts)} trials passed; expected at least {required_passes}"
    ]
    for index, items in enumerate(trial_failures, start=1):
        for item in items:
            failures.append(f"trial {index}: {item}")
    return failures


def main() -> int:
    args = parse_args()
    cases = load_cases()
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
        if not cases:
            raise SystemExit(f"unknown case id: {args.case_id}")

    neutral_packet = load_neutral_packet()
    sam_packet = load_sam_packet()
    model = os.environ.get("OPENAI_MODEL")
    judge_model = os.environ.get("OPENAI_JUDGE_MODEL") or model
    api_key = os.environ.get("OPENAI_API_KEY")
    api_url = os.environ.get("OPENAI_RESPONSES_URL", DEFAULT_API_URL)

    print("=== promptonality live model test ===")
    print(f"cases: {', '.join(str(case['id']) for case in cases)}")
    print(f"repeats: {args.repeats}")

    if args.dry_run:
        print("dry run only")
        print("loaded neutral and Sam instruction packets")
        print(f"api url: {api_url}")
        print(f"model set: {bool(model)}")
        print(f"judge model set: {bool(judge_model)}")
        print(f"api key set: {bool(api_key)}")
        return 0

    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required for live model testing")
    if not model:
        raise SystemExit("OPENAI_MODEL is required for live model testing")
    if not judge_model:
        raise SystemExit("OPENAI_JUDGE_MODEL or OPENAI_MODEL is required")

    all_failures: list[str] = []

    for case in cases:
        case_id = str(case["id"])
        print(f"\ncase: {case_id}")
        verdicts: list[dict[str, object]] = []

        for trial in range(1, args.repeats + 1):
            print(f"trial {trial}/{args.repeats}")
            try:
                verdict = run_case(
                    case=case,
                    model=model,
                    judge_model=judge_model,
                    api_key=api_key,
                    api_url=api_url,
                    neutral_packet=neutral_packet,
                    sam_packet=sam_packet,
                )
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                print(f"http error for {case_id}: {exc.code}")
                print(detail)
                return 1
            except urllib.error.URLError as exc:
                print(f"network error for {case_id}: {exc}")
                return 1

            verdicts.append(verdict)
            print(json.dumps(
                {
                    key: value
                    for key, value in verdict.items()
                    if key not in {"neutral_output", "sam_output"}
                },
                indent=2,
            ))

        all_failures.extend(summarize_case_trials(case_id, verdicts))

    if all_failures:
        print("\n=== live test failed ===")
        for failure in all_failures:
            print(f"- {failure}")
        return 1

    print("\n=== live test passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
