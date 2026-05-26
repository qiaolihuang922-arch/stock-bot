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
3. Architect 將需求分派給 PM、Tech 或 QA。
4. PM 只輸出 `TASK.md`。
5. Tech 只根據 `TASK.md` 實作，完成後輸出 `CHANGELOG.md`。
6. QA 只根據 `TASK.md` 與 `CHANGELOG.md` 驗證，完成後輸出 `QA_REPORT.md`。
7. Architect 只讀 `DISPATCH.md`、三份交付摘要或 `RESEARCH.md`，以及必要局部上下文，更新總控文件。

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

- 負責差異測試、snapshot test、formatter test。
- 輸出 `QA_REPORT.md`。
- 只測 `TASK.md` 與 `CHANGELOG.md` 指定影響範圍。
- 不做全局測試，不全 repo 掃描，不 refactor。

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
