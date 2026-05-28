#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

ensure_agent_dirs
ensure_tech_worktree

echo "Repo: $REPO_ROOT"
echo "Agent context: $CAO_AGENT_CONTEXT"
echo "Tech worktree: $CAO_TECH_WORKTREE"
git -C "$CAO_TECH_WORKTREE" status --short --branch
