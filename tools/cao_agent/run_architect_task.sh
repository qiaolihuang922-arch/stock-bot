#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
shift || true
TASK="${*:-}"

if [[ -z "$MODE" || -z "$TASK" ]]; then
  cat >&2 <<'EOF'
Usage:
  run_architect_task.sh research "<研究問題>"
  run_architect_task.sh plan "<技術規劃問題>"
  run_architect_task.sh auto "<Owner 任務>"

Only Architect should call this wrapper.
Broad Owner commands like "開始/繼續/處理/修復/檢查" are workflow triggers,
not permission for Architect to bypass PM -> Tech -> QA.
EOF
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$MODE" in
  research)
    exec "$SCRIPT_DIR/run_project_research.sh" "$TASK"
    ;;
  plan)
    exec "$SCRIPT_DIR/run_tech_plan.sh" "$TASK"
    ;;
  auto)
    exec "$SCRIPT_DIR/run_auto_dev_cycle.sh" "$TASK"
    ;;
  *)
    echo "Unsupported mode: $MODE" >&2
    echo "Allowed: research | plan | auto" >&2
    exit 2
    ;;
esac
