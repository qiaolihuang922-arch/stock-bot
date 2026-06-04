# TASK: 新增可選第 4 則 Telegram「未來30日關注」推送

## 任務狀態

- task_id: telegram_future_30d_watch_v20_4_45
- 任務類型: minor
- 狀態: ready_for_tech
- 建議版本: v20.4.45
- QA 分級建議: L3
- 原因: 新增使用者可見 Telegram message，涉及官方資料源、跨月 30 日查詢、message list 契約與手機閱讀風險；不改策略決策、不改 DB schema。

## Owner 問題

Owner 要在既有 Telegram 推送中新增「未來 30 日要關注的時間點」，但不能污染既有決策簡報。新增內容需涵蓋：

1. 今天盤勢很像台灣曾經哪一次崩盤的時間線。
2. 哪些股票準備法說會。
3. 全球未來 30 日大事件。

本功能必須以手機閱讀為第一視角，資料不足時 fail closed，不得假造事件或主觀硬套崩盤類比。

## 使用者可見結果

- Telegram 推送可選新增第 4 則 message。
- Header 使用同一份報文版本，標題為：
【未來30日關注】
- 既有第 1-3 則決策簡報、持倉、候選、風控內容不得被插入、重排或語意污染。
- 若三個區塊都無可信資料，該第 4 則可不產生；若只部分區塊有資料，只顯示有資料區塊與必要 fail-closed 狀態。
- 手機閱讀路徑：使用者打開 Telegram 後，先讀既有決策簡報；若要看未來事件，往下讀第 4 則，能在 1 屏內先看到「是否有高相似崩盤樣本、法說會提醒、全球事件」。

## 非目標

- 不改既有買賣、加減碼、停損停利、持倉狀態機或策略 decision。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不寫 production DB。
- 不 live Telegram delivery。
- 不新增主觀市場預測模型。
- 不把歷史崩盤類比寫成預測或警報。
- 不列全市場所有法說會，只列持倉、watchlist、未持倉候選相關股票。
- 不把全球事件混入既有 Summary 或候選推薦區塊。

## 影響模組與直接消費者

影響模組：

- Telegram official generator。
- Telegram message list 組裝流程。
- 報文版本/header 常量或 formatter。
- 未來 30 日事件資料組裝 helper。
- MOPS 法說會資料讀取 adapter。
- 全球事件資料讀取/fixture adapter。
- 歷史崩盤類比 helper。
- official generator/message-list tests。

直接消費者：

- Telegram 手機閱讀使用者。
- 既有 Telegram runner/message sender 的 message list。
- QA replay / official generator 測試。
- 之後可能消費相同 future-watch payload 的 CLI/report artifact。

## 輸出契約

### Message List 契約

- 新增 message 為可選第 4 則。
- 既有 message 1-3 的順序、內容、header、版本不得回退。
- 第 4 則只有在至少一個區塊有可顯示內容或明確 fail-closed 狀態需要提示時產生。
- 第 4 則不得影響既有 summary 決策文字。

### Header 契約

第 4 則 header 形狀：

台股策略速報 v20.4.45
【未來30日關注】

若 repo 既有 header 格式不同，Tech 必須沿用既有正式 header 格式，只新增同版本與 【未來30日關注】 標題，不得回退版本。

### 區塊順序

第 4 則固定區塊順序：

1. 歷史類比
2. 法說會提醒
3. 全球事件

空資料區塊處理：

- 法說會查無資料：不占版、不顯示 0-count。
- 全球事件查無資料或 source-error：顯示 fail-closed 狀態，不得假造事件。
- 歷史類比資料不足或相似度低：必須顯示無高相似樣本，不得空白造成誤讀。

### 歷史類比契約

輸入：

- today market features：可得欄位包含跌幅、量能、market_grade、breadth/limit-down、連跌、遠離均線等。
- historical timeline source：優先 repo 既有 market_theme_index_daily_bars / TWSE official index source；若本輪環境無法取得，可使用可注入 fixture。
- 必須量化相似度與門檻。

輸出：

- 若有高相似樣本：
- 日期或事件短名。
- 相似度。
- 主要相似特徵，最多 3 個。
- 明確標示「類比不是預測」。
- 若資料不足或相似度低於門檻：
- 固定文案：
歷史類比：無高相似崩盤樣本｜依據不足/相似度低

禁止：

- 不得用主觀描述硬套歷史崩盤。
- 不得出現「即將崩盤」「重演」等預測式文字。

### 法說會契約

資料來源：

