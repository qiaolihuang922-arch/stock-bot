# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_chain_approval_package_20260530`
- task_name: `Evidence Chain Approval Package Generator`
- task_type: `risk_patch`
- version_level: `none`
- qa_level: `L2+`
- owner_status: `requested`
- architect_status: `qa_passed_pending_commit`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要求繼續證據鏈，並追問「為什麼要人工 SQL」。本輪把人工 SQL 往前收斂成 repo-side controlled approval package / write plan；仍不做 live write。
- 本輪完成 non-live approval package generator：
  - 新增 `scripts/generate_evidence_approval_package.py`。
  - 輸入 Owner-approved payload 後，可輸出 `approval_package.json`、`approval_package.md`，以及 validation passed 且 source allowed 時的 deterministic review-only SQL。
  - package 固定標示 `schema_decision=no-schema-change`、`mode=non-live-approval-package`、`write_execution=disabled`。
  - SQL header 明確標示 Owner manual approval required、Agent did not execute this SQL、This package is not evidence of production deployment。
  - forbidden / missing / mixed source family fail closed，不產生 SQL。
- 本輪沒有 live Supabase write、沒有正式 backfill、沒有 production RLS / grant 變更、沒有 live Telegram、沒有改策略 decision 或使用者可見 Telegram version。
- QA 通過：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：36 passed, 17 warnings。
  - forbidden runtime payload exit 2，`deterministic_sql=None`。
  - allowed owner-approved persistent payload exit 0，寫出 package JSON / Markdown / SQL。
  - `py_compile`、`git diff --check` 通過。
  - QA 額外反證：fixture-derived source fail closed、secret-like `postgres://` payload 不產生 SQL、generator 無 Supabase client / insert / upsert / rpc / execute / Telegram delivery pattern。
- Runner 狀態：CAO auto cycle 再次把 QA 明確 `通過` 誤判為 failed；Architect 按 QA 報告與主 repo 驗證手動吸收，未整包搬 worktree。
- Post-cycle review：
  - 根因分類：`manual_sql_operator_risk` + `approval_flow_gap` + `runner_parser_false_fail`。
  - QA 有效覆蓋誤讀、fake source 與 live side-effect 風險。
  - 不新增 `AGENTS.md` 硬規則；既有 source-of-truth、fake confirmed、live write 禁令已覆蓋。本輪沉澱為 generator contract、tests、handoff docs 與 runner 待補。

## Next Action

- Architect 進行 commit / push，然後清理 CAO worktree。
- 下一步若 Owner 要真正進 production：先提供 / 確認 approved payload，使用 approval package 審核 SQL；正式 SQL execution、backfill、RLS / grant、live write、live Telegram 仍需單獨批准。

## Status Values

- `todo`: 等待該角色處理。
- `waiting_pm`: Tech 或 QA 等待 PM 交付。
- `waiting_tech`: QA 等待 Tech 交付。
- `task_ready`: PM 已交付 `TASK.md`。
- `changelog_ready`: Tech 已交付 `CHANGELOG.md`。
- `qa_passed`: QA 驗證通過。
- `qa_failed`: QA 驗證失敗。
- `conditional_pass`: QA 有條件通過，仍有合併前必要驗證或 Owner 決策。
- `conditional_acceptance`: Architect 有條件吸收結果，不代表可 commit / push。
- `blocked`: 該角色遇到阻塞，需 Architect 或 Owner 判斷。
- `completed`: 非開發類任務已由負責角色完成。
- `not_required`: 本輪不需要該角色處理。
- `pushed`: Architect 已提交並推送。
- `research_dispatched`: Architect 已建立研究任務。
- `research_ready`: 該角色已提交研究摘要。
- `research_accepted`: Architect 已吸收研究摘要並整理結論。

## Version / QA Levels

- version_level `patch`：bug / 文案 / 顯示一致性，不改策略意圖。
- version_level `minor`：新增使用者可見能力或報文結構。
- version_level `major`：改策略核心、DB schema、交易狀態機、正式寫庫或跨日持久化。
- version_level `none`：純流程 / 文件規則補強。
- qa_level `L1`：局部 formatter / snapshot / 指定回歸。
- qa_level `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- qa_level `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。
- qa_level `process`：純流程文件補強。
- qa_level `research`：研究任務，不執行測試。

## Fixed Startup Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。先讀 AGENTS.md 和 DISPATCH.md；若是產品 bug / 顯示 bug / feature request，只能先更新 DISPATCH.md 分派 PM，不得直接寫 TASK.md、不得搜尋或修改產品代碼，除非 Owner 明確說你直接代該角色。
```

Architect 可用 CAO：

```text
研究：tools/cao_agent/run_architect_task.sh research "<研究問題>"
規劃：tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
自動開發：tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"

CAO 服務確認：tools/cao_agent/ensure_cao_services.sh
分配或啟動 CAO agents 後，Architect 必須先確認服務已啟動，再回覆 Owner 前端地址：http://127.0.0.1:5173/
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；若 pm_status 是 todo 或 Architect 指定 PM，請撰寫 TASK.md，不修改代碼。TASK.md 必須從 # TASK: 開始，並符合 AGENTS.md 的 PM 任務卡固定欄位；若需求不足，請輸出 blocked TASK.md。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；若 tech_status 是 todo 且 TASK.md 已 ready，就依 TASK.md 實作並改寫 CHANGELOG.md，不修改產品方向。CHANGELOG.md 必須從 # CHANGELOG: 開始，並符合 AGENTS.md 的 Tech 實作卡固定欄位；若 TASK.md 缺直接消費者、驗收條件或輸出契約，請 blocked。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；若 qa_status 是 todo 且 Tech 已交付 CHANGELOG.md，請執行本輪 qa_level 指定驗證，補直接消費者、跨區塊語意一致性、使用者誤讀風險、負面案例與關聯風險掃描，完成後改寫 QA_REPORT.md。QA_REPORT.md 必須從 # QA_REPORT: 開始；若只重跑 Tech 測試或沒有主動質疑，不能判定通過。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、TASK.md、CHANGELOG.md、QA_REPORT.md，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
