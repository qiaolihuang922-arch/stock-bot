# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `second-take-profit-execution-dedupe-v20.2.3`
- task_name: `Second Take-profit Execution Dedupe`
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

- Owner 指出已依第二次停利建議賣出 75 股後，`v20.2.2` 仍顯示 `第二段停利 / 本次建議 56 股`，要求嚴格避免同日第二段重複賣出建議。
- 本輪只處理第二段 / 額外停利 execution 去重與手機報文一致性；不改 RR / 過熱 / 漲停不追門檻，不改市場證據鏈，不改 DB schema，不 live、不 backfill。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，定義：
  - 優先使用既有 DB execution / local execution，再 fallback 到 `position_events`，不得只靠 formatter 文案猜。
  - 第二段已完整或超額執行後，主行動改為 `第二段停利後觀察 / 停利完成觀察`，不得再輸出完整可執行建議。
  - 部分執行只顯示剩餘建議股數；未執行時仍可顯示 `第二段停利 / 本次建議 N 股`。
  - summary、持倉卡、持倉風控檢查的今日已賣、剩餘、建議股數不得互相矛盾。
- Tech 已交付候選 diff：
  - `core/generator.py` VERSION 升為 `v20.2.3`。
  - 新增 execution 狀態 helper，依序讀取 DB / local execution / position_events 今日已賣股數。
  - completed：`第二段停利後觀察｜今日已賣 N 股｜剩餘 N 股｜第二段已執行`。
  - partial：`第二段停利剩餘建議 X 股｜今日已賣 Y 股｜原建議 Z 股`。
  - unexecuted：保留 `第二段停利｜本次建議 N 股｜剩餘 N 股`。
  - 持倉卡 `今日 ...` 欄同步使用同一 execution state，避免 `今日 無` 與 `今日已賣` 同卡矛盾。
- QA 最終驗證通過：
  - completed DB execution 已賣 75 股後不再出現完整 `第二段停利 / 本次建議 56`。
  - partial local execution 只顯示剩餘建議 36 股。
  - unexecuted 仍顯示 `第二段停利 / 本次建議 56 / 剩餘`。
  - 持倉卡、summary、風控檢查不再有 `今日 無` 與 `今日已賣 N 股` 矛盾。
  - 無策略門檻、DB、watchlist、live Telegram、backfill diff。
  - 主 repo 驗證：`76 passed, 21 warnings`；策略 smoke `8 passed`；`git diff --check` 通過。
- Post-cycle review：
  - QA 有效攔下三個問題：未執行第二段被過度去重、持倉卡 `今日 無` 與 execution 文案矛盾、`CHANGELOG.md` 自述與 diff 不一致。
  - 根因分類：`repeated_pattern` / 手機跨區塊一致性不足；已沉澱到本輪 `TASK.md` / `QA_REPORT.md`，並更新 `CURRENT_STATE.md` / `CLEANUP_PLAN.md`，不新增硬規則避免文件膨脹。

## Next Action

- commit / push 後清理 tech worktree。
- 若要精準區分第一段、第二段、額外停利、風控賣出，另開 execution stage / DB 設計任務；不得在 formatter 裡無限猜。

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
