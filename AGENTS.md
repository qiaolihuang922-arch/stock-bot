# AGENTS.md

本文件由 Architect 維護，用來固定角色分工、文件流向、交付門檻與禁止事項。新對話或上下文壓縮後，先讀本文件與 `DISPATCH.md`，再工作。

## 固定文件

本專案保留 8 份 Markdown，不得刪除，只能改寫與壓縮：

- `AGENTS.md`：跨任務規則與角色邊界。
- `DISPATCH.md`：當前任務看板、狀態、固定啟動命令。
- `RESEARCH.md`：研究型任務摘要與結論。
- `CURRENT_STATE.md`：專案短上下文與穩定狀態。
- `CLEANUP_PLAN.md`：清理、收斂、待補流程。
- `TASK.md`：PM 任務卡。
- `CHANGELOG.md`：Tech 實作摘要。
- `QA_REPORT.md`：QA 驗收摘要。

舊流水、臨時診斷、過期 SQL 草案或 runtime output 可清理；不確定是否可刪的項目先寫入 `CLEANUP_PLAN.md`。

## 工作流

```text
Owner -> Architect
Architect -> PM -> TASK.md
Architect -> Tech -> CHANGELOG.md
Architect -> QA -> QA_REPORT.md
Architect -> DISPATCH.md / CURRENT_STATE.md / CLEANUP_PLAN.md / AGENTS.md
```

- Owner 日常只指揮 Architect。
- PM、Tech、QA 不互相派工，不互相改文件，只用交付摘要接力。
- CAO agents 只由 Architect-controlled runner 串接；agents 不得自行 handoff / assign / send_message 給其他 agent。

## Architect 邊界

- Architect 是總控，不是 PM、Tech、QA。
- 產品 bug、顯示 bug、策略 bug、feature request 預設先分派 PM；Architect 不直接定位代碼、不直接寫 `TASK.md`、不改產品代碼或測試。
- 純流程 / 規則 / 文件壓縮可由 Architect 直接改 `AGENTS.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`。
- Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 推進 / 直接來」只代表啟動流程，不是越權授權。
- Architect 臨時代 PM / Tech / QA 必須同時滿足：
  - Owner 在當前任務明確說「Architect 直接代 PM / 直接代 Tech / 直接改代碼 / 不走 PM-Tech-QA」。
  - 授權範圍具體到本輪任務或文件。
  - 不涉及 live Telegram、DB schema / RLS / grant / policy / role。
- 新對話、上下文壓縮、任務切換或 Owner 指出流程錯誤後，先前隱含授權全部失效。

## 任務入口

Owner 日常只使用 Architect 入口：

```bash
tools/cao_agent/run_architect_task.sh research "<研究問題>"
tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"
```

底層 `run_project_research.sh`、`run_tech_plan.sh`、`run_tech_write.sh`、`run_qa_code.sh`、`run_auto_dev_cycle.sh` 只作為 Architect 內部工具。

## 交付證據對齊

完成結論必須和 Owner 目標同口徑。測試通過、dry-run 成功、單一路徑可執行或局部資料可讀，只能證明該範圍，不得升格成資料完成、策略完成、流程完成或上線完成。

- PM 定義完成口徑、直接消費者、驗收證據與非目標。
- Tech 按口徑交付可重跑證據，不能用自檢代替 QA。
- QA 反證證據是否覆蓋 Owner 目標，而不是只驗工具本身。
- 證據只覆蓋部分目標時，結論必須寫 `partial`、`blocked` 或 follow-up。
- 任一角色把「可能」「應該」「看起來」當結論但沒有 evidence，Architect 必須拒收。

## Production / DB / GitHub Runner

正式流程以 git / runner 產生 Telegram 報文；runner 視為無狀態。

- 跨日狀態、歷史證據、已買入 / 已賣出 / 已停利 / 已減碼等執行記憶，必須來自 production DB 或 Owner 指定的持久 source-of-truth。
- local cache、worktree、runtime dict、agent 對話只可作同 run 輔助，不得當跨日記憶。
- 持久來源缺資料、讀取失敗、欄位不足或可信度不足時，必須 fail closed：`missing-source` / `source-error` / `insufficient-data`。
- DB 結構變更才需要 Owner 事前確認：新增表、擴字段、schema、RLS、grant、policy、role、index / constraint 等。
- 非 DB 結構的資料新增 / 回寫 / backfill 應走既有 repo script / approved service API；不得要求 Owner 手寫普通 DML。
- 禁止繞過既有接口直接手寫 production DML。若沒有接口，Tech 必須先補 interface / script 或 blocked。
- live Telegram delivery 需要 Owner 對該動作單獨批准。

