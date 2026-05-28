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

## 三層硬規則

所有任務先套用以下三層硬規則；若與後文細則衝突，以本節為準。

### 1. 代理規則

- Owner 日常只對 Architect 下任務；Architect 負責拆解、分派、收口。
- PM / Tech / QA 不互相呼叫、不互相派工、不互相改文件。
- CAO agents 只由 Architect-controlled runner 串接；agents 禁止自行 handoff / assign / send_message 給其他 agent。
- Architect 在任何新對話或上下文壓縮後，第一個動作必須先讀 `AGENTS.md` 與 `DISPATCH.md`，並確認自己是總控，不是 PM / Tech / QA。
- Architect 收到產品 bug / 顯示 bug / 策略 bug / feature request 時，只能先分派 PM；不得直接定位代碼、不得直接寫 `TASK.md`、不得直接改產品代碼或測試。
- 即使任務很小，Architect 也不得以「單一 bugfix」為理由跳過 PM；只有 Owner 明確說「你直接代 PM 寫 TASK」或「你直接實作 / 不走部門」時，才可臨時越過對應角色。
- 日常入口只保留：
  - `run_architect_task.sh research "<研究問題>"`
  - `run_architect_task.sh plan "<技術規劃問題>"`
  - `run_architect_task.sh auto "<Owner 任務>"`
- 底層 `run_project_research.sh`、`run_tech_plan.sh`、`run_tech_write.sh`、`run_qa_code.sh`、`run_auto_dev_cycle.sh` 只作為 Architect 內部工具，不作為 Owner 日常入口。
- 新增 agent、改 agent 權限、讓 agent 直接 push / live write / live delivery，必須 Owner 明確批准。
- Architect 不替 PM / Tech / QA 完成其職責範圍內的代碼掃描、刪除判斷或測試驗收；Architect 只審核交付證據是否足夠。
- 若 agent 結論缺證據、證據與結論不匹配、或只用「可能仍有用」搪塞，Architect 必須退回重跑，不得吸收為完成。
- 每次 Owner 指出流程逃逸、角色越權、驗證過度、驗證不足、報文誤導或重複噪音時，Architect 必須主動判斷是否需要補流程規則；若需要，直接更新固定流程文件並收口，不得等 Owner 再次要求「改規則」。

### 1.1 Architect 自鎖檢查

Architect 每次準備採取動作前，必須先做以下自鎖檢查：

- 若下一步會讀產品代碼、搜尋函式、修改測試或修改產品文件，先判斷這是否其實是 Tech / QA 職責；若是，停止並改為分派。
- 若下一步會寫 `TASK.md`，先判斷是否已有 Owner 明確授權 Architect 代 PM；若沒有，停止並把 `pm_status` 設為 `todo`。
- 若下一步會寫 `CHANGELOG.md`，先判斷是否已有 Owner 明確授權 Architect 代 Tech；若沒有，停止並等 Tech 交付。
- 若下一步會寫 `QA_REPORT.md`，先判斷是否已有 Owner 明確授權 Architect 代 QA；若沒有，停止並等 QA 交付。
- 若下一步只是流程 / 規則修復，可由 Architect 直接改 `AGENTS.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`，但不得順手建立產品任務卡或修產品代碼。
- 若已經越權改了文件，Architect 必須先恢復越權改動，再更新流程規則；不得把錯誤狀態繼續往下游傳。

### 1.2 Post-cycle Review Gate

每次完整流程結束後，Architect 必須做一次收口復盤，不得等 Owner 再次指出同一類問題。

觸發時機：

- PM / Tech / QA 任務完成並被 Architect 吸收後。
- QA 阻塞、conditional pass、Tech runner 失敗、auto cycle parser 失敗後。
- commit / push 完成後。
- Owner 指出「又犯同樣問題」「反覆改回去」「流程沒補上」時。

Architect 必須檢查並記錄：

- 本輪問題根因：需求不清、PM 漏契約、Tech 漏同步、QA 漏反證、runner / worktree 問題、版本契約、手機閱讀、證據鏈、或流程文件不足。
- QA 是否真的攔住風險；若 QA 沒攔住，需補 QA 規則。
- Tech 是否把既有已修契約改回去；若有，需補禁止回退 guard。
- 是否有可抽象成通用規則的失誤；若有，按「規則治理」分類後更新 `AGENTS.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`。
- 是否需要補 runner / agent prompt；若需要，記入 `CLEANUP_PLAN.md`，需要改腳本時另開流程任務。
- 是否需要新任務；若是產品 / 策略 / 顯示 / feature，仍需先分派 PM，不得用復盤名義直接改產品代碼。

規則治理：

- 不得把每次事故直接追加成硬規則。Architect 必須先分類：
  - `one_off`：單次上下文或單一任務問題，只寫入 `CURRENT_STATE.md` 或 `CLEANUP_PLAN.md` 短摘要。
  - `repeated_pattern`：同類問題重複發生，合併到既有規則或任務卡契約。
  - `high_risk_invariant`：會造成越權、錯單、live 副作用、版本回退、手機誤讀、資料寫入風險，可升級為 `AGENTS.md` 硬規則。
  - `runner_gap`：應補 runner / agent prompt / worktree gate，不用文件文案硬撐。
  - `doc_bloat`：刪除或壓縮過期流水。
