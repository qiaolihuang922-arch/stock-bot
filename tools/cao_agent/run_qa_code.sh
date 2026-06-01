#!/usr/bin/env bash
set -euo pipefail

PROMPT="${*:-請驗證目前 tech_write worktree 的 TASK.md / CHANGELOG.md / diff。}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

CAO="$CAO_BIN"
CAO_SERVER="$CAO_SERVER_BIN"
REPO="$REPO_ROOT"
WORKTREE="$CAO_TECH_WORKTREE"
OUT_DIR="$CAO_AGENT_OUTPUTS"
LOG_DIR="$CAO_LOG_DIR"
PROFILE="stock_qa_code_readonly"
QA_TMP="$WORKTREE/.qa_tmp"
READONLY_HANDOFF_FILES=(AGENTS.md DISPATCH.md RESEARCH.md CURRENT_STATE.md CLEANUP_PLAN.md TASK.md CHANGELOG.md QA_REPORT.md)
SERVER_STARTED=0

cleanup() {
  if [[ "${CAO_QA_USE_REPO_CONFIG:-0}" == "1" ]]; then
    if [[ -f "$QA_TMP/config.py.worktree-backup" ]]; then
      cp "$QA_TMP/config.py.worktree-backup" "$WORKTREE/config.py" 2>/dev/null || true
      chmod 600 "$WORKTREE/config.py" 2>/dev/null || true
    else
      rm -f "$WORKTREE/config.py" 2>/dev/null || true
    fi
  fi
  if [[ "${KEEP_CAO_SESSIONS:-0}" != "1" && -n "${SESSION_NAME:-}" ]]; then
    "$CAO" shutdown --session "$SESSION_NAME" >/dev/null 2>&1 || true
  fi
  if [[ "${KEEP_CAO_SESSIONS:-0}" != "1" && "${SERVER_STARTED:-0}" == "1" ]]; then
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

mkdir -p "$OUT_DIR"
chmod 700 "$CAO_AGENT_CONTEXT" "$OUT_DIR"
ensure_tech_worktree
mkdir -p "$QA_TMP"
chmod 700 "$QA_TMP"

exclude_file="$(git -C "$WORKTREE" rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$exclude_file")"
touch "$exclude_file"
grep -qxF ".qa_tmp" "$exclude_file" || echo ".qa_tmp" >> "$exclude_file"

if [[ "${CAO_QA_USE_REPO_CONFIG:-0}" != "1" ]]; then
cat > "$QA_TMP/config.py" <<'EOF'
SUPABASE_URL = "http://localhost"
SUPABASE_KEY = "test"
SUPABASE_SERVICE_ROLE_KEY = "test"
TELEGRAM_BOT_TOKEN = "test"
TELEGRAM_CHAT_ID = "test"
TOKEN = "test"
CHAT_ID = "test"
GITHUB_TOKEN = "test"
GITHUB_REPO = "test/test"
GITHUB_WORKFLOW_FILE = "test.yml"
EOF
chmod 600 "$QA_TMP/config.py"
else
  if [[ ! -f "$REPO/config.py" ]]; then
    echo "CAO_QA_USE_REPO_CONFIG=1 requested but repo config.py is missing" >&2
    exit 1
  fi
  cp "$REPO/config.py" "$QA_TMP/config.py"
  if [[ -f "$WORKTREE/config.py" ]]; then
    cp "$WORKTREE/config.py" "$QA_TMP/config.py.worktree-backup"
    chmod 600 "$QA_TMP/config.py.worktree-backup"
  fi
  cp "$REPO/config.py" "$WORKTREE/config.py"
  chmod 600 "$QA_TMP/config.py"
  chmod 600 "$WORKTREE/config.py"
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
    echo "QA worktree test environment is not available: $target_python" >&2
    exit 1
  fi
}

ensure_worktree_venv

# QA must validate the latest Architect/Tech handoff from the main repo, not a
# stale copy left in the reusable agent worktree.
for f in "${READONLY_HANDOFF_FILES[@]}"; do
  if [[ -f "$REPO/$f" ]]; then
    cp "$REPO/$f" "$WORKTREE/$f"
  fi
done

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