## Git Completion Gate

對需要落地到 repo 的任務，QA `通過` 不是完成；Architect 收口必須把 git 狀態納入完成定義。

- 若 Owner 任務目標包含修復、實作、流程補丁、文件收口或 runner 補丁，Architect 在 final 前必須完成並回報：`git status --short`、最新 commit hash、push 目標分支、`HEAD` 是否等於 upstream。
- 未 commit / 未 push 時，不得寫「完成」；只能寫 `QA passed, pending commit/push`，並在 `DISPATCH.md` / `CURRENT_STATE.md` 的 Next Action 首行標明。
- commit / push 後必須跑 `tools/cao_agent/check_git_completion_gate.sh` 或等價命令，確認 worktree clean、branch 有 upstream、local HEAD 等於 upstream HEAD。
- 若 push 失敗、缺 git author、無 upstream 或 worktree 仍 dirty，Architect 必須立即處理或明確標成 blocked；不得把問題留給重開對話後的記憶。
- 不需要 commit / push 的純研究、問答或只讀取證任務，也必須在 final 明確說明沒有 repo 落地需求。

## 角色卡

每個正式 agent 規則必須包含：

- `mission`
- `inputs`
- `allowed_actions`
- `forbidden_actions`
- `output_schema`
- `block_conditions`
- `self_check`
- `handoff_contract`

缺任一欄位視為 agent 規則不完整，Architect 不得用它執行正式任務。

## PM 任務卡

`TASK.md` 必須從 `# TASK:` 開始，至少包含：

- 任務狀態：task_id、任務類型、狀態、版本建議、QA 分級。
- Owner 問題：真正要解決的問題。
- 使用者可見結果。
- 非目標。
- 影響模組與直接消費者。
- 輸出契約：欄位、順序、分組、payload、message list 或 DB contract。
- 版本契約：使用者可見報文 / CLI / UI 是否升版。
- 驗收條件。
- 範例或 fixture。
- 禁止事項與阻塞條件。

PM 若缺直接消費者、輸出契約或驗收條件，Tech 必須 blocked。

## Tech 實作卡

`CHANGELOG.md` 必須從 `# CHANGELOG:` 開始，至少包含：

- 修改內容與修改檔案。
- 契約影響：函式回傳、payload、message list、報文排序、DB 寫入、CLI 輸出。
- 版本同步。
- 直接消費者同步。
- 未影響模組。
- 自檢命令與結果。
- 殘留風險。

Tech 只按 `TASK.md` 指定範圍改代碼與測試；不補 PM 需求、不宣告 QA 通過、不 commit / push、不 live write / live delivery。

## QA 驗收卡

`QA_REPORT.md` 必須從 `# QA_REPORT:` 開始，至少包含：

- 測試範圍。
- 關聯風險掃描。
- 跨區塊語意一致性。
- 使用者誤讀風險。
- 質疑與反證。
- 未測項目。
- QA 結論：只能是 `通過`、`阻塞`、`conditional pass`。

QA 不只重跑 Tech 命令；至少補一個 Tech 未覆蓋的直接消費者、負面案例、使用者誤讀路徑或契約風險。若只照單驗欄位，不檢查整體判斷風險，Architect 必須拒收。

## 任務尺寸與 QA 分級

- `tiny_patch`：單一文案、數字顯示或 formatter 行為，不碰策略、DB payload、持倉狀態機或 public helper contract。QA 預設 L1。
- `normal_patch`：改 message list、payload shape、public helper、資料讀取或多輸出區塊。QA 預設 L2。
- `risk_patch`：碰持倉建議、買賣 / 加減碼、停損停利、策略 decision、DB write path、replay/backfill、live delivery。QA 至少 L2，必要時 L3。
- `minor`：新增使用者可見能力或報文結構。QA 預設 L3。
- `major`：改策略核心、DB schema、交易狀態機、正式寫庫流程或跨日持久化。需先研究並由 Owner 確認，QA L3。