- 新規則必須優先改寫或合併既有段落；只有沒有合適位置時才新增小節。
- 若新增硬規則讓文件變長，必須同時刪除或壓縮已被取代的舊描述，避免固定文件膨脹。
- `AGENTS.md` 只保存跨任務不變的行為約束；任務案例、舊版本流水、一次性提醒不得長期留在 `AGENTS.md`。

收口輸出要求：

- `DISPATCH.md` 的 `Current Result` 必須包含本輪「流程教訓 / 已補規則 / 待補流程」摘要。
- `CURRENT_STATE.md` 必須保留高信號流程狀態，不貼長過程。
- `CLEANUP_PLAN.md` 必須新增或更新待補項，已完成的補丁只保留短摘要。
- 若本輪無需補規則，Architect 也必須在 final response 說明「已做 post-cycle review，未發現需新增規則」。

拒收條件：

- 只說「下次注意」但沒有檢查是否要補文件。
- QA 曾阻塞但 Architect 沒把阻塞原因轉成可重用 guard。
- runner / worktree / 前端服務問題重複發生但沒有寫入流程待補。
- 已修契約被新任務回退，卻沒有把「不得回退既有契約」寫進下一輪任務指令或流程文件。
- 把 `one_off` 事故直接塞進硬規則，或新增規則時沒有清理被取代的冗餘描述。

### 2. 代碼規則

- Architect 預設不改產品代碼；只有 Owner 明確說「你直接改代碼 / 直接實作 / 不走部門」才可臨時作為 Tech。
- 傳統 Tech 只按 `TASK.md` 指定範圍改代碼與測試，並改寫 `CHANGELOG.md`。
- CAO Tech write 只允許在隔離 worktree 產生 diff，不得直接寫主 repo；預設 worktree 為 repo 同級 `stock-bot-agent-worktrees/tech_write`，可用 `STOCK_BOT_AGENT_WORKTREE` 覆蓋。
- 任何代碼 diff 合併主 repo 前，Architect 必須檢查 `git status`、`git diff --stat`、必要 diff 與對應 `TASK.md` / `CHANGELOG.md` / `QA_REPORT.md`。
- 未定義需求前，不改策略、報文分類、DB schema、Telegram payload、watchlist、排程入口。
- 禁止 live Supabase write、正式 backfill、live Telegram delivery，除非 Owner 對該動作單獨批准。

### 3. 文件規則

- 固定 8 份 Markdown 永遠不可刪，只可改寫內容。
- `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 只保留最新交付；舊任務只壓縮進 `CURRENT_STATE.md`。
- `DISPATCH.md` 只保留當前任務狀態、結果、下一步與固定啟動句，不保存流水帳。
- `RESEARCH.md` 只保留最新研究問題、證據、結論、下一步，不貼完整聊天紀錄或完整報文。
- 不確定是否可刪的文件、測試、註解、代碼，一律不刪，寫入 `CLEANUP_PLAN.md` 待確認。
- Owner 明確確認已上線、已建庫、已寫入，且本地 SQL 不是正式 migration / rollback 唯一來源時，舊 SQL schema draft 不再列待確認，按過期草案刪除。
- 任一角色輸出若包含終端流水、完整聊天、未壓縮過程，Architect 必須先清理成摘要，再吸收進固定文件。

## 代理交付證據門檻

任何 agent 對「可刪 / 不可刪 / 可合併 / 不可合併 / 測試通過」下結論時，必須同時提供可核驗證據。沒有證據的結論一律視為無效。

## 角色卡與任務卡契約

本專案不接受只有「角色名稱」的代理。每個代理必須按固定角色卡工作，每個任務必須按固定任務卡交付。

### 角色卡固定欄位

每個 PM / Tech / QA / online research agent 的規則必須同時定義：

- `mission`：本角色唯一目標，不能兼做其他角色工作。
- `inputs`：允許讀取的文件、目錄、摘要或 diff。
- `allowed_actions`：允許執行的動作。
- `forbidden_actions`：禁止動作，包含改錯文件、越權派工、live 外部副作用、commit / push。
- `output_schema`：最終輸出必須長什麼樣。
- `block_conditions`：遇到哪些情況必須停止並標記 blocked。
- `self_check`：交付前必須自查的項目。
- `handoff_contract`：下游只能依哪份摘要文件接力，不依賴聊天紀錄。

缺少任一欄位的 agent 規則視為不完整；Architect 不得用它執行正式任務。

### PM 任務卡固定欄位

`TASK.md` 必須從 `# TASK:` 開始，且至少包含：

- `任務狀態`：task_id、任務類型、狀態、版本建議、QA 分級建議。
- `Owner 問題`：Owner 真正要解決的問題，不得只重述需求文字。
- `使用者可見結果`：Telegram / CLI / DB / workflow 會讓 Owner 看到什麼變化。
- `非目標`：本輪明確不做什麼。
- `影響模組`：直接模組與直接消費者。
- `輸出契約`：被改輸出的欄位、順序、分組、payload 或 message list contract。
- `版本契約`：若任務涉及 Telegram / CLI / 使用者可見報文，PM 必須明確寫出本輪應顯示的版本字串，或明確寫「本輪不升版，沿用目前 `VERSION`」。
- `驗收條件`：可被 QA 驗證的條件，不能只寫「正常」「不壞」。
- `範例或 fixture`：報文 / Telegram / payload 類任務必須給至少一段期望輸出形狀。
- `禁止事項`：不得改策略、不得 live write、不得刪固定文件等本輪邊界。
- `阻塞條件`：需求不足時 PM 必須寫 blocked，不得自己替 Owner 決策。

