# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗接力。各角色按本文件判斷是否工作。

## Current Task

- task_id: `correction-market-theme-prod-coverage-2026-05`
- task_name: `Market Theme 2026-05 Historical Fetch And Dedupe`
- task_type: `risk_patch`
- version_level: `none`
- qa_level: `L3`
- owner_status: `requested`
- architect_status: `completed`
- pm_status: `completed`
- tech_status: `completed`
- qa_status: `通過`
- commit: `pushed`

## Current Result

- 已完成 market/theme 2026-05 historical fetch 與 confirmed evidence dedupe。
- 使用 repo script 寫入 production DB，非手寫普通 DML，無 schema / RLS / grant / policy / index / constraint 變更。
- 寫入結果：`market_theme_confirmed_evidence` 180 rows，`market_theme_index_daily_bars` 200 rows，日期範圍 `2026-05-04` 到 `2026-05-29`，20 trade dates。
- 獨立 read-only audit：`status=pass`，`next_action=["read_only_audit_complete"]`。
- duplicate groups：confirmed evidence 0，index bars 0。
- `sector_theme_members` 維持 `mapping_only`，不計入 daily history。
- `daily_signal_snapshot` 維持 daily-version-as-recorded 語義：history covered，current `v20.4.6` May 0 rows 只作 diagnostic。
- 完整檢查已完成：full pytest 261 passed；production trend consumption check `fresh_runner_rebuild=passed`，generator path 已消費 production `market_theme_confirmed_evidence` history，未使用 daily_signal_snapshot / runtime / local cache 作 market/theme evidence。

## Next Action

- 可以開始下一階段證據鏈功能擴張：把 production `market_theme_confirmed_evidence` history trend 轉成更明確的策略提示 / 題材證據呈現。
- 先補 runner gap：QA runner 對 production read-only audit 任務不能固定 dummy Supabase config，否則會把已完成的 production audit 誤判 blocked。
- 若下一階段涉及 schema 變更，仍需先給 Owner SQL；普通資料寫入仍走 repo script / service API。

## Status Values

- `todo`: 等待該角色處理。
- `not_required`: 本輪不需要該角色。
- `in_progress`: Architect 正在處理。
- `blocked`: 遇到阻塞。
- `completed`: 已完成未推送。
- `pushed`: 已提交並推送。

## Fixed Startup Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。先讀 AGENTS.md 和 DISPATCH.md；產品 bug / 顯示 bug / 策略 bug / feature request 先分派 PM，不直接寫 TASK.md、不搜尋或修改產品代碼。Owner 說「開始、繼續、處理、修復、檢查、清理、直接來」只代表啟動流程；只有當前任務明確、限範圍授權，Architect 才可代 PM / Tech / QA。
```

Architect CAO 入口：

```text
研究：tools/cao_agent/run_architect_task.sh research "<研究問題>"
規劃：tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
自動開發：tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"

CAO 服務確認：tools/cao_agent/ensure_cao_services.sh
分配或回覆 CAO 前端地址前，先確認 http://127.0.0.1:9889/ 與 http://127.0.0.1:5173/ 已啟動。
```

Owner 對 PM：

```text
讀 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md。若 pm_status 是 todo 或 Architect 指定 PM，撰寫 # TASK:，不修改代碼。
```

Owner 對 Tech：

```text
讀 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md。若 tech_status 是 todo 且 TASK.md ready，依 TASK.md 實作並撰寫 # CHANGELOG:；缺直接消費者、驗收條件或輸出契約則 blocked。
```

Owner 對 QA：

```text
讀 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md。若 qa_status 是 todo 且 Tech 已交付，按 qa_level 驗證並撰寫 # QA_REPORT:；不能只重跑 Tech 測試。
```

Owner 回到 Architect：

```text
讀 DISPATCH.md、TASK.md、CHANGELOG.md、QA_REPORT.md，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
