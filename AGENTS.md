# AGENTS.md

本文件由 Architect 維護，用來固定團隊分工、文件流向與禁止事項。所有會話先按本文件工作，不依賴完整聊天紀錄。

## 固定文件

本專案保留 8 份 Markdown 作為工作流文件，不得視為無用文件刪除：

- `AGENTS.md`：角色、流程、分工規則。
- `DISPATCH.md`：任務看板、狀態接力、固定啟動命令。
- `RESEARCH.md`：研究型任務的跨角色摘要與結論。
- `CURRENT_STATE.md`：專案目前狀態與模組全貌。
- `CLEANUP_PLAN.md`：清理、收斂、避免重複工作的計畫。
- `TASK.md`：PM 交付給 Architect 的需求摘要。
- `CHANGELOG.md`：Tech 交付給 Architect 的實作摘要。
- `QA_REPORT.md`：QA 交付給 Architect 的驗證摘要。

舊文件、臨時文件、過期診斷文件可由 Architect 依 Owner 指示清理；上述 8 份文件只允許改寫內容，不允許刪除。

## 工作流分層

```text
[Owner]
   |
   v
[Architect]
   |
   +-- [PM]   -> TASK.md
   +-- [Tech] -> CHANGELOG.md
   +-- [QA]   -> QA_REPORT.md
   |
   v
[Architect 更新專案狀態]
   |
   +-- DISPATCH.md
   +-- RESEARCH.md
   +-- CURRENT_STATE.md
   +-- AGENTS.md
   +-- CLEANUP_PLAN.md
```

Owner 只直接指揮 Architect。PM、Tech、QA 不互相指揮、不互相覆蓋工作，只透過各自摘要文件交付。

## 標準流程

1. Owner 向 Architect 下達方向或要求。
2. Architect 更新/確認 `DISPATCH.md`、`CURRENT_STATE.md`、`AGENTS.md`、`CLEANUP_PLAN.md`。
3. Architect 先判斷任務屬於研究、開發、測試或推送。
4. 研究任務先走 `RESEARCH.md`，確認方向後才進入 `TASK.md`。
5. 開發任務按版本分級與 QA 分級寫入 `DISPATCH.md`。
6. PM 只輸出 `TASK.md`。
7. Tech 只根據 `TASK.md` 實作，完成後輸出 `CHANGELOG.md`。
8. QA 只根據 `TASK.md` 與 `CHANGELOG.md` 驗證，完成後輸出 `QA_REPORT.md`。
9. Architect 只讀 `DISPATCH.md`、三份交付摘要或 `RESEARCH.md`，以及必要局部上下文，更新總控文件。

## 版本分級

- `patch`：修 bug、文案、顯示一致性或測試補強，不改策略意圖；例：`v19.4.1`。
- `minor`：新增使用者可見能力、報文結構或工作流能力；例：`v19.5`。
- `major`：改策略核心、DB schema、交易狀態機、正式寫庫流程或跨日持久化；例：`v20`。

升版規則：

- patch 可由 Architect 直接分派 PM/Tech/QA，但仍需 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 接力。
- minor 必須先由 PM 明確定義使用者可見變化與驗收條件。
- major 必須先走研究任務，Owner 明確確認後才可進入開發。
- 若一個任務同時符合多個級別，以最高級別處理。

## QA 分級

