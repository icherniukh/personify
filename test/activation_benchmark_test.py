#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import importlib.util
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT_DIR / "test" / "activation_benchmark.py"
MODEL_CONFIG = ROOT_DIR / "config" / "activation_benchmark_models.json"


spec = importlib.util.spec_from_file_location("activation_benchmark", BENCHMARK)
assert spec is not None and spec.loader is not None
activation_benchmark = importlib.util.module_from_spec(spec)
sys.modules["activation_benchmark"] = activation_benchmark
spec.loader.exec_module(activation_benchmark)


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"expected to find {needle!r}"


def main() -> None:
    print("=== personify activation benchmark test ===")

    print("1. benchmark runner exists")
    assert BENCHMARK.is_file(), "missing activation benchmark runner"
    text = BENCHMARK.read_text(encoding="utf-8")
    assert_contains(text, "Plain Prepend Baseline")
    assert_contains(text, "PAP + Self-Check")
    assert_contains(text, "OPENROUTER_API_URL")
    assert_contains(text, "OPENROUTER_API_KEY")
    assert_contains(text, "DEFAULT_OPENROUTER_MODEL")
    assert_contains(text, "benchmark-runs")
    assert_contains(text, "activation_benchmark_models.json")
    assert_contains(text, "rotation_state")
    assert_contains(text, "--output-report")
    assert_contains(text, "PAP + Self-Check")
    assert_contains(text, "pap_beats_plain")
    assert_contains(text, "pap_advantage")
    print("ok")

    print("2. dry run loads all benchmark treatments")
    result = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--dry-run",
            "--persona",
            "sam-harris",
            "--case",
            "hidden-assumption",
        ],
        cwd=ROOT_DIR,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    assert_contains(result.stdout, "=== personify activation benchmark ===")
    assert_contains(result.stdout, "persona: sam-harris")
    assert_contains(result.stdout, "case: hidden-assumption")
    assert_contains(result.stdout, "neutral packet:")
    assert_contains(result.stdout, "plain prepend packet:")
    assert_contains(result.stdout, "pap packet:")
    assert_contains(result.stdout, "dry run - no API calls made")
    print("ok")

    print("3. openrouter dry run uses OpenRouter defaults and key")
    result = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--api",
            "openrouter",
            "--dry-run",
            "--persona",
            "sam-harris",
            "--case",
            "hidden-assumption",
        ],
        cwd=ROOT_DIR,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    assert_contains(result.stdout, "provider: openrouter")
    assert_contains(result.stdout, "model:")
    assert_contains(result.stdout, "judge:")
    assert_contains(result.stdout, "model pair:")
    assert_contains(result.stdout, "api key set:")
    print("ok")

    print("4. model rotation config is tracked and extensible")
    assert MODEL_CONFIG.is_file(), "missing model rotation config"
    config_text = MODEL_CONFIG.read_text(encoding="utf-8")
    assert_contains(config_text, '"openrouter"')
    assert_contains(config_text, '"pairs"')
    assert_contains(config_text, '"model"')
    assert_contains(config_text, '"judge_model"')
    assert_contains(config_text, '"x-ai/grok-4.3"')
    assert_contains(config_text, '"moonshotai/kimi-k2.6"')
    print("ok")

    print("5. default dry run writes repo-local report paths and model metadata")
    result = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK),
            "--api",
            "openrouter",
            "--dry-run",
            "--persona",
            "yoda",
            "--case",
            "technical-debt",
            "--run-id",
            "test-dry-run",
        ],
        cwd=ROOT_DIR,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    assert_contains(result.stdout, "report:")
    assert_contains(result.stdout, "jsonl:")
    assert_contains(result.stdout, "benchmark-runs/test-dry-run.md")
    assert_contains(result.stdout, "benchmark-runs/test-dry-run.jsonl")
    assert_contains(result.stdout, "model pair:")
    print("ok")

    print("6. validator accepts weak plain baseline when PAP wins overall")
    verdict = {
        "task_success_neutral": True,
        "task_success_plain": True,
        "task_success_pap": True,
        "neutral_stays_neutral": True,
        "plain_shows_persona": True,
        "pap_shows_persona": True,
        "pap_preserves_task_quality": True,
        "pap_beats_plain": True,
        "scores": {
            "neutral_task": 5,
            "plain_task": 2,
            "pap_task": 5,
            "plain_persona": 3,
            "pap_persona": 5,
            "plain_reasoning_delta": 2,
            "pap_reasoning_delta": 5,
            "plain_repetition_control": 5,
            "pap_repetition_control": 4,
            "pap_advantage": 5,
        },
    }
    failures = activation_benchmark.validate_verdict("regression", verdict)
    assert failures == [], failures
    print("ok")

    print("7. markdown report uses grouped comparison tables")
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.md"
        report.write_text(
            activation_benchmark.report_header(
                provider="openrouter",
                model="deepseek/deepseek-v4-pro",
                judge_model="x-ai/grok-4.3",
                model_pair="deepseek-generator-grok-judge",
                repeats=1,
            ),
            encoding="utf-8",
        )
        activation_benchmark.append_report(
            report,
            persona_id="yoda",
            case={
                "id": "technical-debt",
                "title": "Technical debt triage",
                "user_input": "Should we rewrite this service?",
            },
            trial=1,
            verdict={
                **verdict,
                "notes": "PAP is more useful.",
                "neutral_output": "Neutral answer.",
                "plain_output": "Plain answer.",
                "pap_output": "PAP answer.",
            },
            failures=[],
        )
        report_text = report.read_text(encoding="utf-8")
    assert_contains(report_text, "## Run Metadata")
    assert_contains(report_text, "| Field | Value |")
    assert_contains(report_text, "### Judge Checks")
    assert_contains(report_text, "| Check | Result |")
    assert_contains(report_text, "### Score Comparison")
    assert_contains(report_text, "| Metric | Neutral | Plain | PAP |")
    assert_contains(report_text, "### Validation")
    assert_contains(report_text, "| Status | Detail |")
    assert_contains(report_text, "### Answer Comparison")
    assert_contains(report_text, "| Treatment | Scores | Answer |")
    print("ok")

    print("=== activation benchmark test passed ===")


if __name__ == "__main__":
    main()
