#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tools/cao_agent/env.sh
source "$SCRIPT_DIR/env.sh"

escape_sed() {
  printf '%s' "$1" | sed -e 's/[\/&]/\\&/g'
}

render_template() {
  local template="$1"
  local output="$2"
  sed \
    -e "s/__CAO_MCP_SERVER_BIN__/$(escape_sed "$CAO_MCP_SERVER_BIN")/g" \
    -e "s/__REPO_ROOT__/$(escape_sed "$REPO_ROOT")/g" \
    -e "s/__CAO_ONLINE_CONTEXT__/$(escape_sed "$CAO_ONLINE_CONTEXT")/g" \
    -e "s/__CAO_TECH_WORKTREE__/$(escape_sed "$CAO_TECH_WORKTREE")/g" \
    "$template" > "$output"
  chmod 600 "$output"
}

ensure_agent_dirs
mkdir -p "$CAO_AGENT_PROFILE_DIR"
chmod 700 "$CAO_AGENT_PROFILE_DIR"

for template in "$SCRIPT_DIR"/profiles/stock_*.md.template; do
  name="$(basename "$template" .template)"
  render_template "$template" "$CAO_AGENT_PROFILE_DIR/$name"
done

echo "Installed stock agent profiles to: $CAO_AGENT_PROFILE_DIR"
