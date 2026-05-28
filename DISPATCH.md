# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `cao-agent-prompt-efficiency-20260528`
- task_name: `CAO Agent Prompt Efficiency and Closeable Handoff`
- task_type: `process`
- version_level: `none`
- qa_level: `process`
- owner_status: `requested`
- architect_status: `completed`
- pm_status: `not_required`
- tech_status: `not_required`
- qa_status: `not_required`
- commit: `pushed`

## Current Result

- 本輪只做 CAO runner prompt 與流程文件補強，不改產品代碼、不改策略、不改測試。
- Owner 擔心：agent 不夠聰明、效率低，且關掉對話後狀態會錯亂。
- 已完成本機 runner prompt 補丁：
  - `/Users/liveroom/stock-bot-agent-context/run_auto_dev_cycle.sh`：PM 必須先判斷任務尺寸，tiny patch 只允許單一主 bug、單一輸出契約、1-2 個驗收案例，並寫停止條件。
  - `/Users/liveroom/stock-bot-agent-context/run_tech_write.sh`：Tech 必須先寫任務尺寸、最小改動策略、旁支待辦；禁止順手重構、測試過擬合、回退既有契約。
  - `/Users/liveroom/stock-bot-agent-context/run_qa_code.sh`：QA 必須先寫風險預算與停止條件；驗證範圍需匹配任務尺寸，tiny patch 不得無理由擴成全量矩陣。
  - `/Users/liveroom/stock-bot-agent-context/run_tech_plan.sh`：規劃代理必須輸出任務尺寸、最小影響面與不應觸碰模組。
  - `/Users/liveroom/stock-bot-agent-context/README.md`：更新 Tech write / QA runner 已啟用狀態，移除舊「Tech 自動寫碼尚未啟用」誤導。
- 關閉對話後的接力方式：
  - 新對話先讀 `AGENTS.md`、`DISPATCH.md`、`CURRENT_STATE.md`。
  - 本輪 runner 腳本不在 git repo 內，但已在本機實際路徑改好；本文件與 `CURRENT_STATE.md` 記錄改動位置。
  - 若要重新核對 runner，直接讀上述 5 個本機檔案。
- 已驗證：
  - Runner shell syntax：`bash -n run_auto_dev_cycle.sh run_tech_write.sh run_qa_code.sh run_tech_plan.sh run_online_agent.sh` 通過。
  - Repo 文件 diff：`git diff --check` 通過。

## Next Action

- 等待 Owner 下一個需求。

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
研究：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh research "<研究問題>"
規劃：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh plan "<技術規劃問題>"
自動開發：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh auto "<Owner 任務>"

CAO API：/Users/liveroom/.local/bin/cao-server --host 127.0.0.1 --port 9889
CAO 中文前端：cd /Users/liveroom/.local/share/cao-web-zh/web && npm run dev -- --host 127.0.0.1 --port 5173
CAO 服務確認：/Users/liveroom/stock-bot-agent-context/ensure_cao_services.sh
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
