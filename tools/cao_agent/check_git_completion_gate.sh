#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT"

branch="$(git branch --show-current)"
if [[ -z "$branch" ]]; then
  echo "Git completion gate failed: detached HEAD." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Git completion gate failed: worktree is not clean." >&2
  git status --short >&2
  exit 1
fi

upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [[ -z "$upstream" ]]; then
  echo "Git completion gate failed: branch '$branch' has no upstream." >&2
  exit 1
fi

git fetch --quiet "${upstream%%/*}" "$branch"

local_head="$(git rev-parse HEAD)"
remote_head="$(git rev-parse "$upstream")"
if [[ "$local_head" != "$remote_head" ]]; then
  echo "Git completion gate failed: HEAD is not pushed to $upstream." >&2
  echo "local:  $local_head" >&2
  echo "remote: $remote_head" >&2
  exit 1
fi

echo "Git completion gate passed: $branch at $local_head matches $upstream and worktree is clean."