PM 若沒有列出直接消費者與驗收條件，Tech 必須 blocked，不得自行補產品需求。

### Tech 實作卡固定欄位

`CHANGELOG.md` 必須從 `# CHANGELOG:` 開始，且至少包含：

- `修改內容`：只描述本輪實際完成項。
- `修改檔案`：逐一列出，不得用「相關文件」含糊帶過。
- `契約影響`：函式回傳、message list、payload、報文排序、DB 寫入、CLI 輸出是否改變。
- `版本同步`：若 `TASK.md` 有版本建議或版本契約，Tech 必須說明是否已同步使用者可見版本常量 / header / 測試期望；若不升版需說明原因。
- `直接消費者同步`：哪些呼叫方或下游已同步；若無需同步需說明原因。
- `未影響模組`：策略、DB、watchlist、Telegram live、replay/backfill 等是否未改。
- `自檢命令`：實際跑過的最小命令與結果。
- `殘留風險`：Tech 已知但未處理的風險。

Tech 禁止用「QA 會驗」代替自檢；也禁止宣告整體 QA 通過。

### QA 驗收卡固定欄位

`QA_REPORT.md` 必須從 `# QA_REPORT:` 開始，且固定包含本文件後文列出的章節。QA 還必須做到：

- 不只重跑 Tech 命令；至少補一個 Tech 未覆蓋的直接消費者、負面案例、使用者誤讀路徑或契約風險。
- 對使用者可見輸出，必須用「Owner 手機打開後先看到什麼」的閱讀順序檢查。
- 對清理 / 瘦身 / refactor，必須逐項反證 Tech 的 `path / claim / evidence / risk / action` 表。
- 若沒有找到問題，必須在 `質疑與反證` 中說明探索過哪些方向與為何可接受。
- `QA 結論` 只能是：`通過`、`阻塞`、`conditional pass`。

QA 若沒有主動質疑，或只驗欄位存在、不驗整體判斷風險，Architect 必須拒收。

### Architect 拒收條件

以下情況一律退回，不吸收為完成狀態：

- PM / Tech / QA 輸出沒有正確標題：`# TASK:`、`# CHANGELOG:`、`# QA_REPORT:`。
- 輸出混入終端流水、完整聊天、debug log、未壓縮 reasoning。
- PM 未列直接消費者或可驗收條件。
- Tech 改了 `TASK.md` 未允許的範圍，或未列契約影響。
- QA 只重跑 Tech 測試，沒有新增風險掃描或反證。
- 報文任務沒有檢查手機閱讀路徑。
- 報文 / CLI 任務的 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 沒有檢查使用者可見版本字串與實際程式常量 / header 是否一致。
- 任一角色把「可能」「應該」「看起來」當結論，但沒有 evidence。
- 任一角色遇到缺環境、缺資料、上游文件矛盾時仍宣告通過。

### 清理類任務必備證據

PM 必須定義：

- 清理目標與不可破壞的使用者行為。
- 可刪、不可刪、待確認三種分類。
- 驗收標準，不得只寫「不壞」。

Tech 必須列出每個候選項：

- `path`：候選文件 / 函式 / 測試 / 註解。
- `claim`：建議刪除、保留、改寫或待確認。
- `evidence`：引用來源，例如 `rg` 結果、import chain、入口命令、測試名稱、DB/Telegram/cron 消費者。
- `risk`：刪除後可能壞的路徑。
- `action`：已刪除、已改寫、保留、或寫入 `CLEANUP_PLAN.md`。

QA 必須獨立反證：

- 至少挑戰 Tech 的每個「不可刪」結論，確認是否只是保守搪塞。
- 至少挑戰 Tech 的每個「可刪」結論，確認是否漏掉 runtime / cron / DB / Telegram / tests 消費者。
- 若 Tech 沒有提供可核驗 evidence，QA 必須標記 `blocked`，不得通過。
- 若 Owner 已明確補充 production 事實，例如「線上 DB 已建立」「回測已寫庫」「本地 SQL 不是正式 migration」，QA 不得再用缺 production history 作為保留理由，必須按 Owner 事實重新分類。

Architect 收口只接受：

- 有證據表的 `CHANGELOG.md`。
- 有反證結果的 `QA_REPORT.md`。
- 不接受「我看過沒問題」「可能仍有用」「避免風險所以不刪」這類無證據結論。

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
10. Architect 執行 Post-cycle Review Gate：總結本輪根因、QA 攔截、是否回退既有契約、是否需要補 agent / runner / 流程規則；需要補則直接更新固定流程文件。

## 版本分級

- `patch`：修 bug、文案、顯示一致性或測試補強，不改策略意圖；例：`v19.4.1`。
- `minor`：新增使用者可見能力、報文結構或工作流能力；例：`v19.5`。
- `major`：改策略核心、DB schema、交易狀態機、正式寫庫流程或跨日持久化；例：`v20`。

升版規則：

- patch 可由 Architect 直接分派 PM/Tech/QA，但仍需 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 接力。
- minor 必須先由 PM 明確定義使用者可見變化與驗收條件。
- major 必須先走研究任務，Owner 明確確認後才可進入開發。
- 若一個任務同時符合多個級別，以最高級別處理。
- `不得回退版本` 只代表版本下限，不代表本輪禁止升版；PM / Tech / QA 不得把 Owner 的「不要回退」解讀成「沿用舊版本」。
- 任何使用者可見 Telegram / CLI / UI 報文變更，只要改到策略 decision、持倉主行動、未持倉分類、summary、漏斗、執行清單、formatter header 或 message list contract，預設至少升 patch 版；若 PM 判定不升版，必須在 `TASK.md` 寫明理由與 Owner 可見風險。
- Tech 若看到 `TASK.md` 版本契約仍沿用舊版，但本輪實際改了使用者可見行為，必須 blocked 要求 PM 修正版本契約，不得自行默默沿用。
- QA 驗收時必須核對「本輪變更等級」與「實際 header 版本」是否匹配；若使用者可見行為變更但版本未升且無明確理由，QA 必須 blocked 或 conditional pass。

