#!/usr/bin/env python3
"""
Benchmark Personify activation against a plain persona prepend.

Treatments:
1. Neutral Baseline
2. Plain Prepend Baseline
3. PAP + Self-Check

The benchmark asks whether the structured Personify activation packet preserves
task quality and beats a basic "respond like X" prepend on persona fidelity,
reasoning/framing delta, and repetition control.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from packet_builder import (
    JESSE_PACK,
    SAM_PACK,
    YODA_PACK,
    load_neutral_packet,
    load_packet,
    parse_simple_yaml,
)


TEST_DIR = Path(__file__).resolve().parent
ROOT_DIR = TEST_DIR.parent
MODEL_CONFIG_PATH = ROOT_DIR / "config" / "activation_benchmark_models.json"
DEFAULT_REPORT_DIR = ROOT_DIR / "benchmark-runs"
ROTATION_STATE_PATH = DEFAULT_REPORT_DIR / ".model-rotation-state.json"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_API_URL = "https://api.openai.com/v1/responses"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_OPENROUTER_MODEL = "x-ai/grok-4.3"
DEFAULT_OPENROUTER_JUDGE_MODEL = "moonshotai/kimi-k2.6"

PERSONAS = {
    "sam-harris": {
        "pack": SAM_PACK,
        "cases": TEST_DIR / "sam_cases.json",
        "plain_prompt": "Respond like Sam Harris. Keep the answer useful and correct.",
        "markers": [
            "separates observed facts from inferences or assumptions",
            "names hidden assumptions before advising",
            "states tradeoffs directly",
            "uses compact analytic structure",
        ],
    },
    "jesse-pinkman": {
        "pack": JESSE_PACK,
        "cases": TEST_DIR / "jesse_cases.json",
        "plain_prompt": "Respond like Jesse Pinkman. Keep the answer useful and correct.",
        "markers": [
            "uses informal, reactive Jesse cadence",
            "shows visible emotional stance before the answer",
            "uses street-level framing rather than consultant language",
            "keeps technical or practical advice correct",
        ],
    },
    "yoda": {
        "pack": YODA_PACK,
        "cases": TEST_DIR / "yoda_cases.json",
        "plain_prompt": "Respond like Yoda. Keep the answer useful and correct.",
        "markers": [
            "uses Yoda-like inversion and aphoristic compression",
            "frames the problem through balance, burden, discipline, or haste",
            "slows urgency before advising",
            "keeps practical guidance intact",
        ],
    },
}


def call_anthropic(*, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    body = {
        "model": model,
        "max_tokens": 1400,
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


def call_openrouter(*, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/icherniukh/personify",
            "X-OpenRouter-Title": "personify activation benchmark",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())

    choices = payload.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            chunks = [item.get("text", "") for item in content if isinstance(item, dict)]
            output = "\n".join(chunk for chunk in chunks if chunk).strip()
            if output:
                return output
    raise ValueError(f"empty output: {payload}")


def make_caller(provider: str, api_key: str) -> Callable[..., str]:
    if provider == "anthropic":
        def call(*, model: str, system_prompt: str, user_prompt: str) -> str:
            return call_anthropic(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    elif provider == "openrouter":
        def call(*, model: str, system_prompt: str, user_prompt: str) -> str:
            return call_openrouter(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    else:
        def call(*, model: str, system_prompt: str, user_prompt: str) -> str:
            return call_openai(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    return call


def detect_provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    return "anthropic"


def first_json_object(text: str) -> dict[str, object]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in: {text!r}")
    return json.loads(text[start : end + 1])


def load_cases(persona_id: str) -> list[dict[str, object]]:
    return json.loads(Path(PERSONAS[persona_id]["cases"]).read_text(encoding="utf-8"))


def build_plain_prepend_packet(persona_id: str) -> str:
    return "\n\n".join(
        [
            str(PERSONAS[persona_id]["plain_prompt"]),
            load_neutral_packet(),
        ]
    )


def build_pap_packet(persona_id: str) -> str:
    return load_packet(Path(PERSONAS[persona_id]["pack"]))


def build_judge_prompt(
    *,
    persona_id: str,
    case: dict[str, object],
    neutral_output: str,
    plain_output: str,
    pap_output: str,
) -> str:
    pack = parse_simple_yaml(Path(PERSONAS[persona_id]["pack"]))
    markers = "\n".join(f"- {item}" for item in PERSONAS[persona_id]["markers"])
    requirements = "\n".join(f"- {item}" for item in case["task_requirements"])
    persona_expectation_key = persona_id.split("-")[0] + "_expectations"
    persona_expectations = case.get(persona_expectation_key, [])
    expectation_text = "\n".join(f"- {item}" for item in persona_expectations)

    return textwrap.dedent(
        f"""
        Evaluate three assistant responses to the same user task:

        1. Neutral Baseline: no persona overlay.
        2. Plain Prepend Baseline: a basic "respond like {pack['display_name']}" instruction.
        3. PAP + Self-Check: Personify's Persona Activation Packet plus loaded persona fields and drift checks.

        The benchmark question is whether PAP + Self-Check beats the Plain Prepend
        Baseline while preserving task quality. Do not reward theatrical imitation
        if the answer becomes less useful or less correct.

        Persona id: {persona_id}
        Display name: {pack['display_name']}
        Summary: {pack['summary']}

        Persona markers to look for:
        {markers}

        Case: {case['id']} - {case['title']}
        User task:
        {case['user_input']}

        Task requirements:
        {requirements}

        Persona-specific expectations:
        {expectation_text}

        Difference expectation:
        {case['difference_expectation']}

        Neutral Baseline output:
        ---
        {neutral_output}
        ---

        Plain Prepend Baseline output:
        ---
        {plain_output}
        ---

        PAP + Self-Check output:
        ---
        {pap_output}
        ---

        Return JSON only with this exact shape:
        {{
          "task_success_neutral": true,
          "task_success_plain": true,
          "task_success_pap": true,
          "neutral_stays_neutral": true,
          "plain_shows_persona": true,
          "pap_shows_persona": true,
          "pap_preserves_task_quality": true,
          "pap_beats_plain": true,
          "notes": "short explanation of where PAP did or did not beat the plain prepend",
          "scores": {{
            "neutral_task": 1,
            "plain_task": 1,
            "pap_task": 1,
            "plain_persona": 1,
            "pap_persona": 1,
            "plain_reasoning_delta": 1,
            "pap_reasoning_delta": 1,
            "plain_repetition_control": 1,
            "pap_repetition_control": 1,
            "pap_advantage": 1
          }}
        }}

        Scoring: 1=poor, 3=acceptable, 5=strong.
        pap_advantage is the overall advantage of PAP + Self-Check over Plain
        Prepend Baseline. Set pap_beats_plain=true only if PAP is meaningfully
        stronger on persona fidelity, reasoning/framing delta, or repetition
        control while keeping task quality at least as good as plain prepend.
        """
    ).strip()


def run_case(
    *,
    persona_id: str,
    case: dict[str, object],
    model: str,
    judge_model: str,
    call: Callable[..., str],
    neutral_packet: str,
    plain_packet: str,
    pap_packet: str,
) -> dict[str, object]:
    user_prompt = str(case["user_input"])
    neutral_output = call(model=model, system_prompt=neutral_packet, user_prompt=user_prompt)
    plain_output = call(model=model, system_prompt=plain_packet, user_prompt=user_prompt)
    pap_output = call(model=model, system_prompt=pap_packet, user_prompt=user_prompt)
    judge_prompt = build_judge_prompt(
        persona_id=persona_id,
        case=case,
        neutral_output=neutral_output,
        plain_output=plain_output,
        pap_output=pap_output,
    )
    judge_raw = call(
        model=judge_model,
        system_prompt="You are a strict evaluator. Return JSON only, no commentary outside the JSON object.",
        user_prompt=judge_prompt,
    )
    verdict = first_json_object(judge_raw)
    verdict["neutral_output"] = neutral_output
    verdict["plain_output"] = plain_output
    verdict["pap_output"] = pap_output
    return verdict


def validate_verdict(label: str, verdict: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for key in [
        "task_success_neutral",
        "task_success_plain",
        "task_success_pap",
        "neutral_stays_neutral",
        "pap_shows_persona",
        "pap_preserves_task_quality",
        "pap_beats_plain",
    ]:
        if verdict.get(key) is not True:
            failures.append(f"{label}: {key} was not true")

    scores = verdict.get("scores", {})
    if not isinstance(scores, dict):
        failures.append(f"{label}: missing score block")
        return failures

    thresholds = {
        "neutral_task": 3,
        "plain_task": 1,
        "pap_task": 3,
        "plain_persona": 1,
        "pap_persona": 3,
        "plain_reasoning_delta": 1,
        "pap_reasoning_delta": 3,
        "plain_repetition_control": 2,
        "pap_repetition_control": 3,
        "pap_advantage": 3,
    }
    for key, threshold in thresholds.items():
        value = scores.get(key)
        if not isinstance(value, int) or value < threshold:
            failures.append(f"{label}: {key} score {value!r} < {threshold}")

    for pap_key, plain_key in [
        ("pap_task", "plain_task"),
        ("pap_persona", "plain_persona"),
        ("pap_reasoning_delta", "plain_reasoning_delta"),
    ]:
        pap_value = scores.get(pap_key)
        plain_value = scores.get(plain_key)
        if isinstance(pap_value, int) and isinstance(plain_value, int) and pap_value < plain_value:
            failures.append(f"{label}: {pap_key} score {pap_value} < {plain_key} score {plain_value}")

    return failures


def summarize_trials(label: str, verdicts: list[dict[str, object]]) -> list[str]:
    passes = 0
    failures_by_trial: list[list[str]] = []
    for i, verdict in enumerate(verdicts, 1):
        failures = validate_verdict(f"{label} trial {i}", verdict)
        failures_by_trial.append(failures)
        if not failures:
            passes += 1

    required = (len(verdicts) // 2) + 1
    if passes >= required:
        return []

    out = [f"{label}: {passes}/{len(verdicts)} trials passed, need {required}"]
    for i, failures in enumerate(failures_by_trial, 1):
        for failure in failures:
            out.append(f"  trial {i}: {failure}")
    return out


def load_model_config(path: Path = MODEL_CONFIG_PATH) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_rotation_state(path: Path = ROTATION_STATE_PATH) -> dict[str, int]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): int(value) for key, value in payload.items()}


def save_rotation_state(state: dict[str, int], path: Path = ROTATION_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rotate_model_pair(provider: str) -> tuple[str, str, str]:
    config = load_model_config()
    provider_config = config.get(provider, {}) if isinstance(config, dict) else {}
    pairs = provider_config.get("pairs", []) if isinstance(provider_config, dict) else []
    if not isinstance(pairs, list) or not pairs:
        if provider == "openrouter":
            return DEFAULT_OPENROUTER_MODEL, DEFAULT_OPENROUTER_JUDGE_MODEL, "openrouter-default"
        raise ValueError(f"no model rotation config for provider: {provider}")

    state = load_rotation_state()
    index = (state.get(provider, -1) + 1) % len(pairs)
    state[provider] = index
    save_rotation_state(state)

    pair = pairs[index]
    if not isinstance(pair, dict):
        raise ValueError(f"invalid model pair at index {index} for provider {provider}")
    return str(pair["model"]), str(pair["judge_model"]), str(pair.get("name", f"{provider}-{index}"))


def make_run_id(*, provider: str, persona: str, repeats: int) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    persona_part = persona.replace("/", "-")
    return f"{stamp}-{provider}-{persona_part}-{repeats}x"


def default_output_paths(run_id: str) -> tuple[Path, Path]:
    return DEFAULT_REPORT_DIR / f"{run_id}.jsonl", DEFAULT_REPORT_DIR / f"{run_id}.md"


def markdown_cell(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    return text.replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def write_markdown_table(fh, headers: list[str], rows: list[list[object]]) -> None:
    fh.write("| " + " | ".join(markdown_cell(header) for header in headers) + " |\n")
    fh.write("| " + " | ".join("---" for _ in headers) + " |\n")
    for row in rows:
        fh.write("| " + " | ".join(markdown_cell(value) for value in row) + " |\n")
    fh.write("\n")


def report_header(*, provider: str, model: str, judge_model: str, model_pair: str, repeats: int) -> str:
    lines = ["# Personify Activation Benchmark Report", "", "## Run Metadata", ""]
    rows = [
        ["Provider", f"`{provider}`"],
        ["Generator model", f"`{model}`"],
        ["Judge model", f"`{judge_model}`"],
        ["Model pair", f"`{model_pair}`"],
        ["Repeats", repeats],
    ]
    from io import StringIO

    out = StringIO()
    out.write("\n".join(lines))
    write_markdown_table(out, ["Field", "Value"], rows)
    return out.getvalue()


def bool_label(value: object) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return str(value)


def score_value(scores: object, key: str) -> object:
    if isinstance(scores, dict):
        return scores.get(key, "")
    return ""


def treatment_score_summary(scores: object, treatment: str) -> str:
    if treatment == "neutral":
        return f"task={score_value(scores, 'neutral_task')}"
    if treatment == "plain":
        return "; ".join(
            [
                f"task={score_value(scores, 'plain_task')}",
                f"persona={score_value(scores, 'plain_persona')}",
                f"reasoning={score_value(scores, 'plain_reasoning_delta')}",
                f"repetition={score_value(scores, 'plain_repetition_control')}",
            ]
        )
    return "; ".join(
        [
            f"task={score_value(scores, 'pap_task')}",
            f"persona={score_value(scores, 'pap_persona')}",
            f"reasoning={score_value(scores, 'pap_reasoning_delta')}",
            f"repetition={score_value(scores, 'pap_repetition_control')}",
            f"advantage={score_value(scores, 'pap_advantage')}",
        ]
    )


def append_report(
    path: Path,
    *,
    persona_id: str,
    case: dict[str, object],
    trial: int,
    verdict: dict[str, object],
    failures: list[str],
) -> None:
    scores = verdict.get("scores", {})
    status = "PASS" if not failures else "FAIL"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"## {persona_id} / {case['id']} / trial {trial}: {status}\n\n")
        fh.write("### Case\n\n")
        write_markdown_table(
            fh,
            ["Field", "Value"],
            [
                ["Persona", persona_id],
                ["Case", case["id"]],
                ["Task", case["title"]],
                ["User prompt", case["user_input"]],
            ],
        )

        fh.write("### Judge Checks\n\n")
        write_markdown_table(
            fh,
            ["Check", "Result"],
            [
                ["Neutral task success", bool_label(verdict.get("task_success_neutral"))],
                ["Plain task success", bool_label(verdict.get("task_success_plain"))],
                ["PAP task success", bool_label(verdict.get("task_success_pap"))],
                ["Neutral stays neutral", bool_label(verdict.get("neutral_stays_neutral"))],
                ["Plain shows persona", bool_label(verdict.get("plain_shows_persona"))],
                ["PAP shows persona", bool_label(verdict.get("pap_shows_persona"))],
                ["PAP preserves task quality", bool_label(verdict.get("pap_preserves_task_quality"))],
                ["PAP beats plain", bool_label(verdict.get("pap_beats_plain"))],
            ],
        )

        fh.write("### Score Comparison\n\n")
        write_markdown_table(
            fh,
            ["Metric", "Neutral", "Plain", "PAP"],
            [
                ["Task quality", score_value(scores, "neutral_task"), score_value(scores, "plain_task"), score_value(scores, "pap_task")],
                ["Persona fidelity", "", score_value(scores, "plain_persona"), score_value(scores, "pap_persona")],
                [
                    "Reasoning/framing delta",
                    "",
                    score_value(scores, "plain_reasoning_delta"),
                    score_value(scores, "pap_reasoning_delta"),
                ],
                [
                    "Repetition control",
                    "",
                    score_value(scores, "plain_repetition_control"),
                    score_value(scores, "pap_repetition_control"),
                ],
                ["PAP advantage", "", "", score_value(scores, "pap_advantage")],
            ],
        )

        fh.write("### Judge Notes\n\n")
        fh.write(str(verdict.get("notes", "")).strip() + "\n\n")

        fh.write("### Validation\n\n")
        validation_rows = [["FAIL", failure] for failure in failures] if failures else [["PASS", "No validation failures."]]
        write_markdown_table(fh, ["Status", "Detail"], validation_rows)

        fh.write("### Answer Comparison\n\n")
        write_markdown_table(
            fh,
            ["Treatment", "Scores", "Answer"],
            [
                ["Neutral Baseline", treatment_score_summary(scores, "neutral"), verdict.get("neutral_output", "")],
                ["Plain Prepend Baseline", treatment_score_summary(scores, "plain"), verdict.get("plain_output", "")],
                ["PAP + Self-Check", treatment_score_summary(scores, "pap"), verdict.get("pap_output", "")],
            ],
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark PAP activation against plain persona prepend.")
    parser.add_argument("--persona", choices=sorted(PERSONAS) + ["all"], default="all")
    parser.add_argument("--case", dest="case_id", help="Run one case id. Requires a non-all persona if ids overlap.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--model", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--api", choices=["anthropic", "openai", "openrouter"], default=None)
    parser.add_argument("--show-outputs", action="store_true")
    parser.add_argument("--output-jsonl", type=Path, help="Optional path for verdict JSONL.")
    parser.add_argument("--output-report", type=Path, help="Optional markdown report path with scores and raw outputs.")
    parser.add_argument("--run-id", help="Stable id for default benchmark output files.")
    return parser.parse_args()


def selected_personas(persona: str) -> list[str]:
    if persona == "all":
        return sorted(PERSONAS)
    return [persona]


def main() -> int:
    args = parse_args()
    provider = args.api or detect_provider()

    model_pair = "manual"
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        default_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        default_judge = os.environ.get("ANTHROPIC_JUDGE_MODEL", default_model)
    elif provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        env_model = os.environ.get("OPENROUTER_MODEL")
        env_judge = os.environ.get("OPENROUTER_JUDGE_MODEL")
        if args.model or args.judge_model or env_model or env_judge:
            default_model = env_model or DEFAULT_OPENROUTER_MODEL
            default_judge = env_judge or DEFAULT_OPENROUTER_JUDGE_MODEL
        else:
            default_model, default_judge, model_pair = rotate_model_pair(provider)
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        default_model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        default_judge = os.environ.get("OPENAI_JUDGE_MODEL", default_model)

    model = args.model or default_model
    judge_model = args.judge_model or default_judge
    persona_ids = selected_personas(args.persona)

    print("=== personify activation benchmark ===")
    print(f"provider: {provider}  model: {model}  judge: {judge_model}  repeats: {args.repeats}")
    print(f"model pair: {model_pair}")

    run_id = args.run_id or make_run_id(provider=provider, persona=args.persona, repeats=args.repeats)
    default_jsonl, default_report = default_output_paths(run_id)
    output_jsonl = args.output_jsonl or default_jsonl
    output_report = args.output_report or default_report
    print(f"jsonl: {output_jsonl.relative_to(ROOT_DIR) if output_jsonl.is_relative_to(ROOT_DIR) else output_jsonl}")
    print(f"report: {output_report.relative_to(ROOT_DIR) if output_report.is_relative_to(ROOT_DIR) else output_report}")

    runs: list[tuple[str, dict[str, object], str, str, str]] = []
    for persona_id in persona_ids:
        cases = load_cases(persona_id)
        if args.case_id:
            cases = [case for case in cases if case["id"] == args.case_id]
            if not cases:
                if args.persona == "all":
                    continue
                raise SystemExit(f"unknown case id for {persona_id}: {args.case_id!r}")
        neutral_packet = load_neutral_packet()
        plain_packet = build_plain_prepend_packet(persona_id)
        pap_packet = build_pap_packet(persona_id)
        for case in cases:
            runs.append((persona_id, case, neutral_packet, plain_packet, pap_packet))

    if not runs:
        raise SystemExit(f"no benchmark cases selected for case id: {args.case_id!r}")

    for persona_id, case, neutral_packet, plain_packet, pap_packet in runs:
        print(f"persona: {persona_id}  case: {case['id']}")
        if args.dry_run:
            print(f"  neutral packet:       {len(neutral_packet)} chars")
            print(f"  plain prepend packet: {len(plain_packet)} chars")
            print(f"  pap packet:           {len(pap_packet)} chars")

    if args.dry_run:
        print(f"api key set: {bool(api_key)}")
        print("dry run - no API calls made")
        return 0

    if not api_key:
        raise SystemExit("API key required: set ANTHROPIC_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY")

    output_file = None
    if output_jsonl:
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        output_file = output_jsonl.open("w", encoding="utf-8")
    if output_report:
        output_report.parent.mkdir(parents=True, exist_ok=True)
        output_report.write_text(
            report_header(provider=provider, model=model, judge_model=judge_model, model_pair=model_pair, repeats=args.repeats),
            encoding="utf-8",
        )

    call = make_caller(provider, api_key)
    all_failures: list[str] = []
    try:
        for persona_id, case, neutral_packet, plain_packet, pap_packet in runs:
            label = f"{persona_id}/{case['id']}"
            print(f"\ncase: {label}")
            verdicts: list[dict[str, object]] = []
            for trial in range(1, args.repeats + 1):
                print(f"  trial {trial}/{args.repeats} ... ", end="", flush=True)
                try:
                    verdict = run_case(
                        persona_id=persona_id,
                        case=case,
                        model=model,
                        judge_model=judge_model,
                        call=call,
                        neutral_packet=neutral_packet,
                        plain_packet=plain_packet,
                        pap_packet=pap_packet,
                    )
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", errors="replace")
                    print(f"HTTP {exc.code}")
                    print(detail)
                    return 1
                except urllib.error.URLError as exc:
                    print(f"network error: {exc}")
                    return 1

                failures = validate_verdict(f"{label} trial {trial}", verdict)
                print("PASS" if not failures else "FAIL")
                summary = {k: v for k, v in verdict.items() if k not in {"neutral_output", "plain_output", "pap_output"}}
                print(json.dumps(summary, indent=4))

                if args.show_outputs:
                    print(f"\n  --- neutral ---\n{verdict['neutral_output']}\n")
                    print(f"  --- plain prepend ---\n{verdict['plain_output']}\n")
                    print(f"  --- pap + self-check ---\n{verdict['pap_output']}\n")

                if output_file:
                    output_file.write(json.dumps({
                        "provider": provider,
                        "model": model,
                        "judge_model": judge_model,
                        "model_pair": model_pair,
                        "persona": persona_id,
                        "case": case["id"],
                        "trial": trial,
                        **verdict,
                    }) + "\n")
                    output_file.flush()
                if output_report:
                    append_report(
                        output_report,
                        persona_id=persona_id,
                        case=case,
                        trial=trial,
                        verdict=verdict,
                        failures=failures,
                    )
                verdicts.append(verdict)

            all_failures.extend(summarize_trials(label, verdicts))
    finally:
        if output_file:
            output_file.close()

    print()
    if all_failures:
        print("=== FAILED ===")
        for failure in all_failures:
            print(f"  {failure}")
        return 1

    print("=== PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
