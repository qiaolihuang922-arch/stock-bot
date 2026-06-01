#!/usr/bin/env bash
set -euo pipefail

OWNER_TASK="${*:-}"
if [[ -z "$OWNER_TASK" ]]; then
  echo "Usage: $0 <Owner task>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

REPO="$REPO_ROOT"
WORKTREE="$CAO_TECH_WORKTREE"
CTX="$CAO_AGENT_DIR"
OUT_DIR="$CAO_AGENT_OUTPUTS"

mkdir -p "$OUT_DIR"
chmod 700 "$CTX" "$OUT_DIR"
ensure_tech_worktree

RUN_ID="$(date +%Y%m%d_%H%M%S)_$RANDOM"
SUMMARY="$OUT_DIR/${RUN_ID}_auto_dev_cycle.md"

{
  echo "# Auto Dev Cycle"
  echo
  echo "- run_id: $RUN_ID"
  echo "- owner_task: $OWNER_TASK"
  echo "- repo: $REPO"
  echo "- worktree: $WORKTREE"
  echo
} > "$SUMMARY"
chmod 600 "$SUMMARY"

fail_cycle() {
  local stage="$1"
  local detail="$2"
  {
    echo
    echo "## FAILED"
    echo
    echo "- stage: $stage"
    echo "- detail: $detail"
  } >> "$SUMMARY"
  echo "$SUMMARY"
  exit 1
}

extract_task_md() {
  local src="$1"
  local dst="$2"
  python3 - "$src" "$dst" <<'PY'
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(errors="replace")
lines = text.splitlines()

start = None
for idx, line in enumerate(lines):
    cleaned = re.sub(r"^[\s•>\-\u2502]+", "", line).strip()
    if cleaned.startswith("# TASK"):
        start = idx
        break

if start is None:
    raise SystemExit("No '# TASK' heading found in PM answer")

out = []
for line in lines[start:]:
    if line.startswith("---") and "CAO_DONE_" in line:
        break
    cleaned = re.sub(r"^[\s•>\u2502]+", "", line.rstrip())
    out.append(cleaned)

while out and not out[-1].strip():
    out.pop()

dst.write_text("\n".join(out).strip() + "\n", encoding="utf-8")
PY
}

PM_PROMPT="你是 stock-bot 的 PM。請根據 Owner 任務輸出 TASK.md。你的價值是收斂問題，不是把小 bug 寫成大工程。

Owner 任務：
$OWNER_TASK

要求：
- 只輸出 TASK.md 內容，不要寒暄。
- Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 直接來」只代表啟動流程；不得把它解讀成 Architect 或 PM 可跳過 Tech / QA 或直接改代碼。
- 必須從 # TASK: 開始。
- 必須包含：任務狀態、Owner 問題、使用者可見結果、非目標、影響模組、直接消費者、輸出契約、驗收條件、範例或 fixture、明確禁止事項、阻塞條件、QA 分級建議。
- 先判斷任務尺寸：tiny_patch / normal_patch / risk_patch / research / process。若是 tiny_patch，TASK.md 必須收斂在單一主 bug、單一輸出契約、1-2 個驗收案例，不得順手擴成策略重設、全量清理或 L3 驗證。
- 必須寫出本輪停止條件：驗到哪裡算完成、哪些旁支問題只記待辦不納入本輪。
- 必須列出已存在且不得回退的契約；若不確定，寫 blocked 或要求 Architect 補充，不要自己假設。
- 報文 / Telegram / UI 任務必須給手機閱讀路徑與示例輸出形狀。
- 若需求不足，仍先寫 blocked TASK.md，說明缺什麼。"

if ! PM_ANSWER="$("$CTX/run_online_agent.sh" stock_pm_online_readonly "$PM_PROMPT" | tail -1)"; then
  fail_cycle "PM" "PM runner failed"
fi

TASK_CLEAN="$OUT_DIR/${RUN_ID}_TASK.clean.md"
if ! extract_task_md "$PM_ANSWER" "$TASK_CLEAN"; then
  fail_cycle "PM" "PM answer did not contain a clean TASK.md heading: $PM_ANSWER"
fi

cp "$TASK_CLEAN" "$REPO/TASK.md"
cp "$TASK_CLEAN" "$WORKTREE/TASK.md"

{
  echo "## PM"
  echo
  echo "- TASK.md source: $PM_ANSWER"
  echo "- TASK.md cleaned: $TASK_CLEAN"
  echo "- TASK.md written to repo and worktree"
  echo
} >> "$SUMMARY"

if ! TECH_ANSWER="$("$CTX/run_tech_write.sh" "請依 TASK.md 完成本輪任務。")"; then
  fail_cycle "Tech" "Tech runner failed"
fi

{
  echo "## Tech"
  echo
  echo '```text'
  printf '%s\n' "$TECH_ANSWER"
  echo '```'
  echo
} >> "$SUMMARY"

if [[ -f "$WORKTREE/CHANGELOG.md" ]]; then
  if ! rg -q '^# CHANGELOG:' "$WORKTREE/CHANGELOG.md"; then
    fail_cycle "Tech" "CHANGELOG.md missing required '# CHANGELOG:' heading"
  fi
  for required in '契約影響' '直接消費者' '未影響模組' '自檢'; do
    if ! rg -q "$required" "$WORKTREE/CHANGELOG.md"; then
      fail_cycle "Tech" "CHANGELOG.md missing required section: $required"
    fi
  done
else
  fail_cycle "Tech" "CHANGELOG.md missing in worktree"
fi

if ! QA_ANSWER="$("$CTX/run_qa_code.sh" "請驗證本輪自動開發循環：TASK.md、CHANGELOG.md、git diff、直接消費者與使用者誤讀風險。")"; then
  fail_cycle "QA" "QA runner failed"
fi
if ! rg -q '^# QA_REPORT:' "$QA_ANSWER"; then
  fail_cycle "QA" "QA report missing required '# QA_REPORT:' heading"
fi
for required in '質疑與反證' '使用者誤讀風險' '關聯風險掃描' 'QA 結論'; do
  if ! rg -q "$required" "$QA_ANSWER"; then
    fail_cycle "QA" "QA report missing required section: $required"
  fi
done
if ! python3 - "$QA_ANSWER" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
matches = list(re.finditer(r"^(?:#+\s*)?QA 結論(?:\s*$|[：:])", text, re.M))
if not matches:
    raise SystemExit(1)
tail = text[matches[-1].end():]
if not re.search(r"\b(通過|阻塞|conditional pass)\b", tail):
    raise SystemExit(1)
PY
then
  fail_cycle "QA" "QA report conclusion must be 通過, 阻塞, or conditional pass"
fi
cp "$WORKTREE/CHANGELOG.md" "$REPO/CHANGELOG.md"
cp "$QA_ANSWER" "$REPO/QA_REPORT.md"
cp "$QA_ANSWER" "$WORKTREE/QA_REPORT.md"

{
  echo "## QA"
  echo
  echo "- QA_REPORT.md source: $QA_ANSWER"
  echo
  echo "## Worktree Diff"
  echo
  echo '```text'
  git -C "$WORKTREE" status --short
  git -C "$WORKTREE" diff --stat
  echo '```'
} >> "$SUMMARY"

echo "$SUMMARY"
