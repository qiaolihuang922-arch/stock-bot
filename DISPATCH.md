# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `telegram-holding-risk-tomorrow-plan-dedupe-v20-1-3`
- task_name: `Telegram Holding Risk Tomorrow Plan Dedupe v20.1.3`
- task_type: `development`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `completed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- CAO 前端：`http://127.0.0.1:5173/`
- Owner 指出 `v20.1.2` 報文中 `隔日計畫` 與 `持倉風控檢查` 重複：智原 / 緯創同一個明日未修復降級行動被兩個區塊重複描述。
- PM 定義 `v20.1.3` tiny patch：同一檔同一風控 / 降級行動只能出現一次；`明日計畫` 只承載真正非重複待觸發事項。
- Tech 已交付 `CHANGELOG.md`，QA 結論 `通過`。
- 本輪實作：
  - Telegram header / formatter `VERSION` 升為 `v20.1.3`。
  - 移除獨立 `隔日計畫` 與舊 `format_next_day_plan()` helper。
  - 持倉未修復 / 降級檢查只保留在 `持倉風控檢查`。
  - `明日計畫` 只顯示非重複 pending items，例如 `技嘉｜待觸發加碼10`。
  - 沒有非重複明日事項時，不輸出 `明日計畫 0`、`明日計畫：無新增下單` 或空明日計畫區塊。
  - Summary 手機閱讀順序改為先持倉風控，再明日計畫。
  - 未改策略 decision、持倉 action 判斷來源、DB、watchlist、market theme evidence provider、live Telegram / Supabase、replay/backfill。
- QA 驗證：
  - `tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：`64 passed, 21 warnings`。
  - 補手機閱讀 fixture：risk_only 無明日計畫噪音；risk_plus_add 中持倉風控早於明日計畫 1，技嘉待觸發加碼保留。
- Post-cycle review：
  - QA 兩次 conditional pass 有效攔住殘留噪音：先攔下 `明日計畫 0 / 無新增下單`，再攔下 `明日計畫` 排在持倉風控之前。
  - 已補 `AGENTS.md` 手機 Telegram 報文硬規則：空區塊 / 0 計數 / no-op 文案也算手機噪音；同義區塊不得重複同一行動；持倉風控優先於待觸發明日事項。

## Next Action

- Architect final review 已在主 repo 跑同組驗證，通過後提交並推送。
- 推送後清理 CAO worktree，並確認 CAO API / 前端服務可用。
- 後續報文任務如新增區塊，PM 必須定義空區塊 / 0 計數是否顯示；未定義則預設不顯示。QA 必須檢查手機閱讀順序。

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