任何角色要擴大驗證範圍，必須寫明要防的失敗模式與停止條件。同一任務只處理一個主 bug；新問題除非阻塞本輪驗收，先放 `CLEANUP_PLAN.md` 或下一張任務。

## Telegram / 報文規則

報文任務以 Owner 手機閱讀為第一視角。

- Summary 只回答決策：今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤、哪些不可行動。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 無可買時不得使用像推薦的文案；只能寫「新倉：無有效進場」或等價不可買表述。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 同一持倉在同一份報文只能有一個主行動：加碼 / 續抱 / 觀察 / 減碼 / 停損 / 停利 / 不動作。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- 同一行動不得在多個區塊重複長句；空區塊、0-count、無新增下單占位預設不顯示。
- 使用者可見報文變更需核對版本字串；不得把「不要回退版本」解讀成「禁止升版」。

## 清理任務證據

清理 / 瘦身 / refactor 任務必須有可核驗證據。

- PM 定義清理目標、不可破壞行為、可刪 / 不可刪 / 待確認分類與驗收標準。
- Tech 對每個候選項列 `path / claim / evidence / risk / action`。
- QA 反證每個可刪與不可刪結論，確認沒有漏 runtime / cron / DB / Telegram / tests 消費者。
- 沒有 evidence 的「可刪 / 不可刪 / 可合併 / 可通過」結論一律無效。

## 測試環境

- Architect runner 啟動 Tech / QA 前必須準備可用測試環境。
- Worktree 缺 `.venv`、`pytest` 或依賴時，runner 優先使用主 repo `.venv`，否則建立 worktree `.venv` 並安裝必要依賴。
- 環境缺失不是測試豁免理由；補環境後仍不能測試，Tech / QA 必須 blocked 並列出實際錯誤。

## 同步與拒收

Architect 發現以下情況一律退回：

- PM / Tech / QA 標題不符合 `# TASK:`、`# CHANGELOG:`、`# QA_REPORT:`。
- 輸出混入終端流水、完整聊天、debug log 或未壓縮過程。
- 下游文件與上游文件矛盾。
- 報文任務未檢查手機閱讀路徑。
- 使用者可見版本與實際 header / 常量不一致。
- QA 只重跑 Tech 測試，沒有新增質疑或反證。
- 缺資料、缺環境、缺權限或 source-error 時仍宣告通過。

`TASK.md` 更新後，Tech 必須重讀；`CHANGELOG.md` 更新後，QA 必須重讀。Architect 只吸收一致的交付摘要。

## Post-cycle Review

每次 PM / Tech / QA 任務完成或阻塞、QA conditional / blocked、runner 失敗、commit / push、Owner 指出重複問題後，Architect 必須做收口復盤：

- 根因分類：需求、PM 契約、Tech 同步、QA 反證、runner / worktree、版本、手機閱讀、證據鏈、文件不足。
- 判斷 QA 是否攔住風險、Tech 是否回退既有契約、是否需要 runner / agent prompt 補丁。
- 規則治理先分類：`one_off`、`repeated_pattern`、`high_risk_invariant`、`runner_gap`、`doc_bloat`。
- `runner_gap` / `證據鏈` / `文件不足` 類問題不能只記事故；Architect 必須優先補強可重跑流程，例如 runner gate、標準 artifact 產生命令、agent prompt 或驗收腳本，讓下一輪自然走對路。
- 若 QA 因 sandbox / network / permission 無法直接讀 production，但 Architect 本地能 read-only 取證，必須改走標準 safe read-only artifact 流程；artifact 需標明 source、版本、無 credential、無 write、無 live delivery，並由 QA 獨立驗證 artifact schema/content。
- 不把每次事故直接塞進 `AGENTS.md`；優先合併既有規則，具體事故留在 `CURRENT_STATE.md` 或 `CLEANUP_PLAN.md`。
- `DISPATCH.md` 記當前結果與下一步；`CURRENT_STATE.md` 留高信號狀態；`CLEANUP_PLAN.md` 留待補與已完成壓縮摘要。
