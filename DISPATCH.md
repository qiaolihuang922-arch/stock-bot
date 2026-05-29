# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `data-authenticity-hardening-fail-closed-v20.3.1`
- task_name: `Data Authenticity Fail Closed`
- task_type: `risk_patch`
- version_level: `patch`
- qa_level: `L3-lite`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `see git log -1`

## Current Result

- Owner 要求：DB 已有資料後，策略 / 報文 / 證據鏈 / 行情 / 持倉 / 回測 / DB runtime 拒絕一切假資料；缺真實來源時 fail closed，不補 fake/default/synthetic。
- 本輪修復三個 runtime 可達高風險點，不改策略、不改 DB schema、不改 watchlist、不 live write/backfill/Telegram：
  - positions 缺設定 / DB error / 0 rows 不再回全 watchlist 0 股 fallback，改 `{}` + warning。
  - position_events missing-source / source-error 不再回全 0 event summary；只有 DB query 成功且空資料才代表真實無事件。
  - watchlist breadth runtime fallback 不再稱市場證據、不再 weak/runtime、不進 sources、不 confirmed；只保留非交易診斷。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，定義 source-of-truth / fail-closed 契約與 position_events 殘留契約。
- Tech / Architect 吸收 diff：
  - `core/generator.py` VERSION 升為 `v20.3.1`；持倉或今日交易事件來源 warning 存在時，直接輸出最小不可行動 summary。
  - `services/position_store.py` 移除 0 股 fallback；position_events source-error/missing-source 回 unavailable metadata。
  - `core/market_theme_evidence.py` 將 runtime breadth fallback 改為 non-trading diagnostic。
  - 新增 `tests/test_position_store.py`，並同步 generator / evidence / notifier 測試。
- QA / Architect 驗證通過：
  - positions missing-source / source-error / empty table fail closed。
  - position_events source-error 不產生 fake 今日無交易；DB query 成功空資料仍是真實 0 event。
  - DB evidence/cache missing 時 watchlist breadth 不 confirmed、不 weak/runtime，只顯示 absent/missing-source + 非交易診斷。
  - forbidden diff 檢查確認無 DB schema、migration、Supabase write、watchlist、live/backfill diff。
  - 主 repo 驗證：`162 passed, 13 warnings`；`git diff --check` 通過。
- Post-cycle review：
  - 根因分類：`high_risk_invariant` / DB 已有資料後 runtime fallback 不可再偽裝事實。
  - QA 攔截有效：untracked new test 與 position_events fake 0 event 殘留都已收口。
  - Runner gap：auto cycle QA parser false fail 重複；第二次 Tech runner 因 dirty worktree fail，已記入 `CLEANUP_PLAN.md`。
  - 不新增 `AGENTS.md` 硬規則，既有 source-of-truth / fail-closed / DB live 禁令已足夠；本輪沉澱為 TASK/CHANGELOG/QA fixture 與 runner 待補。

## Next Action

- 已 push；執行 tech worktree cleanup 後等待 Owner 下一個需求。
- 下一步可回到證據鏈 production 化；若要 market_index / sector_index、DB cache/table、external provider 或持久化 evidence，先通知 Owner。

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
