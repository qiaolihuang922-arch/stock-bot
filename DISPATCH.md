# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗接力。各角色按本文件判斷是否工作。

## Current Task

- task_id: `correction-daily-signal-snapshot-history-semantics`
- task_name: `Correction Audit Daily Signal Snapshot History Semantics`
- task_type: `normal_patch`
- version_level: `none`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `completed`
- pm_status: `completed`
- tech_status: `completed`
- qa_status: `通過`
- commit: `pending`

## Current Result

- 已修 correction audit 的 `daily_signal_snapshot` 語義：歷史 coverage 依 daily-version-as-recorded 全版本檢查；current `core/generator.py VERSION` 只作 run-health diagnostic。
- current `v20.4.6` 舊五月 0 rows 現在輸出 `diagnostic=current_version_old_month_zero_rows` 且 `blocks_history_coverage=false`，不再被當成五月歷史 backfill blocker。
- QA 結論：`通過`。QA 反證 market/theme latest-only / mapping-only 仍 blocked，且 `next_action` 不再要求 daily snapshot current VERSION backfill。
- Architect 用正確 arm64 interpreter 補跑 production read-only audit：`daily_signal_snapshot.history_coverage.conclusion=covered`，全版本 936 rows / 20 trading days；current version 0 rows 僅診斷。
- market/theme 三表 production 現況仍 blocked：`market_theme_confirmed_evidence` 18 rows only `2026-05-29` 且 9 duplicate business-key groups；`market_theme_index_daily_bars` 10 rows only `2026-05-29`；`sector_theme_members` 12 active mapping rows from `2026-01-01`，不是五月 daily history。

## Next Action

- 開下一張 PM 任務：實作 market/theme historical fetch 與 confirmed evidence dedupe。
- 抓取任務必須用 production DB / repo script / approved service API 寫入，不要求 Owner 手寫普通 DML；若需要新增表、擴字段、index / constraint、RLS / grant / policy，先產 SQL 給 Owner。
- 完成後重跑 `--correction-audit-json`，必須看到 market/theme 五月 coverage 不再 latest-only，duplicate business-key groups 清零或有明確去重規則，才能繼續證據鏈功能擴張。

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
