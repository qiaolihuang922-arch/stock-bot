# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗接力。各角色按本文件判斷是否工作。

## Current Task

- task_id: `rules-and-agent-doc-compression-2026-05-30`
- task_name: `Rules And Agent File Compression`
- task_type: `process`
- version_level: `none`
- qa_level: `process`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `not_required`
- tech_status: `not_required`
- qa_status: `not_required`
- commit: `pushed`

## Current Result

- Owner 要求清除規則文件內過時 / 淘汰內容，把留下的規則壓短但不丟失職責與保護力，包含 CAO agent 文件。
- 本輪是流程文件治理，不處理產品代碼、不新增 DB schema、不 live write、不 live Telegram。
- 目標：`AGENTS.md` 留抽象規則；`CURRENT_STATE.md` 留短上下文；`CLEANUP_PLAN.md` 留案例 / 待補；agent profiles 留角色卡、安全邊界與輸出契約。

## Next Action

- 提交並推送本輪規則文件與 agent profile 壓縮；後續回到 correction audit 時，仍須先解決 QA blocked 的 production read-only audit。

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