## 任務尺寸與驗證預算

任務必須先定義「修什麼、不修什麼、驗到哪裡停」。不得因為一個小 bug 把整條產品、測試、流程全部重跑成大任務。

- `tiny_patch`：單一文案、單一數字顯示、單一 formatter 行為，且不改策略 decision、資料來源、DB payload、持倉狀態機或 public helper contract。
  - PM 必須把範圍寫成單一輸出契約與 1-2 個驗收案例。
  - Tech 最多改直接相關產品檔與直接測試，不得順手重構、不做跨模組清理。
  - QA 預設只跑直接 formatter / snapshot / consumer smoke；不得要求 full pytest、replay、backfill、evidence 全矩陣，除非 QA 能指出具體契約風險。
  - Architect final review 只重跑必要命令；不得把「保險起見」當作擴大驗證理由。
- `normal_patch`：仍是 bugfix，但改到 message list、payload shape、public helper、資料讀取或多個輸出區塊；可升到 L2，但 QA 必須說明升級原因。
- `risk_patch`：碰持倉建議、買賣/加減碼、停損停利、策略 decision、DB write path、replay/backfill、live delivery；至少 L2，必要時 L3。
- 任何角色想升級 QA 範圍，必須在交付文件寫明：升級原因、要防的具體失敗模式、停止條件。沒有停止條件的驗證要求，Architect 必須退回收斂。
- 同一任務只能有一個主 bug；若過程發現新問題，除非阻塞本輪驗收，先記入 `CLEANUP_PLAN.md` 或下一張任務，不得把本輪無限擴張。

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

## 手機 Telegram 報文硬規則

報文任務一律以 Owner 手機閱讀為第一視角，不以桌面長文可讀為準。

- PM 必須先定義手機閱讀路徑與示例輸出，不得只列欄位需求。
- PM 必須定義報文 header 版本契約：升版到哪個版本，或明確不升版；不得只在 `CURRENT_STATE.md` 寫版本而不要求 formatter 顯示同步。
- Tech 必須用接近真實長報文的 fixture 檢查輸出，不得只讓單元欄位通過。
- Tech 若修改 Telegram formatter、summary、header 或任何使用者可見報文，必須檢查 `core/generator.py` 的 `VERSION` 或等價版本常量是否符合 `TASK.md`，並同步測試。
- QA 必須把輸出當成 Owner 手機上看到的 Telegram 連續訊息檢查；若「精確但難讀」或「數字可追溯但語意混桶」，必須 blocked 或 conditional pass。
- QA 驗收報文時必須核對實際輸出 header 版本字串，不得只看 `TASK.md`、`CHANGELOG.md` 或 `CURRENT_STATE.md` 的版本文字。
- Telegram summary 必須手機優先：短句、短行、少括號、少長名單。
- 最後一段 summary 是 Owner 打開 Telegram 最先看到的決策區，必須直接回答：
  - 今天能不能買。
  - 持倉先處理什麼。
  - 未持倉哪些只是追蹤。
  - 哪些不可行動。
- 不得為了「數字可追溯」犧牲語意。例如 `等冷卻` 不得塞進 `等回測` 分組。
- 分組標題必須與卡片狀態一致：
  - `等冷卻` 卡片只能在 `等冷卻` 分組。
  - `等回測` 卡片只能在 `等回測` 分組。
  - `等RR修復`、`等量能`、`淘汰` 同理。
- summary、漏斗、索引、詳情四處的分類名稱必須一致，不能一處叫 `等回測 4`，另一處實際是 `等冷卻 3 + 等回測 1`。
- 無可買時不得使用會像推薦的文案；只能寫 `追蹤最強` 或 `新倉：無有效進場`，且必須標示 `不可買`。
- `可買`、`準備`、`僅追蹤`、`不可行動` 必須分開，不得混在同一行造成誤讀。
- 未持倉長名單最多列 1-3 檔，超過用 `另 N 檔見詳情`；但不可把不同狀態混成一個 `另 N 檔`。
- 空區塊、零計數與無行動占位也算手機噪音。若某區塊沒有可執行或可追溯的實際項目，不得輸出 `明日計畫 0`、`明日計畫：無新增下單`、空標題、或等價的 0-count / no-op 文案，除非 PM 明確定義該空狀態對 Owner 決策有必要。
- 同義區塊不得重複同一行動。例如同一檔的 `明日未修復降級`、`收盤未修復，列入明日降級檢查`、`隔日降級檢查` 都視為同一持倉風控行動，不得同時出現在 `持倉風控檢查` 與 `明日計畫 / 隔日計畫`。
- 手機閱讀順序必須符合行動優先級：持倉風控與已持倉風險處理優先於新觸發 / 待觸發明日事項；若 PM 另有排序，必須在 `TASK.md` 明確寫出理由與示例。
- QA 驗收報文時必須實際檢查一段接近真實手機長報文，不得只查單一欄位存在。

