# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `intraday-v20-0-10-report-followup-review`
- task_name: `Intraday v20.0.10 Report Follow-up Review`
- task_type: `telegram_strategy_report_review`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- Owner 提供新的 `05/28 盤中｜v20.0.10` 報文，要求繼續檢查報文。
- Architect 初判本輪需 PM 定義的問題：
  - 報文 header 是 `盤中`，但持倉下一步仍使用 `明日未修復降級`、`隔日未修復`；需要 PM 定義盤中報文中「今日盤中執行」、「盤中觀察」與「隔日計畫」如何分區，避免時間語意再次混用。
  - `✅ 今日盤中執行清單` 內 4 項全是持倉觀察 / 續抱 / 減碼後觀察，沒有真正下單動作；summary 也寫 `持倉優先處理`。PM 需定義這些是否應叫 `執行清單`，還是改為 `持倉檢查清單 / 風控觀察清單`，避免把觀察誤讀成今日要交易。
  - 英業達今日已賣 25%，持倉卡為 `減碼後觀察`，summary 清單列 `修復才恢復優先級`，但沒有明確標示 `今日已減碼 / 不再減碼`；可能仍有二次賣出誤讀風險。
  - 未持倉漏斗數量本次對得上：未持倉總數 8 = 僅追蹤 4 + 淘汰 4；僅追蹤拆分 2+1+0+1 = 4。此項目前看起來正常。
  - 淘汰股 `群創` 顯示 `淘汰｜突破失敗`，但買點行是 `不買｜追價風險｜等重新轉強｜失敗訊號`，`數據 RR -（過熱）`；主因、買點原因與數據原因混用，需 PM 定義單一主因優先級。
  - `光寶科` 從前一版可買變成 `淘汰｜突破失敗`，價格 -6.20% 且 RR 不可用，策略上可能合理；但若從「可買候選」快速轉「淘汰」，報文需顯示轉弱觸發，避免 Owner 不知道是價格破位、RR 不可用還是突破失敗。
  - `旺宏` +4.66% 仍淘汰，若是弱反彈未修復可以合理；目前有 `弱反彈待確認`，但 summary 主因只寫 `突破失敗、弱反彈待確認`，仍可接受但 PM 需確認是否需要 `上漲但結構未修復` 的短句。
  - 版本已為 `v20.0.10`，本輪若只是 PM 檢查不改輸出可不升版；若 Tech 修改使用者可見報文，需按版本規則至少升到 `v20.0.11`。
- CAO 前端：`http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，版本契約升為 `v20.0.11`。
- Tech 已完成候選 diff：
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `CHANGELOG.md`
- QA 前兩輪分別指出已執行長句重複與 `明日/隔日未修復` 舊語意殘留；Architect 已退回 Tech 收斂。
- QA 最終結論：`通過`。
- QA 驗證：`tests/test_generator_report.py tests/test_notifier.py -q`，`46 passed, 21 warnings`；補手機長報文 fixture，確認 summary 與持倉 detail card 無 `明日未修復 / 隔日未修復`，英業達已執行長句不重複，交易執行 0 不把觀察項算成下單，群創 / 光寶科淘汰主因一致，漏斗數量未回歸。

## Next Action

- 本輪已通過主 repo 驗證，完成 commit / push；等待 Owner 下一個任務。

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
- `qa_accepted`: Architect 已吸收 QA 結論並更新狀態。
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

Architect 可用 CAO online research：

```text
研究：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh research "<研究問題>"
規劃：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh plan "<技術規劃問題>"
自動開發：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh auto "<Owner 任務>"

CAO API：/Users/liveroom/.local/bin/cao-server --host 127.0.0.1 --port 9889
CAO 中文前端：cd /Users/liveroom/.local/share/cao-web-zh/web && npm run dev -- --host 127.0.0.1 --port 5173
分配或啟動 CAO agents 後，Architect 必須回覆 Owner 前端地址：http://127.0.0.1:5173/

底層 run_project_research.sh / run_tech_plan.sh / run_auto_dev_cycle.sh / run_tech_write.sh / run_qa_code.sh 只作為內部工具，不作為 Owner 日常入口。
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
