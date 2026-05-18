#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

PLUGIN_JSON="$ROOT_DIR/codex/.codex-plugin/plugin.json"
PERSONA_START="$ROOT_DIR/src/skills/use-persona/SKILL.md"
PERSONA_APPLY="$ROOT_DIR/src/skills/as-persona/SKILL.md"
PERSONA_LIST="$ROOT_DIR/src/skills/list-personas/SKILL.md"
PERSONA_LIST_SCRIPT="$ROOT_DIR/scripts/persona_list.py"
PERSONA_EXTRACT_ONLINE="$ROOT_DIR/src/skills/extract-persona/SKILL.md"

require_file() {
    local path="$1"
    if [ ! -f "$path" ]; then
        echo "missing required file: $path" >&2
        exit 1
    fi
}

require_pattern() {
    local pattern="$1"
    local path="$2"
    if ! rg -q "^${pattern}" "$path"; then
        echo "missing required pattern '${pattern}' in $path" >&2
        exit 1
    fi
}

echo "=== personify smoke test ==="

echo "1. Build generated platform packages"
python3 "$ROOT_DIR/scripts/package.py" build --target all
echo "ok"

echo "2. Required files"
require_file "$PLUGIN_JSON"
require_file "$PERSONA_START"
require_file "$PERSONA_APPLY"
require_file "$PERSONA_LIST"
require_file "$PERSONA_LIST_SCRIPT"
require_file "$PERSONA_EXTRACT_ONLINE"
echo "ok"

echo "3. plugin package validation"
python3 "$ROOT_DIR/test/package_test.py"

echo "4. personality-pack contract validation"
python3 "$ROOT_DIR/test/personality_pack_contract_test.py"
echo "ok"

echo "5. composition references"
rg -q "Persona asset:" "$PERSONA_START"
rg -q "use this persona for this kind of work" "$PERSONA_START"
rg -q "This skill does not create a new installed skill" "$PERSONA_APPLY"
rg -q "Persona plus task" "$PERSONA_APPLY"
rg -q "Read those YAML files directly when listing available personas" "$PERSONA_LIST"
rg -q "as-persona" "$PERSONA_LIST"
echo "ok"

echo "6. separation guard"
if rg -q "\\b(Rue|rue)\\b" "$ROOT_DIR/src/skills" "$ROOT_DIR/src/assets"; then
    echo "unexpected Rue reference in personify plugin" >&2
    exit 1
fi
echo "ok"

echo "7. behavior test"
python3 "$ROOT_DIR/test/behavior_test.py"

echo "8. extractor test"
python3 "$ROOT_DIR/test/extractor_test.py"

echo "9. personality listing script"
python3 "$ROOT_DIR/scripts/persona_list.py"

echo "10. Platform package sync check"
python3 "$ROOT_DIR/scripts/package.py" check --target all

echo "11. Claude plugin package validation"
python3 "$ROOT_DIR/test/claude_plugin_test.py"

echo "12. live model runner dry run"
python3 "$ROOT_DIR/test/live_model_test.py" --dry-run

echo "13. activation benchmark dry run"
python3 "$ROOT_DIR/test/activation_benchmark_test.py"
python3 "$ROOT_DIR/test/activation_benchmark.py" --api openrouter --dry-run --persona sam-harris --case hidden-assumption

echo "=== smoke test passed ==="