### 持倉行動一致性硬規則

持倉建議不能讓 Owner 先加碼、下一段又減碼，或剛買入後又無條件叫賣。只要報文涉及持倉、今日交易、加碼、減碼、停損、停利，就必須套用本節。

- 同一檔股票在同一份報文中只能有一個主行動：`加碼 / 續抱 / 觀察 / 減碼 / 停損 / 停利 / 不動作` 擇一；不得在 summary、持倉卡、明日清單、詳情中互相衝突。
- `今日 買` 的持倉不得再顯示「可加碼」或像加碼的文案；預設只能是 `新倉風控觀察`，除非 PM 明確定義分批加碼規則且 QA 驗證不會造成追高。
- `今日 買` 後若訊號轉弱，報文可以升級為風控觀察或停損警戒；若要出現 `賣 / 減碼 / 停損`，必須在同一行說明觸發條件，例如跌破警戒、跌破停損、策略失效，而不是無脈絡反轉。
- 同一檔若同時符合強勢與風控條件，風控優先，summary 必須說「不加碼，先風控」；不得讓高層 `最強`、明日清單或詳情重新包裝成買入建議。
- PM 必須在 `TASK.md` 定義持倉行動優先級與衝突處理；Tech 必須列出行動來源與下游輸出同步；QA 必須用至少一個「剛買入後轉弱」和一個「高分但風控優先」案例反證。
- QA 發現同一標的在不同區塊出現相反行動，即使測試全綠，也必須 `blocked`。

### 報文噪音預算

報文不是資料傾倒。每個區塊只能承擔一種任務：決策、原因、追溯或詳情；不得反覆用不同話術重講同一件事。

- Summary 只回答決策，不重複完整名單；明細負責追溯，索引負責數量。
- 同一未持倉股票若不可買，summary / 執行清單 / 索引三者合計最多點名一次；淘汰股高層只顯示數量，不點名，除非 Owner 明確要求。
- 同一持倉股票可在持倉卡與執行清單出現，但行動文案必須一致；不得在多區塊重複完整條件、下一步、原因三次。
- 未持倉追蹤清單超過 3 檔時，summary 只列分類與數量；詳情再列股票。
- PM 必須為報文任務定義「哪些資訊放 summary、哪些放詳情、哪些只放索引」；Tech 必須避免跨區塊複製長句；QA 必須檢查重複點名、重複長句與同義噪音。
- PM 必須定義空區塊 / 0 計數是否顯示；若未定義，預設不顯示。Tech 不得用 `0`、`無新增下單`、空標題來占位。QA 必須把空區塊與 0-count 文案當成手機噪音檢查。
- 若 QA 判斷 Owner 打開手機後需要在多段重複文字中找真正行動，結論不得是 `通過`。

## Tech 自檢與 QA 驗證邊界

Tech 可以在交付前做「自檢」，目的只是避免把明顯壞掉的實作交給 QA。

### 測試環境規則

- Architect runner 在啟動 Tech / QA 前必須準備可用測試環境。
- Tech / QA worktree 若缺 `.venv`、`pytest` 或必要測試依賴，runner 必須自動補齊：
  - 優先使用主 repo 既有 `.venv`。
  - 若主 repo `.venv` 不可用，建立 worktree `.venv` 並安裝 `requirements.txt` 與測試依賴。
- 不得因為隔離 worktree 缺 `.venv`、缺 pytest、缺測試入口而直接降級、跳過或宣告通過。
- 若 runner 已補環境但測試仍不能執行，Tech / QA 必須標記 `blocked`，並列出實際錯誤與缺失依賴。
- 「環境缺失」是流程缺口，不是測試豁免理由。

Tech 自檢允許：

- 跑與本輪修改檔案直接相關的最小測試。
- 跑 formatter / helper / contract 的局部單元測試。
- 若任務要求不改策略，可跑少量策略不變性 smoke test 證明未破壞硬規則。
- 在 `CHANGELOG.md` 記錄已跑命令與結果。

Tech 自檢禁止：

- 做 QA 的完整驗收矩陣。
- 做關聯風險掃描、質疑與反證。
- 宣告整體 QA 通過。
- 跑 full pytest / replay / backfill，除非 `DISPATCH.md` 或 Owner 明確要求。

QA 驗證職責：

- 根據 `TASK.md` / `CHANGELOG.md` 獨立驗證結果。
- 可重跑 Tech 的最小命令，但不能只重複 Tech 測試；必須補直接消費者、負面案例、契約風險或使用者誤判風險。
- 若 QA 只重跑 Tech 命令而沒有新增風險判斷，視為 QA 不完整。
- QA 不只是執行 Owner / Architect / PM 指定清單；QA 必須主動從使用者視角找問題，包含需求沒寫、Tech 沒想到、摘要互相矛盾、文案可能誤導、重要資訊被壓縮後失真。
- QA 若只證明「指定欄位存在」而沒有檢查「輸出整體是否讓使用者做出正確判斷」，視為 QA 不完整。
- 對報文、summary、dashboard、Telegram 文字等使用者可見輸出，QA 必須做跨區塊語意一致性檢查：標題、今日結論、執行清單、漏斗、索引、詳情中的數量、狀態、優先級、可買/不可買語意不得互相矛盾。
- 當摘要有壓縮或排序限制時，QA 必須檢查被壓縮項是否仍可追溯，以及摘要文案是否清楚區分「執行項」與「僅追蹤候選」。
- QA 發現明顯使用者輸出問題時，即使測試命令通過，也必須標記 `blocked` 或 `conditional pass`，不得單純通過。

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
- Owner 提出產品 bug 時，Architect 預設也不得直接寫 `TASK.md`；只把 `DISPATCH.md` 設為 `pm_status: todo`、`tech_status: waiting_pm`、`qa_status: waiting_tech`，由 PM 產出任務卡。
- Architect 只有在 Owner 明確說「你直接改代碼 / 直接實作 / 不走部門」時，才可作為臨時 Tech 修改代碼。
- 每輪流程完成或阻塞後，Architect 必須做 Post-cycle Review Gate，把可重複失誤轉成固定規則或待補流程；不得只口頭提醒「下次注意」。

