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
RUNNER="$BASE/run_online_agent.sh"
OUT_DIR="$CAO_AGENT_OUTPUTS"
mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

RUN_ID="$(date +%Y%m%d_%H%M%S)_$RANDOM"
COMBINED="$OUT_DIR/${RUN_ID}_online_research_pair.md"

PM_PROMPT="你是 PM 線上研究代理。請針對以下問題查公開資料並輸出：
1. 公開證據與來源
2. 產品結論
3. 建議需求 / TASK.md 重點
4. 驗收條件
5. 直接消費者與輸出契約
6. 不確定性

若需要輸出 TASK 草案，必須符合 AGENTS.md 的 PM 任務卡固定欄位；若證據不足，請標記 blocked 或待 Owner 確認。

研究問題：
$QUESTION"

QA_PROMPT="你是 QA 線上研究代理。請針對以下問題查公開資料並輸出：
1. 外部證據
2. 可能的策略盲點
3. 使用者誤讀風險
4. 建議下一步測試
5. 證據性質：即時 / 延遲 / 歷史 / 觀點型
6. 至少一個反向假設或反證方向

不得只附和 PM；若公開資料不足，必須明確標記證據不足。

研究問題：
$QUESTION"

PM_OUT="$("$RUNNER" stock_pm_online_readonly "$PM_PROMPT")"
QA_OUT="$("$RUNNER" stock_qa_online_readonly "$QA_PROMPT")"

{
  echo "# Online Research Pair"
  echo
  echo "- question: $QUESTION"
  echo "- pm_output: $PM_OUT"
  echo "- qa_output: $QA_OUT"
  echo
  echo "## PM Online Research"
  echo
  cat "$PM_OUT"
  echo
  echo "## QA Online Research"
  echo
  cat "$QA_OUT"
} > "$COMBINED"

chmod 600 "$COMBINED"
echo "$COMBINED"
