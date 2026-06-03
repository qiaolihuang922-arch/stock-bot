#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT"

git_completion_output="$(tools/cao_agent/check_git_completion_gate.sh "$ROOT")"

if rg -n "待 push|待 final 收口|pending commit|pending push|commit / push 待|push / completion gate|未 commit / 未 push" DISPATCH.md CURRENT_STATE.md; then
  {
    echo
    echo "Architect closeout gate failed: git completion passed, but closeout docs still contain pending commit/push language."
    echo "Fix DISPATCH.md / CURRENT_STATE.md before final so a resumed conversation does not infer a stale task state."
  } >&2
  exit 2
fi

latest_recent="$(awk '
  /^## Recently Done$/ {in_section=1; next}
  /^## / && in_section {exit}
  in_section && /^- `/ {print; exit}
' DISPATCH.md)"

if [[ -z "$latest_recent" ]]; then
  echo "Architect closeout gate failed: DISPATCH.md has no Recently Done entry." >&2
  exit 3
fi

if [[ "$latest_recent" == *pending* ]]; then
  echo "Architect closeout gate failed: top Recently Done entry is still pending." >&2
  echo "$latest_recent" >&2
  exit 4
fi

if ! rg -q "Git completion gate passed" CURRENT_STATE.md DISPATCH.md; then
  echo "Architect closeout gate failed: closeout docs do not record Git completion gate passed." >&2
  exit 5
fi

echo "$git_completion_output"
echo "Architect closeout gate passed: DISPATCH/CURRENT_STATE no longer advertise stale pending git state."
