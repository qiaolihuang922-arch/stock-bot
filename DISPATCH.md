# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `runtime-market-breadth-evidence-fallback-v20.3.0`
- task_name: `Runtime Market Breadth Evidence Fallback`
- task_type: `normal_patch`
- version_level: `minor`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `a627c12`

## Current Result

- Owner 要求報文確認後繼續證據鏈；本輪做 runtime market breadth evidence fallback，不建表、不 live write、不 backfill。
- 本輪只讓 production 無 evidence table/cache 時能用當次 runtime results_map 產生 weak/runtime 或 missing-source evidence；不改交易策略、不改 DB schema、不改 watchlist、不 live。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，定義：
  - 無 DB evidence table/cache 時，可用 runtime watchlist breadth 作為弱證據 fallback。
  - 缺 market_index / sector_index 時不得 confirmed。
  - evidence 不能改 BUY / SELL / RR / 過熱 / 漲停不追 / 可準備分類，也不能新增進場建議。
  - Telegram 文案必須清楚標示內部觀察池偏強但缺大盤 / 族群指數 evidence，未確認。
- Tech 已交付候選 diff：
  - `core/generator.py` VERSION 升為 `v20.3.0`。
  - `core/market_theme_evidence.py` 可在缺 DB/cache 時用 runtime results_map 生成 watchlist breadth fallback evidence。
  - 新增 `runtime_fallback`、`runtime_supportive`、`missing_source_reasons` 欄位。
  - Telegram evidence 區塊新增 `市場證據：weak/runtime`、`題材證據：weak/runtime` 與 `absent/missing-source` 缺來源說明。
  - `core/generator.py` 的 dict evidence 與非 dict market_summary 路徑都同步傳入 missing DB/cache 條件。
- QA 最終驗證通過：
  - 無 DB/cache + runtime supportive 顯示 weak/runtime。
  - runtime 不足顯示 absent/missing-source 並列缺來源。
  - 缺 market/sector index 不出現 confirmed。
  - fallback 不改原始交易 decision，不產生買入 / 加碼 / 可買暗示。
  - forbidden diff 檢查確認無 DB schema、migration、Supabase write、watchlist、live/backfill diff。
  - 主 repo 驗證：`120 passed, 21 warnings`；`git diff --check` 通過。
- Post-cycle review：
  - 根因分類：`repeated_pattern` / production 無 evidence table 時缺 runtime fallback 與缺來源說明。
  - 已沉澱成 fixture：runtime supportive but missing indexes、missing breadth、existing source 不誤標缺 DB/cache、decision 不變。
  - Runner gap 重複：auto cycle 對 QA `通過` 再次 false fail，已提升為 `CLEANUP_PLAN.md` 待補。
  - 不新增 `AGENTS.md` 硬規則，因既有 DB/live 禁令與 evidence 不放寬買點規則已覆蓋。

## Next Action

- 已 push；執行 tech worktree cleanup 後等待 Owner 下一個需求。
- 下一步若要 market_index / sector_index、DB cache/table、external provider 或持久化 evidence，先通知 Owner。

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