### PM / 產品

- 負責功能需求、報文設計、UI/流程、edge case。
- 輸出 `TASK.md`。
- 可讀 `CURRENT_STATE.md` 與 Architect 指令。
- 不修改代碼，不做全局分析。
- 必須按「PM 任務卡固定欄位」輸出，不得只寫口語摘要。
- 報文 / Telegram / UI 任務必須給手機閱讀路徑與示例輸出形狀。
- 若 Owner 需求不足以定義驗收條件，PM 寫 blocked，不得自行替 Owner 決定產品方向。

### Tech / 技術

- 負責功能實作、bug 修復、必要 refactor。
- 輸出 `CHANGELOG.md`。
- `CHANGELOG.md` 必須包含：修改內容、修改檔案、未影響模組。
- 只讀與 `TASK.md` 相關的局部源碼。
- 不重新分析全專案，不修改產品方向。
- 可做最小本地自檢，但不得替代 QA 驗收。
- 必須按「Tech 實作卡固定欄位」輸出。
- 若 `TASK.md` 缺直接消費者、驗收條件或輸出契約，Tech 必須 blocked，不得自行補需求。
- 若修改回傳結構、訊息順序、payload、報文分組或 public helper，必須同步直接呼叫方並在 `CHANGELOG.md` 明確說明。

### QA / 測試

- 負責差異測試、snapshot test、formatter test、契約檢查、關聯風險掃描。
- 輸出 `QA_REPORT.md`。
- 只測 `TASK.md` 與 `CHANGELOG.md` 指定影響範圍。
- 預設不做全局測試，不全 repo 掃描，不 refactor。
- 若 `DISPATCH.md` 指定 QA 分級為 `L3`，可執行 full pytest、replay/backfill dry-run、入庫 payload 路徑檢查與必要風險掃描。
- 若變更涉及 formatter output、messages list、Telegram payload、DB payload 或任一公開函式回傳契約，QA 必須補測直接消費者，不得只測產出函式本身。
- QA 必須主動質疑 PM / Tech 的影響範圍，列出「可能漏掉的直接消費者、間接依賴、邊界情境、負面案例」。
- QA 若發現 `TASK.md` 或 `CHANGELOG.md` 未列出必要關聯模組，不得直接判定通過；必須在 `QA_REPORT.md` 標記 blocked 或 conditional pass。
- QA 不應只重複 Tech 自檢；必須補充 Tech 沒覆蓋的風險與反證。
- QA 必須把自己視為最後一道使用者體驗與風險防線，不得只做「照單驗收」。
- QA 必須主動提出 PM / Tech 未要求但與本輪輸出直接相關的問題；若沒有發現問題，也必須在 `質疑與反證` 中說明探索過哪些方向。
- 必須按「QA 驗收卡固定欄位」輸出。
- QA 的價值不是重複 Tech 自檢，而是主動找 PM / Tech 沒想到的錯誤、衝突、誤讀與下游破壞。
- 若 QA 沒有提出至少一條主動質疑或反證路徑，即使測試全綠，也只能是 `conditional pass` 或 `阻塞`，不得直接 `通過`。
- QA 對報文類任務至少要檢查：
  - 單一欄位是否正確。
  - 區塊之間是否互相矛盾。
  - 數量統計是否能對上明細或索引。
  - 排序是否符合使用者打開 Telegram 後的閱讀路徑。
  - 文案是否會把「不可買 / 等待 / 追蹤」誤讀成「可買 / 必須執行」。
  - 重要風控或持倉盈虧是否因壓縮而消失。

QA_REPORT 固定章節：

- `測試範圍`：列出依據與實測範圍。
- `關聯風險掃描`：列出直接呼叫方、資料流下游、外部副作用與未覆蓋契約。
- `跨區塊語意一致性`：對使用者可見輸出，檢查各區塊數字、狀態、排序、結論與詳情是否互相支持；若不適用需說明原因。
- `使用者誤讀風險`：列出可能讓 Owner 誤判買入、賣出、加碼、停損、等待、追蹤優先級的文案或排序風險。
- `質疑與反證`：至少回答「PM 是否漏需求」、「Tech 是否漏同步」、「測試是否能證明沒有破壞直接消費者」、「QA 是否主動找到指定清單之外的風險」。
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

## 文件寫入權限

開發任務：

