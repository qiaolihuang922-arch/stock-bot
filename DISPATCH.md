# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗接力。各角色按本文件判斷是否工作。

## Current Task

- task_id: `risk_patch_20260531_holiday_report_execution_memory_evidence_dates`
- task_name: `05/31 Holiday Report Execution Memory And Evidence Date Fix`
- task_type: `risk_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `completed`
- pm_status: `completed`
- tech_status: `completed`
- qa_status: `通過`
- commit: `committed`

## Current Result

- 已完成 05/31 假日报文修复候选并通过 QA。
- 英業達 2356 第二段停利读取 production cross-day execution memory；若 2026-05-29 已卖出 `-112`、`-75`，报文显示已执行不重复，不再输出「本次建議 56 股」或进入明日计划。
- 若 production source 可读但已有 prior take-profit guard、execution memory 缺失或 sold_shares 不足，现在 fail closed：显示「停利記憶不足」，不输出明确重复卖出股数。
- market/theme evidence 用户可见来源改为 actual/latest trade date，并显示 holiday report 使用最近交易日 evidence。
- market/theme trend lookback rows 提高到 240，并显示 lookback_range，避免五月历史被默认 row limit 压成近 2 日。
- `策略證據 v20.0` 增加 strategy sample 层说明，避免样本 0 被误读为 market/theme production evidence 无效。
- 使用者可见版本升到 `v20.4.7`。
- Tech 自检：`tests/test_generator_report.py` 71 passed；`tests/test_market_theme_evidence.py tests/test_cross_day_context.py` 39 passed；`git diff --check` passed。
- QA 复验：`通過`；补充验证 missing / zero execution memory 不再进入明日计划，正常 `-112/-75` memory 仍显示已执行不重复。

## Next Action

- 已提交，待 push 完成后可以继续下一阶段证据链功能扩张；不得跳过本轮执行记忆修复的验证结论。
- 先补 runner gap：auto wrapper 曾把有效 QA `通過` 误判失败；Tech worktree stale diff 曾阻塞新任务，需纳入 runner/worktree hygiene 待办。

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
