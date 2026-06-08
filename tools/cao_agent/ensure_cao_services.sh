#!/usr/bin/env bash
set -euo pipefail

API_PORT=9889
WEB_PORT=5173
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

LOG_DIR="$CAO_LOG_DIR"
WEB_DIR="$CAO_WEB_DIR"
API_SESSION="cao_api"
WEB_SESSION="cao_web"
NPM_BIN="${NPM_BIN:-npm}"

mkdir -p "$LOG_DIR"

if ! lsof -nP -iTCP:"$API_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  tmux kill-session -t "$API_SESSION" >/dev/null 2>&1 || true
  tmux new-session -d -s "$API_SESSION" \
    "'$CAO_SERVER_BIN' --host 127.0.0.1 --port $API_PORT >> '$LOG_DIR/cao_server_${API_PORT}.log' 2>&1"
fi

if ! lsof -nP -iTCP:"$WEB_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  if [[ ! -d "$WEB_DIR" ]]; then
    echo "Missing CAO web directory: $WEB_DIR" >&2
    exit 1
  fi
  tmux kill-session -t "$WEB_SESSION" >/dev/null 2>&1 || true
  tmux new-session -d -s "$WEB_SESSION" \
    "cd '$WEB_DIR' && '$NPM_BIN' run dev -- --host 127.0.0.1 --port $WEB_PORT >> '$LOG_DIR/cao_web_${WEB_PORT}.log' 2>&1"
fi

for port in "$API_PORT" "$WEB_PORT"; do
  for _ in {1..20}; do
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1 && break
    sleep 0.5
  done

  if ! lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Service did not start on 127.0.0.1:$port" >&2
    exit 1
  fi
done

curl -fsS --max-time 3 "http://127.0.0.1:$API_PORT/docs" >/dev/null
curl -fsS --max-time 3 "http://127.0.0.1:$WEB_PORT/" >/dev/null

echo "CAO API: http://127.0.0.1:$API_PORT/"
echo "CAO UI: http://127.0.0.1:$WEB_PORT/"
