#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

required_role_fields=(
  mission
  inputs
  allowed_actions
  forbidden_actions
  output_schema
  conflict_priority
  block_conditions
  self_check
  handoff_contract
  aligned_to
)

fail() {
  printf 'agent profile contract gate failed: %s\n' "$*" >&2
  exit 2
}

require_rg() {
  local pattern="$1"
  local file="$2"
  rg -q -- "$pattern" "$file" || fail "missing pattern '$pattern' in $file"
}

for profile in tools/cao_agent/profiles/stock_*.md.template; do
  for field in "${required_role_fields[@]}"; do
    require_rg "^- ${field}：" "$profile"
  done
  require_rg "_common_boundaries.md" "$profile"
done

for section in \
  "任務狀態" \
  "Owner 問題" \
  "使用者可見結果" \
  "非目標" \
  "影響模組與直接消費者" \
  "輸出契約" \
  "版本契約" \
  "驗收條件" \
  "範例或 Fixture" \
  "明確禁止事項" \
  "阻塞條件" \
  "本輪停止條件"
do
  require_rg "\`$section\`" tools/cao_agent/profiles/stock_pm_safe.md.template
  require_rg "\`$section\`" tools/cao_agent/profiles/stock_pm_online_readonly.md.template
done

for section in \
  "任務尺寸與風險" \
  "修改內容" \
  "修改檔案" \
  "最小改動策略" \
  "契約影響" \
  "直接消費者同步" \
  "未影響模組" \
  "已跑自檢命令" \
  "殘留風險" \
  "旁支待辦"
do
  require_rg "\`$section\`" tools/cao_agent/profiles/stock_tech_write_sandbox.md.template
done

for section in \
  "測試範圍" \
  "關聯風險掃描" \
  "跨區塊語意一致性" \
  "使用者誤讀風險" \
  "質疑與反證" \
  "未測項目" \
  "QA 結論"
do
  require_rg "\`$section\`" tools/cao_agent/profiles/stock_qa_safe.md.template
  require_rg "\`$section\`" tools/cao_agent/profiles/stock_qa_code_readonly.md.template
done

require_rg "^## Active$" DISPATCH.md
require_rg "^## Queued$" DISPATCH.md
require_rg "^## Recently Done$" DISPATCH.md
require_rg "task_md_holds:" DISPATCH.md
if rg -q "^## Current Task$|^## Current Follow-up$" DISPATCH.md; then
  fail "DISPATCH.md still uses legacy Current Task / Current Follow-up slots"
fi

require_rg "標準啟動順序固定為：\`AGENTS.md\` -> \`DISPATCH.md\` -> \`CURRENT_STATE.md\`" AGENTS.md
require_rg "依 \`AGENTS.md\` 啟動順序閱讀" DISPATCH.md
require_rg "依 \`AGENTS.md\` 啟動順序閱讀" CURRENT_STATE.md

echo "agent profile contract gate passed"
