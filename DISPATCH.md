# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `verify_evidence_phase_4_production_table_schema`
- task_name: `Verify Evidence Phase 4 Production Table Schema`
- task_type: `process`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `conditional_pending_owner_results`
- pm_status: `task_ready`
- tech_status: `handoff_sql_ready`
- qa_status: `conditional_pass`
- commit: `pending`

## Current Result

- Owner 回報：production table 已建立，要求檢查。
- 本輪只做 read-only schema verification；不寫 production DB、不 backfill、不 live Telegram、不改產品代碼 / 策略 / watchlist。
- 當前執行環境沒有可用 `SUPABASE_*` / `DATABASE_*` connection env，不能直接連線檢查線上表，也不能輸出或讀取 secrets。
- Tech 依停止條件新增只讀 metadata verification SQL：
  - `docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql`
  - 只讀 `information_schema` 與 `pg_catalog` metadata。
  - 覆蓋 table exists、columns、unexpected columns、check constraints、freshness / support_level / evidence_status、indexes、latest confirmed partial index、comments。
- QA conditional pass：
  - 可吸收為「提供 Owner 手動執行的只讀 verification SQL」，不得宣告 production schema 已通過。
  - SQL 只讀掃描通過：無 insert/update/delete/drop/truncate/create/alter/grant/revoke、secret/token/connection string。
  - 粗略 statement check：16 個 statement，皆為 `select`，尾端有分號。
  - 風險：allowed-values summary rows 只檢查必要值存在，不能排除 production constraint 多允許額外值；必須人工比對 raw check constraints 與 SQL artifact。
- Architect 額外驗證：
  - 使用 `.qa_tmp/` 臨時 `pglast` parser 解析 verification SQL：parse OK，16 statements。
  - 在 verification SQL header 補明 raw check constraints 是 allowed values 的 source of truth，不得只看 summary rows 宣告 pass。
- Post-cycle review：
  - 根因分類：`no_safe_db_connection` + `manual_verification_required`。
  - 不新增 `AGENTS.md` 硬規則；既有 no secret / no live write 規則已覆蓋，本輪沉澱為 handoff SQL。

## Next Action

- commit / push verification SQL artifact。
- Owner 在 Supabase SQL editor 執行 `docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql`，回傳全部 result sets。
- Architect 根據回傳結果判定 table schema pass / blocked；若 pass，下一輪才開 read-only loader 任務。

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