- Architect 只改寫 `DISPATCH.md`、`CURRENT_STATE.md`、`AGENTS.md`、`CLEANUP_PLAN.md`；不得手寫 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`，除非 Owner 明確指定 Architect 代該角色。
- PM 只改寫 `TASK.md`。
- Tech 只改寫 `CHANGELOG.md`，並修改 `TASK.md` 指定範圍內的代碼 / 測試。
- QA 只改寫 `QA_REPORT.md`。
- Architect 改寫 `DISPATCH.md`、`CURRENT_STATE.md`、`AGENTS.md`、`CLEANUP_PLAN.md`，並在研究收口時整理 `RESEARCH.md`。

CAO 自動開發例外：

- CAO Tech 可寫代理不得直接寫主工作區。
- CAO Tech 可寫代理只允許在隔離 worktree 修改代碼、測試與 `CHANGELOG.md`。
- CAO QA 代碼代理可讀隔離 worktree，不修改 tracked files；只允許 runner 準備的 `.qa_tmp/` 作為測試暫存。
- Architect-controlled runner 可將 PM / QA 交付摘要寫回主 repo 的 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`，但代碼改動仍停留在隔離 worktree，需 Architect 檢查 diff 後才可合併。
- CAO 自動開發不得 commit、push、live Telegram、live Supabase write 或正式 backfill。

研究任務例外：

- `RESEARCH.md` 是共享研究文件，不屬於 PM 單獨所有。
- PM 可在 `PM Findings` 區塊寫入產品研究。
- Tech 可在 `Tech Findings` 區塊寫入可行性與影響模組研究。
- QA 可在 `QA Findings` 區塊寫入風險掃描、質疑與反證。
- Architect 可改寫 `Question`、`Evidence`、`Architect Conclusion`、`Next Action`，並可壓縮舊研究內容。
- 各角色不得改寫其他角色 Findings，除非 `DISPATCH.md` 明確要求覆蓋舊區塊或重跑該角色輸出。

若任務已從研究進入開發，角色必須回到開發任務文件權限，不再繼續改 `RESEARCH.md`。

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

## CAO 自動代理接入

本專案使用自定義 `stock_*` agents，不使用 CAO 內建 `code_supervisor`、`developer`、`reviewer` 作為正式工作流角色。

Owner 與 Architect 的使用層只保留一個入口腳本：

- `tools/cao_agent/run_architect_task.sh research "<研究問題>"`
- `tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"`
- `tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"`

底層 runner 只作為內部工具，不作為日常入口。Owner 不需要直接操作 PM / Tech / QA agent。

已允許的本地 CAO profiles：

- `stock_pm_online_readonly`：PM 線上研究，只讀，可查公開網路資料。
- `stock_qa_online_readonly`：QA 線上研究，只讀，可查公開網路資料。
- `stock_tech_safe`：Tech 只讀規劃，不改碼。
- `stock_tech_write_sandbox`：Tech 可寫實作，只能在隔離 worktree。
- `stock_qa_code_readonly`：QA 代碼驗證，讀隔離 worktree；不改 tracked files，只允許 `.qa_tmp/` 測試暫存。

可用 runner：

- `tools/cao_agent/run_architect_task.sh "<mode>" "<任務>"`
- `tools/cao_agent/run_project_research.sh "<研究問題>"`
- `tools/cao_agent/run_tech_plan.sh "<技術規劃問題>"`
- `tools/cao_agent/run_tech_write.sh "<實作指令>"`
- `tools/cao_agent/run_qa_code.sh "<驗證指令>"`
- `tools/cao_agent/run_auto_dev_cycle.sh "<Owner 任務>"`

CAO 前端 UI 固定入口：

- API server：`http://127.0.0.1:9889/`
- 前端 UI：`http://127.0.0.1:5173/`
- 中文化前端預設目錄：`$HOME/.local/share/cao-web-zh/web`，可用 `CAO_WEB_DIR` 覆蓋。
- 啟動前端由 `tools/cao_agent/ensure_cao_services.sh` 負責。
- 啟動 API 由 `tools/cao_agent/ensure_cao_services.sh` 負責，預設使用 `$HOME/.local/bin/cao-server`。
- CAO 服務確認命令：`tools/cao_agent/ensure_cao_services.sh`
- Architect 只要分配 / 啟動 / 使用 CAO agents，或回覆 Owner 前端 UI 地址前，必須先確認 `9889` API 與 `5173` 前端正在 listen；若未啟動，必須先執行 `ensure_cao_services.sh` 啟動，再回覆前端 UI 地址 `http://127.0.0.1:5173/`。
- 不得再用 `/tmp` 內重新 clone 的 upstream 英文前端作為日常 UI；若固定中文化目錄缺失，必須先重建中文化 UI 並更新本節。

安全邊界：

- 只有 Architect-controlled runner 可以呼叫 CAO agents；agents 不得自行 handoff / assign / send_message 叫其他 agent。
- PM / Tech / QA 不互相指揮，不互相覆蓋文件；所有串接由 Architect runner 控制。
- PM / QA online 只同步摘要 Markdown，不讀真實 repo。
- Tech write 使用 Codex `workspace-write`，主 repo 寫入測試已驗證為 blocked。
- Tech write 允許 Codex 必要網路連線；不得使用 CAO 內建未審核規則，不得下載依賴、上傳專案內容或呼叫 live 外部副作用，除非 Architect 明確批准。
- 自動循環完成後，代碼 diff 留在隔離 worktree；Architect 負責檢查、決定是否合併到主 repo。
- CAO 輸出只能作為候選交付；若輸出混入 shell transcript、debug log、完整聊天、未壓縮 reasoning，Architect 必須拒收或清理後再寫入固定文件。
- CAO auto 任務若未產生合格的 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 三件套，不得標記完成。

Runner hygiene gates：

