# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_chain_predev_closure_20260529`
- task_name: `Evidence Chain Pre-Development Closure`
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

- Owner 要求在繼續證據鏈開發前，先把三件事收斂到同一進度：真資料 / DB 資料消費 / 新表端到端流程。
- 本輪完成非 live repo-side 閉環補丁：
  - `services/market_theme_evidence_store.py` 新增 `build_market_theme_evidence_handoff()` 與 `render_market_theme_evidence_handoff_sql()`。
  - helper 只產生 manual SQL handoff；`live_write=False`，不執行 Supabase write、不 backfill、不改 RLS、不 live Telegram。
  - 允許來源收斂為 `production_db`、`owner_approved_persistent`、`market_data`；runtime/local/cache/worktree/test/report-derived/synthetic/default/unknown source 全部 fail closed。
  - handoff builder 自身 `confirmed=False`；只有 Owner 手動執行 SQL 寫入 production table 後，GitHub fresh runner 才能透過既有 read-only loader 讀到 confirmed/supporting/fresh rows。
- 新增測試 `tests/test_market_theme_evidence_handoff.py`，覆蓋合法 manual SQL、fake source、missing status、raw renderer 旁路、empty/None rows。
- QA 通過：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：25 passed, 17 warnings。
  - QA 額外 smoke 覆蓋 14 種 fake/local/runtime/report-derived source、renderer empty/None、no DB fresh-run fail closed。
  - 結論只代表本輪 non-live handoff diff 可吸收；不得解讀為 production ingestion/backfill/RLS/smoke 已完成。
- Post-cycle review：
  - 根因分類：`integration_fragmentation` + `read_only_chain_incomplete` + `runner_gap`。
  - QA 有效攔截兩輪：先抓出 missing `evidence_status` default confirmed 與 raw renderer bypass，再抓出 empty/None renderer 旁路；已修並補測。
  - Tech/QA runner 多次卡在互動提示，需補 runner prompt/session cleanup；本輪用人工審查與 QA 報告收口。
  - 不新增 `AGENTS.md` 硬規則；既有 DB/live write、source-of-truth、Post-cycle Review 已覆蓋，本輪只更新狀態與待補流程。

## Next Action

- Architect commit / push 本輪 diff，清理 CAO worktree。
- 下一步才可繼續證據鏈：production ingestion/backfill/RLS/read-only role/GitHub runner actual data smoke 仍需 Owner 明確批准或手動 SQL / smoke 步驟。

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
