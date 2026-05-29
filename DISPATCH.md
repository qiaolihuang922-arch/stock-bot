# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence-phase-4-confirmed-market-theme-schema-sql`
- task_name: `Evidence Phase 4 Production DB Schema SQL For Confirmed Market/Theme Evidence`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `validated_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要求：若要建表 / 擴字段，整理成一段 SQL 由 Owner 手動執行；雖然 Owner 表示線上權限已放開，本輪仍不由 agent live 執行 SQL。
- PM 已定義 schema SQL contract：新增 repo-local SQL artifact，支援 future GitHub fresh runner 從 production DB read-only reconstruction confirmed market/theme evidence；不改 Telegram、策略、runner、watchlist 或 DB write path。
- Tech 已新增手動 SQL artifact：
  - `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`
  - 建表：`public.market_theme_confirmed_evidence`
  - 必要欄位：`market_index`、`sector_theme_key`、`watchlist_breadth`、`as_of`、`trade_date`、`freshness`、`evidence_value`、`support_level`、`lineage`、`source_family`、`source_name`。
  - 索引：`trade_date`、`market_index/trade_date`、`sector_theme_key/trade_date`、`source_family/source_name/trade_date`、`trade_date/as_of desc`、latest confirmed partial index。
  - SQL header 已寫明 manual execution only、Owner review、未執行 SQL / backfill / production write / live Telegram。
  - RLS / permissions 只保留 comment guidance；未假設 production role，未寫 broad grant。
- QA 靜態驗證通過：
  - SQL artifact 欄位、freshness fail-closed states、lineage/source traceability、索引與 future query shape 足以支援後續 read-only reconstruction。
  - 未命中 destructive / live / secret patterns：無 `drop table`、`truncate`、`delete from`、`insert into`、`grant`、`service_role`、`password`、`secret`、`token`、`connection string`、`supabase db`、`psql`、`curl`、`wget`。
  - `git diff --check` 通過。
  - 未連 production / staging DB，未 live execute SQL，符合本輪停止條件。
- 重要執行風險：
  - SQL 對 clean create 與同 schema repeat execution 是幂等的。
  - 若 production 已有同名但欄位不完整的 table，Owner 需先在 DB console review schema 差異後手動處理，不可無腦執行。
- Post-cycle review：
  - 根因分類：`schema_contract_needed`。本輪不是產品行為修改，而是把 Phase 3 缺口沉澱成手動 SQL artifact。
  - QA 有效補上 Owner/DB admin 誤讀風險與 no-live-write 邊界。
  - 不新增 `AGENTS.md` 硬規則：既有 live write / DB / GitHub runner source-of-truth 規則已覆蓋；本輪只更新狀態與待辦。

## Next Action

- commit / push 本輪 SQL artifact 與交付文件。
- Owner 可手動在 Supabase SQL editor / Postgres console review 並執行 `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`。
- SQL 執行後，下一輪可開 read-only loader 任務，把 GitHub fresh runner 接到該 production table；正式 writer / backfill / RLS policy / live delivery 仍需另行批准。

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