- `L1`：局部 formatter / snapshot / 指定回歸測試。
- `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。

QA 套用規則：

- patch 預設 `L1`；若碰策略、持倉、資料來源或 DB 邊界，升為 `L2`。
- minor 預設 `L3`，除非 Architect 與 Owner 明確降級。
- major 必須 `L3`，且需 Owner 明確批准測試範圍。
- 正式 backfill、live Supabase write、live Telegram delivery 不包含在預設 `L3`，必須另行明確批准。
- Architect 推送前只重跑必要驗證，不替代 QA 的完整職責。
- 若任務改變函式回傳順序、回傳結構、訊息 list、payload shape 或外部呼叫契約，即使是 `L1`，QA 也必須檢查直接呼叫方與邊界契約。
- PM 在需求中需列出「被改輸出」的直接消費者；Tech 在 `CHANGELOG.md` 需列出是否已同步直接呼叫方。

## 對話窗啟動方式

獨立對話窗不會自動收到通知。Owner 只需要對每個對話窗發固定啟動句，該角色再依 `DISPATCH.md` 判斷是否工作。

- 開發任務按 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 接力。
- 研究任務按 `RESEARCH.md` 的 PM / Tech / QA Findings 接力。
- 固定啟動句以 `DISPATCH.md` 的 `Fixed Startup Commands` 為準。

## 同步規則

- `TASK.md` 更新後，既有 `CHANGELOG.md` 若仍引用舊任務狀態，Tech 必須重新讀取 `TASK.md` 並改寫 `CHANGELOG.md`。
- `CHANGELOG.md` 更新後，既有 `QA_REPORT.md` 若仍引用舊實作狀態，QA 必須重新讀取 `TASK.md` / `CHANGELOG.md` 並改寫 `QA_REPORT.md`。
- 下游文件不得與上游文件矛盾；若無法處理，必須明確寫出阻塞原因與需要 Architect/Owner 補充的事項。
- Architect 發現交付文件互相矛盾時，不吸收為專案完成狀態，只標記為「待下游重跑」。

## 角色分工

### Architect / 總控

- 維護 `CURRENT_STATE.md` 與本文件。
- 維護 `DISPATCH.md`。
- 維護 `RESEARCH.md` 的 Architect 區塊。
- 維護 `CLEANUP_PLAN.md`。
- 只接收並彙整 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。
- 判斷需求影響模組與應交由哪個會話處理。
- 控制 context 大小，避免重複分析已完成模組。
- 不主動掃描全 repo，不執行全局測試，不大量修改核心代碼。
- Owner 提出新功能、顯示調整、策略調整或 bug 修復時，Architect 預設只更新 `DISPATCH.md` 並分派，不直接改代碼。
- Architect 只有在 Owner 明確說「你直接改代碼 / 直接實作 / 不走部門」時，才可作為臨時 Tech 修改代碼。

### PM / 產品

- 負責功能需求、報文設計、UI/流程、edge case。
- 輸出 `TASK.md`。
- 可讀 `CURRENT_STATE.md` 與 Architect 指令。
- 不修改代碼，不做全局分析。

### Tech / 技術

- 負責功能實作、bug 修復、必要 refactor。
- 輸出 `CHANGELOG.md`。
- `CHANGELOG.md` 必須包含：修改內容、修改檔案、未影響模組。
- 只讀與 `TASK.md` 相關的局部源碼。
- 不重新分析全專案，不修改產品方向。

### QA / 測試

- 負責差異測試、snapshot test、formatter test、契約檢查、關聯風險掃描。
- 輸出 `QA_REPORT.md`。
- 只測 `TASK.md` 與 `CHANGELOG.md` 指定影響範圍。
- 預設不做全局測試，不全 repo 掃描，不 refactor。
- 若 `DISPATCH.md` 指定 QA 分級為 `L3`，可執行 full pytest、replay/backfill dry-run、入庫 payload 路徑檢查與必要風險掃描。
- 若變更涉及 formatter output、messages list、Telegram payload、DB payload 或任一公開函式回傳契約，QA 必須補測直接消費者，不得只測產出函式本身。
- QA 必須主動質疑 PM / Tech 的影響範圍，列出「可能漏掉的直接消費者、間接依賴、邊界情境、負面案例」。
- QA 若發現 `TASK.md` 或 `CHANGELOG.md` 未列出必要關聯模組，不得直接判定通過；必須在 `QA_REPORT.md` 標記 blocked 或 conditional pass。

QA_REPORT 固定章節：

- `測試範圍`：列出依據與實測範圍。
- `關聯風險掃描`：列出直接呼叫方、資料流下游、外部副作用與未覆蓋契約。
- `質疑與反證`：至少回答「PM 是否漏需求」、「Tech 是否漏同步」、「測試是否能證明沒有破壞直接消費者」。
- `未測項目`：列出未測原因與是否可接受。
- `QA 結論`：只能是通過、阻塞、conditional pass 三種之一。

## 交付文件契約

Architect 只接收以下摘要文件：

- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`

