# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `postprofit-and-strong-market-review-20260529`
- task_name: `Post-profit State And Strong Market Preparation Review`
- task_type: `research_to_product`
- version_level: `patch_then_possible_minor`
- qa_level: `research`
- owner_status: `requested`
- architect_status: `research_accepted_waiting_owner_direction`
- pm_status: `research_ready`
- tech_status: `not_required`
- qa_status: `research_ready`
- commit: `pending`

## Current Result

- Owner 暫停證據鏈，要求檢查 05/29 v20.2.1 報文：
  - 英業達今日已停利賣出 112 股後，主決策仍顯示 `停利`。
  - 本週台股 / AI / 電子大漲，但系統一檔都沒有推薦。
- Architect 已走 research，不改產品代碼、不建表、不做 live、不 backfill。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- Research 結論：
  - 英業達已執行同級停利後仍以 `停利` 作主行動，是高風險報文 / 狀態機問題；疑似違反既有契約：今日已減碼 / 停利達同級建議時，預設轉為觀察，只有更高級風控或硬停損可覆蓋。
  - 公開資料支持本週 AI / 電子 / 台股偏強，但零 BUY 不必然是策略錯；漲停不追、過熱冷卻、RR 不足有風控合理性。
  - 真正產品缺口是：強勢市場下缺少 `市場強但個股買點未成立` 的準備層與手機文案，導致 Owner 只看到無推薦，感覺系統漏掉行情。
- 建議下一步：
  - 先做 `v20.2.2` patch：修已執行停利後主行動，避免同日同級連續停利誤讀。
  - 再視 Owner 是否同意做 minor 產品層：強勢市場準備層；不直接放寬策略門檻。
- 禁止事項：
  - 不直接把市場大漲轉成 BUY。
  - 不改 RR / 過熱 / 漲停不追門檻，除非 Owner 明確批准 major 策略研究。
  - 不建表、不 live Supabase write、不 live Telegram、不 backfill。

## Next Action

- 等待 Owner 決定：
  - 若要修，Architect 分派 PM 撰寫 `v20.2.2` TASK.md。
  - 第一張 TASK 只處理「已執行停利後狀態」，不要同時改強勢市場準備層。

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