- 官方 MOPS endpoint:
https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1
- Method: POST
- 欄位：
- TYPEK: sii / otc / rotc / pub
- year: 民國年，例如 2026 年為 115
- month: 月份
- co_id: 股票代號
- Owner 提供研究摘要：
- 實測可回 115/06 光寶科 2301 法說會資料。
- 115/07 查無資料。
- TWSE WebPro schedule 顯示法人說明會 / MOPS 法說會 / 公司自辦法說會入口。

查詢範圍：

- 未來 30 日，必須支援跨月。
- 只查持倉 + watchlist / 未持倉候選相關股票。
- 最多顯示 5 筆。
- 日期升冪排序。
- 查無資料不占版。

每筆顯示欄位：

- 日期。
- 股票代號與名稱。
- 事件短名。
- 關注原因：持倉 / 候選 / 同產業。
- source=MOPS

source-error / 被擋：

- 不得使用非官方資料補假資料。
- 若 MOPS 被擋或解析失敗，顯示 fail-closed 狀態，例如：
法說會提醒：source-error（MOPS），本次不列事件

### 全球事件契約

資料來源優先官方，Owner 已提供可用來源：

- Fed FOMC 2026 calendar：2026/06/16-17 SEP meeting。
- BLS CPI schedule：May 2026 CPI 2026/06/10 08:30 ET。
- BEA schedule：2026/06/25 GDP third estimate + Personal Income and Outlays May 2026。
- ECB calendar：2026/06/10-11 monetary policy meeting / press conference。
- BOJ release calendar：2026/06/15-16 MPM。
- BoE MPC calendar：2026/06/18 next due。
- G7 official France interior page：Evian 2026/06/15-17。

查詢範圍：

- 未來 30 日。
- 最多顯示 5 筆。
- 日期升冪排序。
- 每筆必須有官方 source 標記。
- 若同日多事件，排序需穩定，優先顯示影響面更直接者：利率、通膨、匯率、能源、政治風險。

每筆顯示欄位：

- 日期。
- 事件。
- 影響面：利率 / 通膨 / 匯率 / 能源 / 政治風險。
- source。

source-error / 查無資料：

- 不得假造事件。
- 顯示 fail-closed 狀態：
全球事件：source-error，本次不列未確認事件
或
全球事件：未查到未來30日官方事件

## 版本契約

- 使用者可見報文版本建議升為 v20.4.45。
- 若 repo 已有更高版本，Tech 必須不得回退，應沿用或升至下一個合理版本，並在 CHANGELOG.md 記錄實際版本。
- 第 4 則 header 版本需與正式 Telegram header 常量一致。
- 測試必須驗證 header 實際輸出版本與常量一致。

## 已存在且不得回退的契約

- 既有 Telegram message 1-3 的順序不得改變。
- 既有 Summary 只回答決策，不得混入未來 30 日全球事件或法說會清單。
- 可買、可準備、僅追蹤、淘汰 / 不可行動仍須分開。
- 無可買時不得使用像推薦的文案。
- 同一持倉在同一份既有報文只能有一個主行動。
- 空區塊、0-count、無新增下單占位預設不顯示。
- live Telegram delivery 仍需 Owner 單獨批准。

若 Tech 發現上述契約在 repo 中無法確認，需在 CHANGELOG.md 標記 blocked/partial，不得自行假設已保留。

## 驗收條件

Tech 必須補 official generator / message-list 層級測試，不可只測 helper。

至少驗收：

1. Message list
- 有未來 30 日資料時，產生可選第 4 則。
- 第 4 則 header 含實際版本與 【未來30日關注】。
- 既有 message 1-3 順序與內容不被第 4 則污染。
2. 手機閱讀
- 第 4 則依序顯示歷史類比、法說會提醒、全球事件。
- 每區塊短句、最多 5 筆，不出現長段資料流水。
- 空法說會不顯示 0-count。
3. 歷史類比
- 無足夠歷史資料時輸出：
歷史類比：無高相似崩盤樣本｜依據不足/相似度低
- 相似度低於門檻時同樣不得硬套崩盤。
- 有 fixture 高相似樣本時，顯示相似度與最多 3 個相似特徵，且含「類比不是預測」。
4. 法說會跨月 30 日
- 以 2026/06 中下旬日期作 fixture 時，查詢需涵蓋 115/06 與 115/07。
- 115/06 2301 光寶科 fixture 可顯示。
- 115/07 查無資料不占版。
- source-error 時 fail closed，不假造資料。
5. 全球事件
- 官方 fixture 中事件按日期升冪排序。
- 最多 5 筆。
- 每筆顯示影響面與 source。
- source-error 時 fail closed，不列未確認事件。
6. 禁止副作用
- 不改 DB schema。
- 不寫 production DB。
- 不觸發 live Telegram。
- 不改策略 decision 結果。

