# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `strategy-state-transition-classification-fix`
- task_name: `Strategy State Transition and Rising Stock Classification Fix`
- task_type: `strategy_state_machine_bugfix`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- Owner 指出三個策略狀態問題：
  - 持倉已停利後，下一次決策仍反覆給同級 `停利`，造成重複賣出訊號。
  - 多日下來標的一直停在 `觀察`，缺少觀察狀態的到期、升級或降級規則。
  - 一直上漲的股票仍反覆被列入 `淘汰`，把「不可追高 / 等冷卻 / 等回測」誤判成永久不可行動。
- 本輪要修的是策略狀態機與報文分類契約，不是單純 formatter 文案，也不是硬性鎖死交易。
- PM 必須先定義：
  - `停利後` 狀態：已執行同級停利後，主行動應轉為 `停利後觀察` / `核心續抱` / 等待新條件；只有獲利階段、過熱級別或風控風險升級時，才允許新增停利。
  - `觀察` 狀態老化：觀察不能無限期存在；必須定義修復升級、未修復降級、失效淘汰或維持觀察的停止條件。
  - `上漲但不可買` 分類：強勢上漲但位置過遠、過熱、漲停或 RR 不足時，應歸為 `等冷卻` / `等回測` / `等RR修復` / `追蹤強勢不可買`，不得直接混入 `淘汰`；`淘汰` 僅保留給結構弱、趨勢失效、明確市場弱或觸發失效。
- Tech 不得用「賣過就永不停利」「觀察 N 天一律淘汰」「上漲一律追蹤」這種硬鎖；必須保留升級條件與風控優先。
- QA 必須用 Owner 這三類情境建 fixture，並額外反證：
  - 已停利同級訊號不重複，但更高級停利 / 停損仍可覆蓋。
  - 多日觀察會按條件升級、降級或失效，不會永久卡住。
  - 上漲過熱股不被淘汰，弱勢反彈或市場弱仍可淘汰。
  - 不回退上一輪 `v20.0.9`、post-reduce cooldown、未持倉漏斗與報文降噪契約。
- CAO 前端：`http://127.0.0.1:5173/`
- PM / Tech / QA 必須在最新 main 上工作；若隔離 worktree 基線過舊，Architect 不得整包吸收，只能白名單移植必要 diff 後重跑 QA。
- PM 已交付 `TASK.md`，版本契約為本輪不升版、沿用 `v20.0.9`。
- Tech 已在對齊最新 `origin/main` 的隔離 worktree 完成候選 diff；首輪舊基線 diff 因無法套用被拒收並重跑。
- QA 首輪 `conditional pass` 擋下弱勢淘汰卡片仍出現 `等RR達標` 的誤讀文案；Tech 已補修，真正淘汰卡片改為 `等市場轉強` / `等結構修復` / `等重新轉強`，非淘汰 RR 不足仍保留 `等RR修復`。
- QA 最終結論：`通過`；驗證 `76 passed, 21 warnings`，並補四類真正淘汰 + RR 不足反證，以及非淘汰 RR 不足對照。
- 已吸收白名單 diff：
  - `services/analysis.py`
  - `core/generator.py`
  - `tests/test_analysis_engine.py`
  - `tests/test_generator_report.py`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`

## Next Action

- 本輪已完成，等待 Owner 下一個任務。

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
