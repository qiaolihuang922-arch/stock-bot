#!/usr/bin/env bash
set -euo pipefail

QUESTION="${*:-}"

if [[ -z "$QUESTION" ]]; then
  echo "Usage: $0 <研究問題>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

BASE="$CAO_AGENT_DIR"
REPO="$REPO_ROOT"
PAIR_RUNNER="$BASE/run_research_pair.sh"
OUT_DIR="$CAO_AGENT_OUTPUTS"

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

PAIR_OUT="$("$PAIR_RUNNER" "$QUESTION")"
RUN_ID="$(basename "$PAIR_OUT" .md)"
RESEARCH="$REPO/RESEARCH.md"

PM_FILE="$(awk -F': ' '/^- pm_output:/ {print $2; exit}' "$PAIR_OUT")"
QA_FILE="$(awk -F': ' '/^- qa_output:/ {print $2; exit}' "$PAIR_OUT")"

if [[ ! -f "$PM_FILE" || ! -f "$QA_FILE" ]]; then
  echo "Missing PM or QA output from pair run: $PAIR_OUT" >&2
  exit 1
fi

cat > "$RESEARCH" <<EOF
# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research

- task_id: \`$RUN_ID\`
- 日期：$(date '+%Y-%m-%d')
- 狀態：CAO online PM / QA research ready，等待 Architect 吸收結論
- 來源輸出：\`$PAIR_OUT\`

## Question

$QUESTION

## Evidence

- 本輪由 Architect 本地 runner 觸發 CAO online read-only PM / QA。
- Online agent 工作目錄：\`$CAO_ONLINE_CONTEXT\`。
- Online agent 可查公開網路資料，但不直接讀真實 repo、不改代碼、不寫固定 8 份 Markdown。
- Tech write 只在隔離 worktree 產生候選 diff；若研究結論需要開發，需由 Architect 轉成 \`TASK.md\` 後交給 Tech。

## PM Findings

$(cat "$PM_FILE")

## QA Findings

$(cat "$QA_FILE")

## Architect Conclusion

- 待 Architect 判斷：本研究是否進入 \`TASK.md\`、繼續研究、或暫不處理。
- 若進入開發，必須按 \`AGENTS.md\` 標準流程分派，不得讓 CAO online agent 直接改 repo。

## Next Action

- Architect review。
EOF

chmod 600 "$RESEARCH"
echo "$RESEARCH"