QA 必須反證：

- 手機閱讀是否會誤讀為買賣建議。
- source-error fail closed。
- 無高相似樣本不硬套崩盤。
- 法說會跨月 30 日。
- 全球事件排序與來源標記。
- Tech 是否真的測到 official generator/message-list，而非只測 helper。

## 範例或 Fixture

### 示例輸出形狀

台股策略速報 v20.4.45
【未來30日關注】

歷史類比
歷史類比：無高相似崩盤樣本｜依據不足/相似度低

法說會提醒
06/xx 2301 光寶科｜法人說明會｜關注原因：持倉｜source=MOPS

全球事件
06/10 美國 CPI（May 2026）｜影響面：通膨/利率｜source=BLS
06/10-11 ECB 利率會議/記者會｜影響面：利率/匯率｜source=ECB
06/15-16 BOJ MPM｜影響面：利率/匯率｜source=BOJ
06/16-17 Fed FOMC SEP｜影響面：利率/匯率｜source=Fed
06/18 BoE MPC｜影響面：利率/匯率｜source=BoE

### Fixture 要求

- MOPS fixture:
- TYPEK=sii
- year=115
- month=06
- co_id=2301
- 含一筆光寶科法說會。
- MOPS 查無 fixture:
- year=115
- month=07
- 回傳查無資料。
- MOPS source-error fixture:
- 模擬 blocked / timeout / parse error。
- 全球事件 fixture:
- 包含 Owner 提供官方事件，測最多 5 筆與日期排序。
- 歷史類比 fixture:
- 一組資料不足。
- 一組相似度低。
- 一組高相似樣本。

## 失敗標本與驗收路由

失敗標本：

- 本輪無 Owner 貼出的完整既有報文；Tech 需用 official generator replay artifact 建立等價驗收標本。
- 驗收標本必須覆蓋正式 message list，而非只覆蓋 formatter/helper。

驗收路由：

1. helper：future-watch payload 組裝。
2. data adapter：MOPS / global events / historical timeline fixture。
3. formatter：第 4 則文字。
4. official generator：正式 Telegram 報文產出。
5. message list：第 4 則可選追加且不污染第 1-3 則。
6. runner artifact：若 repo 已有 dry-run/replay 入口，需產出可檢視 artifact；若無入口，CHANGELOG 寫明未覆蓋 runner artifact。

## 明確禁止事項

- 禁止改 DB schema。
- 禁止 production DB write。
- 禁止 live Telegram delivery。
- 禁止假造 MOPS 或全球事件。
- 禁止使用非官方全球事件來源取代 Owner 指定官方來源，除非 PM/Architect 另開研究任務確認。
- 禁止把歷史類比寫成預測。
- 禁止把第 4 則內容插入既有決策簡報。
- 禁止只測 helper 就宣稱完成。
- 禁止超過 5 筆法說會或 5 筆全球事件。
- 禁止查無資料顯示空 0-count 區塊。
- 禁止回退既有 Telegram 版本/header 契約。

## 阻塞條件

Tech 遇到以下情況需 blocked 或 partial，不得宣稱完成：

- 找不到 official generator/message-list 測試入口，且無法建立等價 replay artifact。
- 無法確認既有 Telegram header/version 常量。
- 無法取得或 fixture 化 MOPS source contract。
- 無法建立跨月 30 日查詢測試。
- 歷史資料源不足且未能使用可注入 fixture 驗證 fail-closed。
- 全球事件官方來源無法解析且無 source-error fail-closed 測試。
- 任何實作需要 DB schema change、production DB write 或 live Telegram。

## 本輪停止條件

本輪完成定義：

- TASK.md、CHANGELOG.md、QA_REPORT.md 均符合標題與契約。
- Tech 已實作可選第 4 則 Telegram message，且補 official generator/message-list 測試。
- QA 結論為 通過 或明確 conditional pass 並列出未覆蓋 runner/production 層。
- Architect 後續依流程更新 DISPATCH.md / CURRENT_STATE.md，QA 通過後再 commit/push/gate。

本輪不處理：

- 擴大為完整經濟日曆平台。
- 全市場法說會搜尋 UI。
- 歷史崩盤模型優化或策略重設。
- DB 持久化事件快取。
- live Telegram 實際發送。
