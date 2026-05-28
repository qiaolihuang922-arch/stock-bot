#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tools/cao_agent/env.sh
source "$SCRIPT_DIR/env.sh"

missing=0

check_cmd() {
  local label="$1"
  local command="$2"
  if eval "$command" >/dev/null 2>&1; then
    echo "[ok] $label"
  else
    echo "[missing] $label"
    missing=1
  fi
}

echo "Repo: $REPO_ROOT"
echo "Agent context: $CAO_AGENT_CONTEXT"
echo "Tech worktree: $CAO_TECH_WORKTREE"
echo

check_cmd "git" "command -v git"
check_cmd "tmux" "command -v tmux"
check_cmd "npm" "command -v npm"
check_cmd "uv" "command -v uv"
check_cmd "Codex app binary" "test -x \"${CODEX_APP_BIN:-/Applications/Codex.app/Contents/Resources/codex}\""
check_cmd "CAO CLI" "test -x \"$CAO_BIN\""
check_cmd "CAO server" "test -x \"$CAO_SERVER_BIN\""
check_cmd "CAO MCP server" "test -x \"$CAO_MCP_SERVER_BIN\""
check_cmd "CAO web UI" "test -f \"$CAO_WEB_DIR/package.json\""

if [[ ! -x "$CAO_BIN" || ! -x "$CAO_SERVER_BIN" || ! -x "$CAO_MCP_SERVER_BIN" ]]; then
  if command -v uv >/dev/null 2>&1; then
    echo
    echo "Installing CAO CLI with uv..."
    uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main"
  else
    echo
    echo "Install uv first, then run:"
    echo '  uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main"'
  fi
fi

if [[ ! -f "$CAO_WEB_DIR/package.json" ]]; then
  echo
  echo "CAO web UI not found at: $CAO_WEB_DIR"
  if command -v git >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    if [[ ! -d "$CAO_WEB_REPO_DIR/.git" ]]; then
      mkdir -p "$(dirname "$CAO_WEB_REPO_DIR")"
      echo "Cloning CAO web source to: $CAO_WEB_REPO_DIR"
      git clone https://github.com/awslabs/cli-agent-orchestrator.git "$CAO_WEB_REPO_DIR"
    fi
    if [[ -f "$CAO_WEB_DIR/package.json" ]]; then
      echo "Installing CAO web dependencies..."
      npm install --prefix "$CAO_WEB_DIR"
    else
      echo "CAO web package.json still missing. Set CAO_WEB_DIR to the web directory."
    fi
  else
    echo "Install git and npm, then clone https://github.com/awslabs/cli-agent-orchestrator.git and set CAO_WEB_DIR."
  fi
fi

"$SCRIPT_DIR/install_agent_profiles.sh"
"$SCRIPT_DIR/setup_agent_worktree.sh"

if [[ "$missing" -ne 0 ]]; then
  echo
  echo "Bootstrap finished with missing downloadable dependencies. See tools/cao_agent/DEPLOYMENT.md."
else
  echo
  echo "Bootstrap finished."
fi
