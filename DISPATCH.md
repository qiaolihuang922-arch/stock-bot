# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `postprofit-state-consistency-v20.2.2`
- task_name: `Post-profit State Consistency`
- task_type: `risk_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `qa_passed_absorbed_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要求開始修 `v20.2.2`：只處理 05/29 報文中「已執行同級停利後仍顯示停利」的狀態 / 報文一致性問題。
- 本輪不處理強勢市場準備層，不改 RR / 過熱 / 漲停不追門檻，不改市場證據鏈，不建表、不 live、不 backfill。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，定義：
  - 同一股票同一交易日已執行同級停利 / 減碼且達建議比例後，不得再次把同級 `停利` 作為主行動。
  - 預設轉為 `停利後觀察 / 減碼後觀察 / 剩餘觀察`。
  - 若仍有第二段 / 更高級停利，必須同行說明觸發條件、今日已賣、剩餘股數、本次建議股數。
- Tech 已交付候選 diff：
  - `core/generator.py` VERSION 升為 `v20.2.2`。
  - POST_PROFIT_WATCH + 今日已賣主案例顯示 `停利後觀察`。
  - 同日已賣後若仍出現可執行停利，顯示 `第二段停利｜今日已賣 N 股｜剩餘 N 股｜本次建議 N 股`。
  - 同步 formatter / notifier / market evidence header 測試。
- QA 最終驗證通過：
  - POST_PROFIT_WATCH 今日已賣不再被誤讀成同級再次停利。
  - 第二段停利跨 summary / 持倉卡 / 風控檢查均帶今日已賣、剩餘與本次建議股數。
  - 無策略門檻、DB、watchlist、live Telegram、backfill diff。
  - 主 repo 驗證：`108 passed, 21 warnings`，`git diff --check` 通過。
- Post-cycle review：
  - QA 有效攔下兩個問題：第二段停利文案不明、CHANGELOG 與 diff 不一致。
  - runner guard 已微調：dirty worktree guard 只攔產品 / 測試候選 diff，不攔正常 `TASK.md` handoff。

## Next Action

- commit / push 後清理 tech worktree。
- 下一張任務可處理強勢市場準備層 / 手機文案；不得直接放寬策略買點。

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
