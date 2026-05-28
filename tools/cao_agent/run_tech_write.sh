#!/usr/bin/env bash
set -euo pipefail

PROMPT="${*:-}"
if [[ -z "$PROMPT" ]]; then
  echo "Usage: $0 <Tech implementation instruction>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

CAO="$CAO_BIN"
CAO_SERVER="$CAO_SERVER_BIN"
REPO="$REPO_ROOT"
WORKTREE="$CAO_TECH_WORKTREE"
OUT_DIR="$CAO_AGENT_OUTPUTS"
LOG_DIR="$CAO_LOG_DIR"
PROFILE="stock_tech_write_sandbox"
READONLY_HANDOFF_FILES=(AGENTS.md DISPATCH.md RESEARCH.md CURRENT_STATE.md CLEANUP_PLAN.md TASK.md QA_REPORT.md)
WRITABLE_HANDOFF_FILES=(CHANGELOG.md)

mkdir -p "$OUT_DIR"
chmod 700 "$CAO_AGENT_CONTEXT" "$OUT_DIR"

ensure_tech_worktree

# Start each Tech run from a clean isolated worktree unless explicitly disabled.
# This worktree is disposable agent scratch space; never use it as the source of truth.
if [[ "${CLEAN_TECH_WORKTREE:-1}" == "1" ]]; then
  TARGET_HEAD="$(git -C "$REPO" rev-parse HEAD)"
  for f in "${READONLY_HANDOFF_FILES[@]}" "${WRITABLE_HANDOFF_FILES[@]}"; do
    git -C "$WORKTREE" update-index --no-skip-worktree "$f" >/dev/null 2>&1 || true
  done
  git -C "$WORKTREE" reset --hard "$TARGET_HEAD" >/dev/null
  git -C "$WORKTREE" clean -fd -e .venv >/dev/null
fi

ensure_worktree_venv() {
  local target_python="$WORKTREE/.venv/bin/python"
  local exclude_file

  exclude_file="$(git -C "$WORKTREE" rev-parse --git-path info/exclude)"
  mkdir -p "$(dirname "$exclude_file")"
  touch "$exclude_file"
  grep -qxF ".venv" "$exclude_file" || echo ".venv" >> "$exclude_file"

  if [[ -x "$target_python" ]] && "$target_python" -m pytest --version >/dev/null 2>&1; then
    return 0
  fi

  if [[ -x "$REPO/.venv/bin/python" ]] && "$REPO/.venv/bin/python" -m pytest --version >/dev/null 2>&1; then
    rm -rf "$WORKTREE/.venv"
    ln -s "$REPO/.venv" "$WORKTREE/.venv"
  else
    rm -rf "$WORKTREE/.venv"
    python3 -m venv "$WORKTREE/.venv"
    "$target_python" -m pip install --upgrade pip >/dev/null
    "$target_python" -m pip install -r "$REPO/requirements.txt" pytest >/dev/null
  fi

  if [[ ! -x "$target_python" ]] || ! "$target_python" -m pytest --version >/dev/null 2>&1; then
    echo "Tech worktree test environment is not available: $target_python" >&2
    exit 1
  fi
}

ensure_worktree_venv

# Sync workflow handoff files from main repo into the isolated worktree.
for f in "${READONLY_HANDOFF_FILES[@]}" "${WRITABLE_HANDOFF_FILES[@]}"; do
  if [[ -f "$REPO/$f" ]]; then
    cp "$REPO/$f" "$WORKTREE/$f"
  fi
done
for f in "${READONLY_HANDOFF_FILES[@]}"; do
  git -C "$WORKTREE" update-index --skip-worktree "$f" >/dev/null 2>&1 || true
done

readonly_hashes() {
  for f in "${READONLY_HANDOFF_FILES[@]}"; do
    if [[ -f "$WORKTREE/$f" ]]; then
      shasum -a 256 "$WORKTREE/$f"
    fi
  done
}
READONLY_BEFORE="$(readonly_hashes)"

