#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

PLUGIN_JSON="$ROOT_DIR/.codex-plugin/plugin.json"
ARCH_REVIEW_CORE="$ROOT_DIR/skills/architecture-review-core/SKILL.md"
BJARNE_ARCH_REVIEW="$ROOT_DIR/skills/bjarne-stroustrup-architecture-review/SKILL.md"
YODA_ARCH_REVIEW="$ROOT_DIR/skills/yoda-architecture-review/SKILL.md"
PERSONA_START="$ROOT_DIR/skills/persona-start/SKILL.md"
PERSONA_APPLY="$ROOT_DIR/skills/persona-apply/SKILL.md"
PERSONA_LIST="$ROOT_DIR/skills/persona-list/SKILL.md"
CORE_SKILL="$ROOT_DIR/skills/orchestrator-core/SKILL.md"
SAM_WRAPPER="$ROOT_DIR/skills/sam-harris-orchestrator/SKILL.md"
PERSONA_LIST_SCRIPT="$ROOT_DIR/scripts/persona_list.py"
PERSONA_EXTRACT="$ROOT_DIR/skills/persona-extract/SKILL.md"
PERSONA_EXTRACT_ONLINE="$ROOT_DIR/skills/persona-extract-online/SKILL.md"
BJARNE_PACK="$ROOT_DIR/assets/personalities/bjarne-stroustrup.yaml"
SAM_PACK="$ROOT_DIR/assets/personalities/sam-harris.yaml"
YODA_PACK="$ROOT_DIR/assets/personalities/yoda.yaml"

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

echo "=== promptonality smoke test ==="

echo "1. Required files"
require_file "$PLUGIN_JSON"
require_file "$ARCH_REVIEW_CORE"
require_file "$BJARNE_ARCH_REVIEW"
require_file "$YODA_ARCH_REVIEW"
require_file "$PERSONA_START"
require_file "$PERSONA_APPLY"
require_file "$PERSONA_LIST"
require_file "$CORE_SKILL"
require_file "$SAM_WRAPPER"
require_file "$PERSONA_LIST_SCRIPT"
require_file "$PERSONA_EXTRACT"
require_file "$PERSONA_EXTRACT_ONLINE"
require_file "$BJARNE_PACK"
require_file "$SAM_PACK"
require_file "$YODA_PACK"
echo "ok"

echo "2. plugin package validation"
python3 "$ROOT_DIR/test/package_test.py"