RUN_ID="$(date +%Y%m%d_%H%M%S)_$RANDOM"
SENTINEL="CAO_DONE_$RUN_ID"
OUT_FILE="$OUT_DIR/${RUN_ID}_${PROFILE}.txt"
ANSWER_FILE="$OUT_DIR/${RUN_ID}_${PROFILE}.answer.txt"
BEFORE_DIFF_HASH="$(git -C "$WORKTREE" diff --binary | shasum -a 256 | awk '{print $1}')"
readonly_hashes() {
  for f in "${READONLY_HANDOFF_FILES[@]}"; do
    if [[ -f "$WORKTREE/$f" ]]; then
      shasum -a 256 "$WORKTREE/$f"
    fi
  done
}
READONLY_BEFORE="$(readonly_hashes)"

LAUNCH_OUT="$(TMPDIR="$QA_TMP" PYTHONPATH="$QA_TMP:$WORKTREE" "$CAO" launch \
  --agents "$PROFILE" \
  --provider codex \
  --headless \
  --auto-approve \
  --working-directory "$WORKTREE" 2>&1)"

SESSION_NAME="$(printf '%s\n' "$LAUNCH_OUT" | awk '/Session created:/ {print $3; exit}')"
WINDOW_NAME="$(printf '%s\n' "$LAUNCH_OUT" | awk '/Terminal created:/ {print $3; exit}')"

FULL_PROMPT="你是 QA 代碼只讀代理。請驗證目前 worktree 的任務結果。你的價值是抓真正風險，不是把小任務驗成大專案。

Architect 指令：
$PROMPT

請讀取 TASK.md、CHANGELOG.md、必要 git diff 與相關檔案，輸出可寫入 QA_REPORT.md 的報告。
不得修改檔案。

硬性驗收：
1. 先判斷 QA 風險預算並寫入 QA_REPORT.md：本輪最值得抓的 1-3 個風險、對應驗證、停止條件。
2. 驗證範圍必須匹配 TASK.md 的任務尺寸與 qa_level；tiny_patch 不得無理由擴成 full pytest / replay / backfill / evidence 全矩陣。
3. 若 TASK.md / CHANGELOG.md / git diff 不一致，必須標記 blocked 或 conditional pass，不得通過。
4. 若清理 / 瘦身 / refactor 任務缺 path / claim / evidence / risk / action 證據表，必須 blocked。
5. 必須明確區分可吸收 diff 與 worktree 殘留，不得建議整包合併。
6. 測試環境已由 runner 準備；不得因缺 .venv / pytest 跳過應跑測試。若環境仍異常，必須標記 blocked 並列出實際錯誤。
7. 最終輸出第一行必須是 # QA_REPORT:。
8. 必須包含：測試範圍、風險預算與停止條件、關聯風險掃描、跨區塊語意一致性、使用者誤讀風險、質疑與反證、未測項目、QA 結論。
9. 不得只重跑 Tech 自檢；至少補一個 Tech 未覆蓋的直接消費者、負面案例、使用者誤讀路徑或契約風險。
10. 對 Telegram / summary / dashboard 等使用者可見輸出，必須按 Owner 手機閱讀順序檢查。
11. 旁支問題除非阻塞本輪驗收，否則列為後續風險，不得擴大本輪驗證。
12. 若沒有主動質疑或反證，不能給通過，只能 conditional pass 或 blocked。
13. 不得修改任何 tracked file；runner 只允許你使用 .qa_tmp/ 作為測試暫存。可用環境：TMPDIR=${QA_TMP}，PYTHONPATH=${QA_TMP}:${WORKTREE}。若 Architect 已用 CAO_QA_USE_REPO_CONFIG=1 啟動本 runner，可執行 read-only production smoke；不得輸出 credential 值。

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
heading = answer.rfind("# QA_REPORT:")
if heading != -1:
    answer = answer[heading:].strip()
answer_path.write_text(answer + "\n", encoding="utf-8")
answer_path.chmod(0o600)
PY

if ! head -n 1 "$ANSWER_FILE" | rg -q '^# QA_REPORT:'; then
  echo "QA answer did not start with required '# QA_REPORT:' heading: $ANSWER_FILE" >&2
  exit 1
fi

AFTER_DIFF_HASH="$(git -C "$WORKTREE" diff --binary | shasum -a 256 | awk '{print $1}')"
if [[ "$AFTER_DIFF_HASH" != "$BEFORE_DIFF_HASH" ]]; then
  echo "QA modified tracked diff; refusing result." >&2
  exit 1
fi

READONLY_AFTER="$(readonly_hashes)"
if [[ "$READONLY_AFTER" != "$READONLY_BEFORE" ]]; then
  echo "QA modified handoff files; refusing result." >&2
  exit 1
fi

echo "$ANSWER_FILE"
