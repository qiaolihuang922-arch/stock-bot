# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_phase3_production_confirmed_source_mapping_20260529`
- task_name: `Evidence Phase 3 Production Confirmed Market Theme Source Mapping`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `blocked_pending_owner_source_contract`
- pm_status: `task_ready`
- tech_status: `blocked`
- qa_status: `not_required`
- commit: `pending`

## Current Result

- Owner 要求：開始 Evidence Phase 3，確認現有 production DB / persistent source 是否足以讓 market/theme evidence confirmed；若需要擴字段或建表，先通知 Owner。
- PM 已定義 source contract 與停止條件：Tech 先檢查既有 code / schema / docs；只在既有 production source 完整時才做 read-only loader，否則 blocked。
- Tech 結論：blocked，未改產品代碼。現有 repo 可證明的 production source 不足，若硬做 loader 會把個股策略資料、runtime 聚合或 payload dict 誤升級成 market/theme confirmed。
- 已確認不足：
  - `daily_signal_snapshot` / `strategy_feature_snapshots` 有個股策略狀態或分類，但不是 market index，缺 sector/theme key 與 production breadth contract。
  - `strategy_outcome_metrics` / `strategy_classification_audit` 是回測或 audit trace，不是當日 market/theme support。
  - `market_daily_bars` / `daily_price` 是個股價格資料，不是 TAIEX / sector index contract，缺 theme mapping 與 breadth。
  - runtime diagnostic / report-derived / payload dict 仍只能 detail，不得 confirmed。
- 需要 Owner/PM 確認或批准的 production source contract：
  - market/theme evidence table、view 或 helper，且 GitHub fresh runner 可 read-only 存取。
  - `market_index` 或等價市場指標，例如 TAIEX / sector index。
  - `sector_theme_key` 或等價 theme / sector key，可映射到 watchlist 股票。
  - production / persistent `watchlist_breadth`，或可 read-only 重建的廣度計算契約。
  - `as_of` / `trade_date` / freshness。
  - `evidence_value` / `support_level`。
  - lineage：`run_id`、`snapshot_id`、`symbol`、`theme_key`、`source_name` 或等價追溯欄位。
- 驗證：
  - Tech 自檢 `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py`：17 passed, 13 warnings。
  - `git diff --check` 通過。
  - 無 schema / migration / SQL / DB write / backfill / watchlist / live Telegram / 策略門檻變更。
- Post-cycle review：
  - 根因分類：`blocked_by_missing_production_source_contract`，不是產品 bug 或程式 diff。
  - 既有 `AGENTS.md` GitHub runner / state source 硬規則已覆蓋，不新增硬規則，避免文件膨脹。
  - 待補流程：下一輪若 Owner 批准建表或指定既有表名，需開 schema / provider 任務，且不得 live write / backfill，除非 Owner 單獨批准。

## Next Action

- 等 Owner 決定：
  - 若 production DB 已有相關表 / view，提供名稱與欄位 contract 後重開 Tech read-only loader 任務。
  - 若沒有，需 Owner 批准新增 schema/table/view/provider 的任務；正式 write / backfill / live Telegram 仍需另外批准。
- 本輪只提交 PM/Tech blocked 文件與總控狀態，不合併產品 diff。

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
