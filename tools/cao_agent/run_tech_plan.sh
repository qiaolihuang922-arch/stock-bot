#!/usr/bin/env bash
set -euo pipefail

PROMPT="${*:-}"

if [[ -z "$PROMPT" ]]; then
  echo "Usage: $0 <技術規劃問題>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

CAO="$CAO_BIN"
CAO_SERVER="$CAO_SERVER_BIN"
REPO="$REPO_ROOT"
CTX="$CAO_TECH_PLAN_CONTEXT"
OUT_DIR="$CAO_AGENT_OUTPUTS"
LOG_DIR="$CAO_LOG_DIR"
PROFILE="stock_tech_safe"

mkdir -p "$CTX" "$OUT_DIR"
chmod 700 "$CAO_AGENT_CONTEXT" "$CTX" "$OUT_DIR"

# Refresh safe summary context only. Source files are not copied automatically.
for f in AGENTS.md CURRENT_STATE.md DISPATCH.md RESEARCH.md TASK.md CHANGELOG.md QA_REPORT.md; do
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

FULL_PROMPT="你是 Tech 安全代理。請只根據 tech_plan 目錄內的摘要文件進行技術規劃。你的價值是找最小可行路徑，不是把規劃擴成大工程。

請輸出：
1. 是否 blocked
2. 任務尺寸與風險判斷：tiny_patch / normal_patch / risk_patch / research / process
3. 需要 Architect / PM 補充的問題
4. 最小影響面與不應觸碰的模組
5. 建議修改檔案
6. 契約影響與直接消費者
7. 實作步驟
8. 最小自檢命令
9. 旁支待辦與不允許 Tech 自行處理的項目

不得修改檔案，不得讀取真實 repo，不得查網。
若 TASK.md 缺直接消費者、驗收條件或輸出契約，必須標記 blocked，不得自行補 PM 需求。

技術規劃問題：
$PROMPT

End your final answer with this marker on its own line:
$SENTINEL"

"$CAO" session send "$SESSION_NAME" "$FULL_PROMPT" --async >/dev/null

FOUND=0
for _ in {1..300}; do
  tmux capture-pane -t "$SESSION_NAME:$WINDOW_NAME" -p -S -500 \
    | perl -pe 's/\e\[[0-9;?]*[A-Za-z]//g' > "$OUT_FILE.tmp"
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
