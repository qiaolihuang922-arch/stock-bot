#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

REPO="$REPO_ROOT"
TECH_WORKTREE="$CAO_TECH_WORKTREE"

HANDOFF_FILES=(
  AGENTS.md
  DISPATCH.md
  RESEARCH.md
  CURRENT_STATE.md
  CLEANUP_PLAN.md
  TASK.md
  CHANGELOG.md
  QA_REPORT.md
)

ensure_tech_worktree

if ! git -C "$REPO" diff --quiet || ! git -C "$REPO" diff --cached --quiet; then
  echo "Main repo has uncommitted changes; refusing to clean agent worktrees." >&2
  exit 1
fi

target_ref="${1:-$(git -C "$REPO" rev-parse HEAD)}"

for f in "${HANDOFF_FILES[@]}"; do
  git -C "$TECH_WORKTREE" update-index --no-skip-worktree "$f" >/dev/null 2>&1 || true
done

git -C "$TECH_WORKTREE" fetch origin main >/dev/null 2>&1 || true
git -C "$TECH_WORKTREE" reset --hard "$target_ref" >/dev/null
git -C "$TECH_WORKTREE" clean -fd -e .venv >/dev/null
rm -rf "$TECH_WORKTREE/.qa_tmp"

exclude_file="$(git -C "$TECH_WORKTREE" rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$exclude_file")"
touch "$exclude_file"
grep -qxF ".venv" "$exclude_file" || echo ".venv" >> "$exclude_file"
grep -qxF ".qa_tmp" "$exclude_file" || echo ".qa_tmp" >> "$exclude_file"

echo "Cleaned $TECH_WORKTREE to $(git -C "$TECH_WORKTREE" rev-parse --short HEAD)"
git -C "$TECH_WORKTREE" status --short --branch
