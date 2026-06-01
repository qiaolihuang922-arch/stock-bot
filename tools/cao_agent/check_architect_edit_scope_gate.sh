#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT"

allow_product_diff="${ARCHITECT_DIRECT_CODE_AUTH:-${ALLOW_PRODUCT_DIFF:-0}}"

process_re='^(AGENTS\.md|DISPATCH\.md|CURRENT_STATE\.md|CLEANUP_PLAN\.md|RESEARCH\.md|tools/cao_agent/)'
handoff_re='^(TASK\.md|CHANGELOG\.md|QA_REPORT\.md)$'
product_re='^(core/|presentation/|services/|tests/|scripts/|docs/|app\.py|main\.py|config\.py|requirements[^/]*|pyproject\.toml|pytest\.ini|\.github/)'

status_output="$(git status --porcelain)"

if [[ -z "$status_output" ]]; then
  echo "Architect edit scope gate passed: worktree clean."
  exit 0
fi

product_paths=()
process_paths=()
handoff_paths=()
other_paths=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if [[ "$path" == *" -> "* ]]; then
    path="${path##* -> }"
  fi

  if [[ "$path" =~ $product_re ]]; then
    product_paths+=("$path")
  elif [[ "$path" =~ $process_re ]]; then
    process_paths+=("$path")
  elif [[ "$path" =~ $handoff_re ]]; then
    handoff_paths+=("$path")
  else
    other_paths+=("$path")
  fi
done <<< "$status_output"

if (( ${#product_paths[@]} > 0 )) && [[ "$allow_product_diff" != "1" ]]; then
  {
    echo "Architect edit scope gate failed: product/test diffs require PM -> Tech -> QA or explicit Owner direct-code authorization."
    echo
    echo "Product/test paths:"
    printf '  - %s\n' "${product_paths[@]}"
    echo
    echo "Allowed Architect-direct scope is process docs/runner governance only."
    echo "If Owner explicitly authorized direct code edits for this exact task, rerun with ARCHITECT_DIRECT_CODE_AUTH=1."
  } >&2
  exit 2
fi

if (( ${#other_paths[@]} > 0 )) && [[ "$allow_product_diff" != "1" ]]; then
  {
    echo "Architect edit scope gate failed: unclassified diffs need explicit review before continuing."
    echo
    echo "Unclassified paths:"
    printf '  - %s\n' "${other_paths[@]}"
    echo
    echo "Classify these as process-only, handoff, or product/test before proceeding."
  } >&2
  exit 3
fi

if (( ${#handoff_paths[@]} > 0 )); then
  echo "Architect edit scope gate note: handoff files are dirty; confirm they were produced by the PM/Tech/QA runner."
  printf '  - %s\n' "${handoff_paths[@]}"
fi

echo "Architect edit scope gate passed."
if (( ${#process_paths[@]} > 0 )); then
  echo "Process/governance paths:"
  printf '  - %s\n' "${process_paths[@]}"
fi
if (( ${#product_paths[@]} > 0 )); then
  echo "Product/test paths allowed by explicit direct-code authorization:"
  printf '  - %s\n' "${product_paths[@]}"
fi
