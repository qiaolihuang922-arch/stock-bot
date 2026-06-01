# TASK: v20.4.21 盤後 Telegram 報文摘要化與樣本狀態一致性修正

## 任務狀態

- task_id: pm-20260601-afterhours-v20421-report-copy-and-sample-state
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見盤後 Telegram 報文需升版或至少不得低於 v20.4.21；若現有版本常量已高於此版本，不得回退。
- QA 分級建議: L2
- 本輪停止條件: 只修正盤後 Telegram 報文的文案結構、狀態呈現與 RR 顯示契約，並補一個可重跑檢查或 QA probe 覆蓋本次錯誤類型；不重設策略、不改 DB、不補歷史資料、不做 live delivery。

## Owner 問題

Owner 要優化 v20.4.21 盤後 Telegram 報文，解決以下使用者可見問題：

1. 第三則簡報目前像是複製 summary 全文，沒有真正摘要化。
2. 策略樣本狀態同時出現 missing-source 與 sample insufficient 類似訊息，造成重複或衝突。
3. 每檔卡片重複顯示「策略樣本不可用」行，手機閱讀負擔過高。
4. 盤後卡片出現盤中語境，與盤後報文場景不符。
5. 持倉 RR 規則不一致：非加碼持倉不應顯示新倉 RR 數字。
6. 完成後需要對今天錯誤做流程強化，但不得新增死規則；應補可重跑檢查或 QA probe。

## 使用者可見結果

Owner 在手機上閱讀盤後 Telegram 報文時應看到：

- 第三則簡報是一段高密度摘要，不再複製第一則 summary 或完整決策全文。
- 策略樣本狀態只在第三則或全局說明中統一說明一次。
- 單檔卡片不再每檔重複「策略樣本不可用」。
- 盤後卡片只使用盤後語境，例如「盤後觀察」、「明日開盤前確認」、「收盤後狀態」，不得出現「盤中留意」、「盤中觸發」等盤中行動語氣。
- 非加碼持倉卡片不顯示新倉 RR 數字；只有加碼候選或新倉候選可顯示對應 RR。
- repo 內新增或更新一個可重跑檢查 / QA probe，能檢出本輪至少一類錯誤：第三則複製全文、樣本狀態重複、卡片重複樣本不可用、盤後出現盤中語境、非加碼持倉顯示新倉 RR。

## 非目標

- 不改策略選股、買賣、加碼、減碼、停損、停利決策。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 DB write、backfill、production DML。
- 不發 live Telegram。
- 不重寫整份 Telegram 報文系統。
- 不清理全 repo、不做全量 refactor。
- 不更改 production 持倉 source-of-truth。
- 不把本輪流程復盤寫成不可驗證的新增死規則；必須落到可重跑檢查或 QA probe。

## 影響模組

Tech 需依 repo 實際結構定位，預期影響範圍限於：

- 盤後 Telegram 報文組裝 / formatter。
- 第三則簡報內容生成邏輯。
- 策略樣本狀態顯示邏輯。
- 持倉 / 新倉 / 加碼卡片 RR 顯示邏輯。
- 報文版本字串或 header 常量。
- 測試、fixture、snapshot 或 QA probe 腳本。

若實際修改需要碰策略 decision、DB write path、跨日狀態機或 schema，Tech 必須停止並回報 blocked，不得自行擴大。

## 直接消費者

- Owner 的手機 Telegram 盤後報文閱讀路徑。
- GitHub runner / 正式 runner 產生的盤後 Telegram message list。
- QA 驗收用的可重跑 fixture、snapshot 或 probe。
- 任何依賴同一 message list 的 dry-run / preview CLI。

## 已存在且不得回退的契約

- 報文版本不得低於 v20.4.21；若程式內已有更高版本，維持更高版本並同步可見 header / 常量 / 測試。
- Telegram 仍應輸出多則 message list；本輪只調整第三則摘要與卡片文案，不把多則報文合併成單則。
- Summary 仍只回答決策：今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤、哪些不可行動。
- 可買、可準備、僅追蹤、淘汰 / 不可行動仍需分組一致。
- 無可買時不得使用像推薦的文案；應呈現「新倉：無有效進場」或等價不可買表述。
- 同一持倉在同一份報文只能有一個主行動。
- 空區塊、0-count、無新增下單占位預設不顯示。
- live Telegram delivery 仍需 Owner 單獨批准，本輪不得執行。

若 Tech 無法確認以上任一契約在現有程式中的位置，需在 CHANGELOG.md 標明未確認項；若會造成行為不明，應 blocked。

## 輸出契約

### Message List

- 維持既有盤後 Telegram message list 的順序與基本分則數量，除非現有程式本來動態省略空訊息。
- 第三則簡報必須是摘要訊息，不得逐段複製第一則 summary 全文。
- 第三則需集中承載全局策略樣本狀態說明：
- 若策略樣本來源缺失或不足，只允許一個統一狀態。
- 狀態文案需能區分「資料來源缺失」與「樣本不足」，但同一 run 不得同時把同一樣本問題寫成兩種互相競爭的主狀態。
- 建議形狀：策略樣本：本次不可用（原因：樣本不足 / 來源缺失），單檔卡片不重複列示。

### 第三則摘要

第三則不得包含：

- 第一則 summary 的完整原文。
- 每檔卡片完整明細。
- 重複的策略樣本不可用行。
- 盤中行動語境。

第三則應包含：

- 盤後總結 1-3 行。
- 全局策略樣本狀態 1 行。
- 明日或下一交易日前需確認的高層級事項 1-3 點。

