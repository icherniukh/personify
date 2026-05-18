#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PERSONA_LIST_SCRIPT = ROOT_DIR / "scripts" / "persona_list.py"


def write_pack(path: Path, pack_id: str, display_name: str, summary: str, quality_level: str = "user") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"id: {pack_id}",
                f"display_name: {display_name}",
                f"summary: {summary}",
                f"quality_level: {quality_level}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    print("=== persona list overlay test ===")

    with tempfile.TemporaryDirectory() as data_home, tempfile.TemporaryDirectory() as config_home:
        user_personas = Path(data_home) / "personify" / "personas"
        write_pack(user_personas / "yoda.yaml", "yoda", "Yoda User Override", "user yoda summary")
        write_pack(user_personas / "custom.yaml", "custom", "Custom Persona", "custom summary")

        hidden_file = Path(config_home) / "personify" / "hidden.yaml"
        hidden_file.parent.mkdir(parents=True, exist_ok=True)
        hidden_file.write_text("hidden:\n  - sam-harris\n", encoding="utf-8")

        env = os.environ.copy()
        env["XDG_DATA_HOME"] = data_home
        env["XDG_CONFIG_HOME"] = config_home

        result = subprocess.run(
            ["python3", str(PERSONA_LIST_SCRIPT)],
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    lines = result.stdout.splitlines()
    by_id = {line.split("\t", 1)[0]: line for line in lines}

    print("1. user-created packs are listed")
    assert "custom" in by_id
    assert by_id["custom"] == "custom\tCustom Persona\tuser\tcustom summary"
    print("ok")

    print("2. user packs override bundled packs with the same id")
    assert by_id["yoda"] == "yoda\tYoda User Override\tuser\tuser yoda summary"
    print("ok")

    print("3. tombstones hide matching bundled ids")
    assert "sam-harris" not in by_id
    print("ok")

    print("=== persona list overlay test passed ===")


if __name__ == "__main__":
    main()
