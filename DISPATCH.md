# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `telegram-unheld-funnel-count-bug`
- task_name: `Telegram Unheld Funnel Count Bug`
- task_type: `formatter_bugfix`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- Owner 指出短報文 `未持倉漏斗（非執行）` 的顯示會造成數量誤讀：
  - 例：已持倉 5 檔，未持倉實際 7 檔。
  - 現有短報文類似 `可買 0｜準備 0｜僅追蹤 6｜冷卻 3｜回測 1｜等RR修復 2｜等量能 0｜淘汰 1`。
  - `僅追蹤 6` 已包含冷卻 / 回測 / RR / 量能，後面又列子分類，手機閱讀上容易被誤加成超過 watchlist 12 檔。
- 本輪只修短報文漏斗顯示契約，不改策略 decision、未持倉分類、DB payload、watchlist、live Telegram 或 live Supabase。
- Architect 已按角色自鎖規則分派 PM；不得直接寫 `TASK.md` 或搜尋 / 修改產品代碼。
- PM 已交付 `TASK.md`。
- Tech 第一輪已在隔離 worktree 產生候選 diff，QA 結論為 `conditional pass`。
- QA 主動發現邊界風險：當 `可準備 > 0` 時，短報文的 `非執行追蹤 N` 與 `其中` 拆分母集合不一致，仍可能造成手機數量誤讀。
- Tech 第二輪已補修該邊界，QA 第二輪結論：`通過`。
- 已吸收白名單候選 diff：
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
- 主 repo 驗證通過：`tests/test_generator_report.py tests/test_notifier.py`，`37 passed, 21 warnings`。
- 已提交並推送：`3514f94 fix: clarify unheld funnel counts`。
- 工作流程補強：Owner 若明確說「對比後沒問題就直接 push / 自己 push / 對齊 git」，Architect 完成 final diff review 與必要驗證後直接 commit / push，不再二次詢問；若發現不明 diff、QA 未通過或測試阻塞則不得 push。
- 版本契約補強：後續 Telegram / CLI / 使用者可見報文任務，PM 必須定義版本字串是否升版，Tech 必須同步程式常量 / header / 測試，QA 必須核對實際輸出版本；狀態文件版本不得替代實際輸出版本。

## Next Action

- 等待 Owner 下一個需求。若要修正目前 `core/generator.py` 仍顯示 `v20.0.1` 的問題，需按新流程開版本同步 patch。

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
