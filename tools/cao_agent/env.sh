#!/usr/bin/env bash

# Shared portable paths for CAO runner scripts.
# Scripts live in stock-bot-main/tools/cao_agent and infer the repo root from
# this file location. Override any path with the matching environment variable.

CAO_AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${STOCK_BOT_REPO:-$(cd "$CAO_AGENT_DIR/../.." && pwd)}"
REPO_PARENT="$(cd "$REPO_ROOT/.." && pwd)"

CAO_BIN="${CAO_BIN:-$HOME/.local/bin/cao}"
CAO_SERVER_BIN="${CAO_SERVER_BIN:-$HOME/.local/bin/cao-server}"
CAO_LOG_DIR="${CAO_LOG_DIR:-$HOME/.aws/cli-agent-orchestrator/logs}"
CAO_WEB_DIR="${CAO_WEB_DIR:-$HOME/.local/share/cao-web-zh/web}"

CAO_AGENT_CONTEXT="${STOCK_BOT_AGENT_CONTEXT:-$REPO_ROOT/.cao_agent_context}"
CAO_AGENT_OUTPUTS="${STOCK_BOT_AGENT_OUTPUTS:-$CAO_AGENT_CONTEXT/outputs}"
CAO_ONLINE_CONTEXT="${STOCK_BOT_ONLINE_CONTEXT:-$CAO_AGENT_CONTEXT/online_research}"
CAO_TECH_PLAN_CONTEXT="${STOCK_BOT_TECH_PLAN_CONTEXT:-$CAO_AGENT_CONTEXT/tech_plan}"
CAO_TECH_WORKTREE="${STOCK_BOT_AGENT_WORKTREE:-$REPO_PARENT/stock-bot-agent-worktrees/tech_write}"

ensure_agent_dirs() {
  mkdir -p "$CAO_AGENT_CONTEXT" "$CAO_AGENT_OUTPUTS" "$CAO_LOG_DIR"
  chmod 700 "$CAO_AGENT_CONTEXT" "$CAO_AGENT_OUTPUTS" "$CAO_LOG_DIR"
}

ensure_tech_worktree() {
  if [[ -d "$CAO_TECH_WORKTREE/.git" || -f "$CAO_TECH_WORKTREE/.git" ]]; then
    return 0
  fi

  mkdir -p "$(dirname "$CAO_TECH_WORKTREE")"
  git -C "$REPO_ROOT" worktree add "$CAO_TECH_WORKTREE" HEAD >/dev/null
}