手機閱讀示例形狀：

📌 盤後簡報
結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。
策略樣本：本次不可用（原因：樣本不足），單檔卡片不重複列示。
明日前確認：觀察持倉是否跌破警戒；新倉候選需重新等待有效進場。

### 單檔卡片

單檔卡片不得每檔重複：

策略樣本不可用
sample insufficient
missing-source

除非該檔有不同於全局狀態的特殊資料錯誤；若有，需用單一明確狀態，不得同時顯示衝突原因。

盤後卡片不得使用盤中語境，例如：

盤中留意
盤中觸發
盤中可追
即時進場

應改為盤後語境，例如：

盤後觀察
明日開盤前確認
收盤後風控觀察
等待下一交易日訊號

### 持倉 RR

- 新倉候選可顯示新倉 RR。
- 加碼候選可顯示加碼 RR 或加碼風險報酬。
- 非加碼持倉不得顯示新倉 RR 數字。
- 非加碼持倉若需要風控資訊，只能顯示持倉風控、停損距離、警戒價或已持倉語境，不得混成新倉 RR。

## 驗收條件

1. 使用盤後 fixture 產生 Telegram message list 時，第三則簡報不等於也不包含第一則 summary 的完整文字；第三則長度與內容呈摘要形狀。
2. 當策略樣本不可用時，整份報文只出現一個全局策略樣本狀態說明；單檔卡片不重複列示相同不可用行。
3. 同一策略樣本問題不得同時以 missing-source 與 sample insufficient 兩種主狀態呈現。
4. 盤後卡片不得包含盤中語境關鍵詞。
5. 非加碼持倉卡片不得顯示新倉 RR 數字；加碼 / 新倉候選仍可顯示對應 RR。
6. 報文版本 header / 常量 / 測試預期不得低於 v20.4.21，且不可和實際輸出不一致。
7. 新增或更新至少一個可重跑檢查、snapshot test、fixture test 或 QA probe，能在 CI 或本地命令中檢出本輪錯誤類型。
8. Tech 自檢不得包含 DB write、live Telegram、DB schema 變更。
9. QA 需補一個 Tech 未覆蓋的反證路徑，例如手機閱讀路徑掃描、負面 fixture、或直接檢查 message list 中第三則與卡片的語意衝突。

## 範例或 Fixture

Tech 應新增或更新一個最小盤後 fixture，至少包含：

- 第一則 summary 有完整決策文字。
- 第三則簡報會被驗證不得複製第一則全文。
- 策略樣本不可用，原因可為 sample insufficient 或 missing-source 其中之一。
- 至少兩檔單檔卡片，避免每檔重複樣本不可用行。
- 至少一檔非加碼持倉，帶有可誘發錯誤的新倉 RR 欄位或資料。
- 至少一檔新倉或加碼候選，確認 RR 顯示沒有被全局移除。

示例輸出形狀：

[Message 1]
盤後 Summary：新倉無有效進場；持倉 A 續抱觀察；B 僅追蹤。

[Message 2]
持倉卡片
A｜盤後觀察｜警戒價 123
不得出現：新倉 RR 2.1

候選卡片
C｜等待下一交易日訊號｜新倉 RR 2.4

[Message 3]
盤後簡報
結論：新倉無有效進場；持倉以收盤後風控觀察為主。
策略樣本：本次不可用（原因：樣本不足），單檔卡片不重複列示。
明日前確認：A 是否跌破警戒；C 是否重新出現有效進場。

## 明確禁止事項

- 禁止 DB write。
- 禁止 live Telegram。
- 禁止 DB schema / RLS / grant / policy / role / index / constraint 變更。
- 禁止繞過既有 repo interface 手寫 production DML。
- 禁止把 Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 直接來」解讀成跳過 PM / Tech / QA。
- 禁止把本輪擴成策略重設、全量清理、全報文重構或 L3 大驗證。
- 禁止新增不可重跑、只靠文件記憶的死規則作為流程強化。
- 禁止用 local cache、agent 對話或 runtime dict 當跨日狀態 source-of-truth。
- 禁止在缺資料、缺環境、source-error 時宣告通過。

## 阻塞條件

Tech 應 blocked 並回報 Architect，如果出現任一情況：

- 無法定位盤後 Telegram message list 或第三則簡報產生入口。
- 現有版本常量 / header 不明，無法保證不回退 v20.4.21。
- 修正 RR 顯示必須改策略 decision 或持倉狀態機，而不只是報文呈現。
- 需要 DB schema、DB write、production DML 或 live Telegram 才能驗收。
- 無法建立或執行最小可重跑 fixture / probe。
- 現有輸出契約與本 TASK 的不得回退契約衝突，且無法用局部 formatter 修正。

## 流程強化要求

本輪完成後，Tech 需在 CHANGELOG.md 說明新增或更新的可重跑檢查 / QA probe：

- 檢查名稱與命令。
- 覆蓋哪一類今天錯誤。
- 失敗時如何提示。
- 未覆蓋哪些旁支風險。

QA 需驗證該 probe 不是只檢查存在性，而能對至少一個負面案例失敗。

## 旁支問題處理

以下問題不納入本輪完成條件，只能記入後續待辦或 CLEANUP_PLAN.md：

- 全部 Telegram 報文資訊架構重設。
- 全量策略樣本資料品質治理。
- DB source-of-truth 補強。
- 持倉狀態機或策略 RR 計算邏輯重寫。
- 多日 replay / backfill。
- production live delivery 流程調整。