echo "3. personality-pack required fields"
require_pattern "id: bjarne-stroustrup$" "$BJARNE_PACK"
require_pattern "display_name: Bjarne Stroustrup$" "$BJARNE_PACK"
require_pattern "summary:" "$BJARNE_PACK"
require_pattern "voice:$" "$BJARNE_PACK"
require_pattern "interaction_stance:$" "$BJARNE_PACK"
require_pattern "value_profile:$" "$BJARNE_PACK"
require_pattern "reasoning_style:$" "$BJARNE_PACK"
require_pattern "preferred_terminology:$" "$BJARNE_PACK"
require_pattern "speech_patterns:$" "$BJARNE_PACK"
require_pattern "default_structures:$" "$BJARNE_PACK"
require_pattern "ambiguity_policy: \\|$" "$BJARNE_PACK"
require_pattern "tradeoff_policy: \\|$" "$BJARNE_PACK"
require_pattern "compression_policy: \\|$" "$BJARNE_PACK"
require_pattern "interaction_rules:$" "$BJARNE_PACK"
require_pattern "guardrails:$" "$BJARNE_PACK"
require_pattern "anti_patterns:$" "$BJARNE_PACK"
require_pattern "prompt_overlay: \\|$" "$BJARNE_PACK"
require_pattern "provenance:$" "$BJARNE_PACK"
require_pattern "quality_level:" "$BJARNE_PACK"
require_pattern "id: yoda$" "$YODA_PACK"
require_pattern "display_name: Yoda$" "$YODA_PACK"
require_pattern "summary:" "$YODA_PACK"
require_pattern "voice:$" "$YODA_PACK"
require_pattern "interaction_stance:$" "$YODA_PACK"
require_pattern "value_profile:$" "$YODA_PACK"
require_pattern "reasoning_style:$" "$YODA_PACK"
require_pattern "preferred_terminology:$" "$YODA_PACK"
require_pattern "speech_patterns:$" "$YODA_PACK"
require_pattern "default_structures:$" "$YODA_PACK"
require_pattern "ambiguity_policy: \\|$" "$YODA_PACK"
require_pattern "tradeoff_policy: \\|$" "$YODA_PACK"
require_pattern "compression_policy: \\|$" "$YODA_PACK"
require_pattern "interaction_rules:$" "$YODA_PACK"
require_pattern "guardrails:$" "$YODA_PACK"
require_pattern "anti_patterns:$" "$YODA_PACK"
require_pattern "prompt_overlay: \\|$" "$YODA_PACK"
require_pattern "provenance:$" "$YODA_PACK"
require_pattern "quality_level:" "$YODA_PACK"
require_pattern "id: sam-harris$" "$SAM_PACK"
require_pattern "display_name: Sam Harris$" "$SAM_PACK"
require_pattern "summary:" "$SAM_PACK"
require_pattern "voice:$" "$SAM_PACK"
require_pattern "interaction_stance:$" "$SAM_PACK"
require_pattern "value_profile:$" "$SAM_PACK"
require_pattern "reasoning_style:$" "$SAM_PACK"
require_pattern "preferred_terminology:$" "$SAM_PACK"
require_pattern "speech_patterns:$" "$SAM_PACK"
require_pattern "default_structures:$" "$SAM_PACK"
require_pattern "ambiguity_policy: \\|$" "$SAM_PACK"
require_pattern "tradeoff_policy: \\|$" "$SAM_PACK"
require_pattern "compression_policy: \\|$" "$SAM_PACK"
require_pattern "interaction_rules:$" "$SAM_PACK"
require_pattern "guardrails:$" "$SAM_PACK"
require_pattern "anti_patterns:$" "$SAM_PACK"
require_pattern "prompt_overlay: \\|$" "$SAM_PACK"
require_pattern "provenance:$" "$SAM_PACK"
require_pattern "quality_level:" "$SAM_PACK"
echo "ok"

echo "4. composition references"
rg -q "architecture-review-core/SKILL.md" "$BJARNE_ARCH_REVIEW"
rg -q "assets/personalities/bjarne-stroustrup.yaml" "$BJARNE_ARCH_REVIEW"
rg -q "architecture-review-core/SKILL.md" "$YODA_ARCH_REVIEW"
rg -q "assets/personalities/yoda.yaml" "$YODA_ARCH_REVIEW"
rg -q "there is no prebuilt named variant" "$PERSONA_START"
rg -q "This skill does not create a new installed variant" "$PERSONA_APPLY"
rg -q "Existing variant skill:" "$PERSONA_APPLY"
rg -q "Read those YAML files directly when listing available" "$PERSONA_LIST"
rg -q "Do not assume the current working directory is the" "$PERSONA_LIST"
rg -q "Explicit composition:" "$PERSONA_LIST"
rg -q "orchestrator-core/SKILL.md" "$SAM_WRAPPER"
rg -q "assets/personalities/sam-harris.yaml" "$SAM_WRAPPER"
echo "ok"

echo "5. separation guard"
if rg -q "\\b(Rue|rue)\\b" "$ROOT_DIR/skills" "$ROOT_DIR/assets"; then
    echo "unexpected Rue reference in promptonality plugin" >&2
    exit 1
fi
echo "ok"

echo "6. behavior test"
python3 "$ROOT_DIR/test/behavior_test.py"

echo "7. extractor test"
python3 "$ROOT_DIR/test/extractor_test.py"

echo "8. personality listing script"
python3 "$ROOT_DIR/scripts/persona_list.py"

echo "9. Claude export sync check"
python3 "$ROOT_DIR/scripts/export_claude_skills.py" --check

echo "10. Claude plugin export sync check"
python3 "$ROOT_DIR/scripts/export_claude_plugin.py" --check

echo "11. Claude plugin package validation"
python3 "$ROOT_DIR/test/claude_plugin_test.py"

echo "12. live model runner dry run"
python3 "$ROOT_DIR/test/live_model_test.py" --dry-run

echo "13. architecture live runner dry run"
python3 "$ROOT_DIR/test/architecture_live_test.py" --dry-run

echo "=== smoke test passed ==="