各會話不得依賴完整聊天紀錄交接，必須以摘要文件描述當前任務、變更與驗證結果。

Architect 狀態輸出固定為：

- `DISPATCH.md`
- `RESEARCH.md`
- `CURRENT_STATE.md`
- `AGENTS.md`
- `CLEANUP_PLAN.md`

## 模組歸屬速查

- 產品/報文語意：PM 先定義，再交 Tech 實作。
- 策略判斷：`services/analysis.py`。
- 報文與 Telegram formatter：`core/generator.py`。
- 條件映射：`core/condition_engine.py`。
- 行情來源：`services/stock_api.py`。
- 原始信號寫入：`services/signal_store.py`。
- 每日 snapshot 寫入：`services/daily_snapshot_store.py`。
- snapshot 組裝：`core/signal_snapshot.py`。
- snapshot 驗證：`core/signal_validator.py`。
- 持倉讀取：`services/position_store.py`。
- 股票清單唯一來源：`core/watchlist.py`。
- replay/backfill：`scripts/dry_run_replay.py`、`scripts/backfill_signals.py`。
- Telegram 持倉命令：`supabase/functions/telegram-execution/index.ts`。

## 工作限制

- 不修改 `config.py`，不輸出任何 token 或密鑰。
- 不恢復 `services/ai.py`、`services/learning.py` 到主流程，除非有明確任務。
- 不在腳本內另建股票清單，12 檔股票必須來自 `core/watchlist.py`。
- 不直接正式 backfill；必須先 dry-run、validate，再經確認後寫入。
- 需求未定義前，不先改策略或報文分類。
- 不刪除 8 份固定 Markdown 工作流文件。

## Git 發布規則

- Tech 負責本地實作與局部驗證，預設不直接 push，除非 Owner 明確要求。
- QA 負責驗證，不 commit，不 push。
- Architect 收口後可負責 commit / push。
- Architect commit / push 前可檢查代碼 diff，但不得補寫功能代碼；若發現缺口，回派 Tech。
- Architect commit 前必須檢查 `git status`、`git diff --stat` 與必要 diff。
- Architect 只提交本輪 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 對應範圍內的文件，以及 Architect 狀態文件。
- 若工作區有不明來源改動，Architect 必須排除或請 Owner 確認，不可無差別提交。
- Owner 明確要求「把本地最新修改推送」時，Architect 仍需先檢查 diff，再將確認屬於本輪工作流與代碼變更的文件提交推送。

## Push 後壓縮規則

每次 Architect 完成 commit / push 後，下一步必須做上下文壓縮，避免 Markdown 文件變成新的長聊天紀錄。

- `DISPATCH.md`：只保留當前任務狀態與固定啟動句，不保留歷史任務過程。
- `TASK.md`：只保留最新任務；舊任務只保留 3-5 行摘要到 `CURRENT_STATE.md`。
- `CHANGELOG.md`：只保留最新任務；舊實作只保留 3-5 行摘要到 `CURRENT_STATE.md`。
- `QA_REPORT.md`：只保留最新任務；舊測試只保留命令、結果、未測範圍摘要到 `CURRENT_STATE.md`。
- `RESEARCH.md`：只保留最新研究問題、結論、下一步；刪除長過程與完整報文。
- `CURRENT_STATE.md`：每個版本只保留高信號摘要，不貼完整報文、不貼完整 diff。
- `CLEANUP_PLAN.md`：只保留待處理項與清理規則，不保留已完成流水帳。
- 壓縮不得刪除固定 8 份 Markdown 文件，只能改寫內容。
