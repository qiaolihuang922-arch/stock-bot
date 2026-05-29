# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_chain_production_ops_artifacts_20260529`
- task_name: `Evidence Chain Production Ops Artifacts`
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

- Owner 要求繼續證據鏈，但進入 production ingestion / backfill / RLS / read-only runner smoke 前，必須先把 repo-side 非 live 操作物補齊，且不可誤導成已上線。
- 本輪完成 production ops artifacts：
  - `scripts/validate_market_theme_evidence_ingestion.py`：驗證 Owner-approved ingestion payload，合格時可選擇輸出 manual SQL；fake/local/runtime/cache/worktree/report-derived/synthetic/default/test source 全部 fail closed。
  - `scripts/smoke_market_theme_evidence_readonly.py`：只用 `SUPABASE_READONLY_KEY` 做 read-only smoke，不 fallback service-role key；缺 env / 無 rows / 權限錯誤都 fail closed。
  - `db/sql/evidence_chain_market_theme_ops_manual_template.sql`：提供 Owner 手動核准後才可使用的 read-only role/grant、RLS policy、optional backfill/upsert template 與 read-only verification queries。
  - `docs/handoff/evidence_chain_market_theme_ops_artifacts.md`：說明 dry-run、manual SQL、read-only smoke、禁止 live side effect。
  - `services/market_theme_evidence_store.py` handoff helper 擴充 validation payload 與 CLI 使用所需 contract。
- 本輪沒有 live Supabase write、沒有正式 backfill、沒有 production RLS / grant 變更、沒有 live Telegram、沒有改策略 decision 或使用者可見 Telegram version。
- QA 通過：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：28 passed, 17 warnings。
  - read-only smoke 缺 env 時 exit 2 並輸出 `telegram_confirmed: false`。
  - fake source 即使用 `--include-sql` 也不得產生 manual SQL。
  - 只設定 `SUPABASE_SERVICE_ROLE_KEY` 不得被 smoke 使用，必須要求 `SUPABASE_READONLY_KEY`。
  - SQL / docs 無 secrets、無自動 live write、無自動 RLS / grant / backfill。
- Runner 狀態：CAO auto 實質 PM/Tech/QA 完成，但 runner parser 對 QA 結論 false fail；Architect 已按 QA 報告與主 repo 驗證手動吸收。
- Post-cycle review：
  - 根因分類：`production_ops_boundary` + `manual_sql_operator_risk` + `runner_parser_false_fail`。
  - QA 有效覆蓋 live side effect、fake confirmed、service-role fallback 與 fresh runner read-only 邊界。
  - Architect 額外補強 SQL / docs：此 SQL template 不是 one-click SQL，Step D 也需替換 `:TRADE_DATE`。
  - 不新增 `AGENTS.md` 硬規則；既有 DB/live write、GitHub runner source-of-truth、Post-cycle Review 已覆蓋。本輪只更新狀態與 runner 待補。

## Next Action

- Architect commit / push 本輪 diff，清理 CAO worktree。
- 若 Owner 要真正進 production：先審核 SQL template 需要執行的 section、替換 placeholder，提供 read-only env 後跑 smoke；正式 backfill / RLS / grant / live write 仍需單獨批准。

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