SERVER_STARTED=0
if ! lsof -ti tcp:9889 >/dev/null 2>&1; then
  "$CAO_SERVER" > "$LOG_DIR/cao_runner_server.log" 2>&1 &
  SERVER_PID="$!"
  disown "$SERVER_PID" 2>/dev/null || true
  SERVER_STARTED=1
  for _ in {1..20}; do
    lsof -ti tcp:9889 >/dev/null 2>&1 && break
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
  if [[ "${KEEP_CAO_SESSIONS:-0}" != "1" && -n "${SESSION_NAME:-}" ]]; then
    "$CAO" shutdown --session "$SESSION_NAME" >/dev/null 2>&1 || true
  fi
  if [[ "${KEEP_CAO_SESSIONS:-0}" != "1" && "$SERVER_STARTED" == "1" ]]; then
    pids="$(lsof -ti tcp:9889 2>/dev/null || true)"
    [[ -n "$pids" ]] && kill $pids >/dev/null 2>&1 || true
  fi
  if [[ "${KEEP_CAO_SESSIONS:-0}" != "1" ]]; then
    sleep 0.5
    rm -f "$LOG_DIR"/terminal/*.log 2>/dev/null || true
    for f in "$LOG_DIR"/*.log; do
      [[ -f "$f" ]] && : > "$f"
    done
  fi
}
trap cleanup EXIT

LAUNCH_OUT="$("$CAO" launch \
  --agents "$PROFILE" \
  --provider codex \
  --headless \
  --auto-approve \
  --working-directory "$WORKTREE" 2>&1)"

SESSION_NAME="$(printf '%s\n' "$LAUNCH_OUT" | awk '/Session created:/ {print $3; exit}')"
WINDOW_NAME="$(printf '%s\n' "$LAUNCH_OUT" | awk '/Terminal created:/ {print $3; exit}')"

if [[ -z "${SESSION_NAME:-}" || -z "${WINDOW_NAME:-}" ]]; then
  printf '%s\n' "$LAUNCH_OUT" >&2
  echo "Failed to parse CAO session/window." >&2
  exit 1
fi

FULL_PROMPT="你是 Tech 可寫隔離代理。你只能在目前 worktree 實作，不能碰主 repo，不能 commit/push。你的價值是做最小正確 diff，不是把任務擴大。

請依照 TASK.md 與以下 Architect 指令實作：
$PROMPT

要求：
1. 先判斷本輪任務尺寸與風險，寫進 CHANGELOG.md：tiny_patch / normal_patch / risk_patch / research / process。
2. 先找最小影響面：只修改 TASK.md 指定的必要代碼與必要測試；不得順手重構、清理旁支、改策略方向或擴大輸出契約。
3. 更新 CHANGELOG.md，且第一行必須是 # CHANGELOG:。
4. CHANGELOG.md 必須包含：修改內容、修改檔案、最小改動策略、契約影響、直接消費者同步、未影響模組、已跑自檢命令、殘留風險、旁支待辦。
5. 若任務改變回傳結構、訊息順序、payload、報文分組或 public helper，必須同步直接呼叫方並在 CHANGELOG.md 說明。
6. 若任務是清理 / 瘦身 / refactor，CHANGELOG.md 必須包含 path / claim / evidence / risk / action 證據表。
7. 不得為了通過測試寫死 fixture、壓掉真實邊界、或回退既有已修契約；如果 TASK.md 與既有契約衝突，停止並回報 blocked。
8. 測試環境已由 runner 準備；不得因缺 .venv / pytest 繞過測試。若環境仍異常，必須回報 blocked 並列出實際錯誤。
9. 不修改產品方向；若 TASK.md 不清楚、缺直接消費者、缺驗收條件或缺輸出契約，停止並回報 blocked。
10. 不執行 live Telegram、live Supabase write、正式 backfill。
11. 不宣告 QA 通過；Tech 自檢只代表交付前檢查。

End your final answer with this marker on its own line:
$SENTINEL"

"$CAO" session send "$SESSION_NAME" "$FULL_PROMPT" --async >/dev/null

FOUND=0
for _ in {1..900}; do
  tmux capture-pane -t "$SESSION_NAME:$WINDOW_NAME" -p -S -1000 \
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
answer = text[first + len(sentinel):second].strip() if first != -1 and second != -1 else text.strip()
heading = answer.rfind("# CHANGELOG:")
if heading != -1:
    answer = answer[heading:].strip()
answer_path.write_text(answer + "\n", encoding="utf-8")
answer_path.chmod(0o600)
PY

if ! head -n 1 "$ANSWER_FILE" | rg -q '^# CHANGELOG:'; then
  echo "Tech answer did not start with required '# CHANGELOG:' heading: $ANSWER_FILE" >&2
  exit 1
fi

READONLY_AFTER="$(readonly_hashes)"
if [[ "$READONLY_AFTER" != "$READONLY_BEFORE" ]]; then
  echo "Tech modified read-only handoff files; refusing result." >&2
  for f in "${READONLY_HANDOFF_FILES[@]}"; do
    [[ -f "$REPO/$f" ]] && cp "$REPO/$f" "$WORKTREE/$f"
  done
  exit 1
fi

echo "$ANSWER_FILE"
git -C "$WORKTREE" status --short
git -C "$WORKTREE" diff --stat
