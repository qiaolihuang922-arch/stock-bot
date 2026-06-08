#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-}"
shift || true
PROMPT="${*:-}"

if [[ -z "$PROFILE" || -z "$PROMPT" ]]; then
  echo "Usage: $0 <stock_pm_online_readonly|stock_qa_online_readonly> <prompt>" >&2
  exit 2
fi

case "$PROFILE" in
  stock_pm_online_readonly|stock_qa_online_readonly) ;;
  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

CAO="$CAO_BIN"
CAO_SERVER="$CAO_SERVER_BIN"
REPO="$REPO_ROOT"
CTX="$CAO_ONLINE_CONTEXT"
OUT_DIR="$CAO_AGENT_OUTPUTS"
LOG_DIR="$CAO_LOG_DIR"

ensure_agent_dirs
mkdir -p "$CTX"
chmod 700 "$CAO_AGENT_CONTEXT" "$CTX" "$OUT_DIR" "$LOG_DIR"

# Refresh sanitized context only. Do not copy source, hidden files, or secrets.
for f in AGENTS.md CURRENT_STATE.md DISPATCH.md RESEARCH.md TASK.md; do
  if [[ -f "$REPO/$f" ]]; then
    cp "$REPO/$f" "$CTX/$f"
    chmod 600 "$CTX/$f"
  fi
done

SERVER_STARTED=0
if ! lsof -ti tcp:9889 >/dev/null 2>&1; then
  "$CAO_SERVER" > "$LOG_DIR/cao_runner_server.log" 2>&1 &
  SERVER_PID="$!"
  disown "$SERVER_PID" 2>/dev/null || true
  SERVER_STARTED=1
  for _ in {1..20}; do
    if lsof -ti tcp:9889 >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

if ! lsof -ti tcp:9889 >/dev/null 2>&1; then
  echo "CAO server did not start on 127.0.0.1:9889" >&2
  exit 1
fi

RUN_ID="$(date +%Y%m%d_%H%M%S)_$RANDOM"
SENTINEL="CAO_DONE_$RUN_ID"
OUT_FILE="$OUT_DIR/${RUN_ID}_${PROFILE}.txt"
ANSWER_FILE="$OUT_DIR/${RUN_ID}_${PROFILE}.answer.txt"

cleanup() {
  if [[ -n "${SESSION_NAME:-}" ]]; then
    "$CAO" shutdown --session "$SESSION_NAME" >/dev/null 2>&1 || true
  fi
  if [[ "$SERVER_STARTED" == "1" ]]; then
    pids="$(lsof -ti tcp:9889 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      kill $pids >/dev/null 2>&1 || true
      if [[ -n "${SERVER_PID:-}" ]]; then
        wait "$SERVER_PID" 2>/dev/null || true
      fi
    fi
  fi
  sleep 0.5
  rm -f "$LOG_DIR"/terminal/*.log 2>/dev/null || true
  for f in "$LOG_DIR"/*.log; do
    [[ -f "$f" ]] && : > "$f"
  done
}
trap cleanup EXIT

LAUNCH_OUT="$("$CAO" launch \
  --agents "$PROFILE" \
  --provider codex \
  --headless \
  --auto-approve \
  --working-directory "$CTX" 2>&1)"

SESSION_NAME="$(printf '%s\n' "$LAUNCH_OUT" | awk '/Session created:/ {print $3; exit}')"
WINDOW_NAME="$(printf '%s\n' "$LAUNCH_OUT" | awk '/Terminal created:/ {print $3; exit}')"

if [[ -z "${SESSION_NAME:-}" || -z "${WINDOW_NAME:-}" ]]; then
  printf '%s\n' "$LAUNCH_OUT" >&2
  echo "Failed to parse CAO session/window." >&2
  exit 1
fi

FULL_PROMPT="$PROMPT

End your final answer with this marker on its own line:
$SENTINEL"

"$CAO" session send "$SESSION_NAME" "$FULL_PROMPT" --async >/dev/null

FOUND=0
for _ in {1..300}; do
  tmux capture-pane -t "$SESSION_NAME:$WINDOW_NAME" -p -S -500 \
    | perl -pe 's/\e\[[0-9;?]*[A-Za-z]//g' > "$OUT_FILE.tmp"
  # The prompt itself contains the sentinel once. Completion requires the agent
  # to echo it back, so wait for at least two occurrences.
  SENTINEL_COUNT="$(rg -o "$SENTINEL" "$OUT_FILE.tmp" 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${SENTINEL_COUNT:-0}" -ge 2 ]]; then
    FOUND=1
    break
  fi
  sleep 1
done

mv "$OUT_FILE.tmp" "$OUT_FILE"
chmod 600 "$OUT_FILE"

if [[ "$FOUND" != "1" ]]; then
  echo "Timed out waiting for $SENTINEL. Captured output: $OUT_FILE" >&2
  exit 1
fi

python3 - "$OUT_FILE" "$ANSWER_FILE" "$SENTINEL" <<'PY'
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
answer_path = Path(sys.argv[2])
sentinel = sys.argv[3]

text = raw_path.read_text(errors="replace")
first = text.find(sentinel)
second = text.find(sentinel, first + len(sentinel)) if first != -1 else -1

if first != -1 and second != -1:
    answer = text[first + len(sentinel):second].strip()
else:
    answer = text.strip()

answer_path.write_text(answer + "\n", encoding="utf-8")
answer_path.chmod(0o600)
PY

echo "$ANSWER_FILE"