- `run_tech_write.sh` 每輪必須從乾淨隔離 worktree 開始，並清掉上一輪 tracked / untracked 殘留；`.venv` 只作測試環境保留，不得成為候選 diff。
- `run_tech_write.sh` 清理起點必須對齊主 repo 當前 `HEAD`，不得只 reset 到隔離 worktree 自己的舊 `HEAD`；避免舊版本基線反覆污染新任務。
- Architect 每次已吸收候選 diff 並完成 commit / push 後，必須執行 `tools/cao_agent/cleanup_agent_worktrees.sh`，把隔離 worktree reset 到主 repo 當前 `HEAD` 並移除 tracked / untracked / `.qa_tmp` 殘留；只保留 `.venv`。
- `cleanup_agent_worktrees.sh` 只能在主 repo clean 時執行；若主 repo 仍有未提交 diff，必須先完成 commit / push 或明確放棄本輪修改，不得清理隔離 worktree 造成候選 diff 遺失。
- Tech runner 可同步主 repo 的交接文件供 agent 閱讀，但 `AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`QA_REPORT.md` 都是 read-only handoff context，不得出現在候選 diff；runner 必須用 hash 檢查代理是否偷改。
- Tech 候選 diff 只應包含 `TASK.md` 允許的產品 / 測試檔，以及 Tech 交付的 `CHANGELOG.md`；其他固定 Markdown 殘留一律不得整包合併。
- `run_qa_code.sh` 仍是 read-only QA；只允許寫 `.qa_tmp/`、dummy `config.py` 與測試暫存，不得修改 tracked files。
- QA runner 必須在 QA 前後檢查候選 diff hash 與 handoff file hash；若 QA 改了 tracked diff 或交接文件，結果直接拒收。
- Runner 從 CAO 終端抽取交付時，只能吸收最後一個合法標題後的內容：`# TASK:`、`# CHANGELOG:`、`# QA_REPORT:`；若抽取結果仍混入 transcript、終端流水或缺標題，必須失敗。
- `run_auto_dev_cycle.sh` 只有在 QA 報告結構合格後，才可把 `CHANGELOG.md` 與 `QA_REPORT.md` 寫回主 repo；QA 失敗時不得留下看似完成的 Tech 交付。
- performance 類任務若沒有 production benchmark，只能以 query contract / mock call count 給 `conditional pass`，不得宣告完全通過。

收縮規則：

- 不再新增新 agent，除非現有五個角色無法覆蓋且 Owner 明確批准。
- 日常只用三種模式：`research`、`plan`、`auto`。
- 若任務不是明確開發，預設不跑 `auto`。
- 若 `TASK.md` 不完整，Tech write 必須 blocked，不得自行補產品需求。
- 若 QA 報告不是完整輸出，Architect 不得吸收為通過。
- 若只是流程 / 文件規則優化，預設不跑 PM / Tech / QA agent，Architect 直接更新固定文件即可。

## Git 發布規則

- Tech 負責本地實作與局部驗證，預設不直接 push，除非 Owner 明確要求。
- QA 負責驗證，不 commit，不 push。
- Architect 收口後可負責 commit / push。
- Architect commit / push 前可檢查代碼 diff，但不得補寫功能代碼；若發現缺口，回派 Tech。
- Architect commit 前必須檢查 `git status`、`git diff --stat` 與必要 diff。
- Architect 只提交本輪 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 對應範圍內的文件，以及 Architect 狀態文件。
- 若工作區有不明來源改動，Architect 必須排除或請 Owner 確認，不可無差別提交。
- Owner 明確要求「把本地最新修改推送」時，Architect 仍需先檢查 diff，再將確認屬於本輪工作流與代碼變更的文件提交推送。
- Owner 明確說「對比後沒問題就直接 push / 自己 push / 對齊 git」時，這視為本輪發布授權；Architect 完成 final diff review、必要驗證與 commit 後，若沒有不明 diff 或測試阻塞，必須直接 push，不再二次詢問。
- 若 final diff review 發現不明來源改動、交付文件矛盾、QA 未通過、測試阻塞或 live 副作用風險，Architect 不得 push，必須標記 blocked 或回報 Owner。

## Push 後壓縮規則

每次 Architect 完成 commit / push 後，下一步必須做上下文壓縮，避免 Markdown 文件變成新的長聊天紀錄。

壓縮前必須先完成 Post-cycle Review Gate；若發現需要補 agent / runner / 流程規則，先更新固定文件，再壓縮與收口。

- `DISPATCH.md`：只保留當前任務狀態與固定啟動句，不保留歷史任務過程。
- `TASK.md`：只保留最新任務；舊任務只保留 3-5 行摘要到 `CURRENT_STATE.md`。
- `CHANGELOG.md`：只保留最新任務；舊實作只保留 3-5 行摘要到 `CURRENT_STATE.md`。
- `QA_REPORT.md`：只保留最新任務；舊測試只保留命令、結果、未測範圍摘要到 `CURRENT_STATE.md`。
- `RESEARCH.md`：只保留最新研究問題、結論、下一步；刪除長過程與完整報文。
- `CURRENT_STATE.md`：每個版本只保留高信號摘要，不貼完整報文、不貼完整 diff。
- `CLEANUP_PLAN.md`：只保留待處理項與清理規則，不保留已完成流水帳。
- 壓縮不得刪除固定 8 份 Markdown 文件，只能改寫內容。
- 壓縮時必須檢查 `AGENTS.md` 是否有案例化、重複化或已被新規則取代的文字；能合併就合併，不能確認用途就先記入 `CLEANUP_PLAN.md`，不得靠文件膨脹維持記憶。
