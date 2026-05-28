# TASK: v20.0.14 盤後 phase / 同輪 Telegram message list phase 一致性修復

## 任務狀態

- task_id：v20.0.14-phase-drift-message-list-consistency
- 任務類型：Telegram 報文一致性 bugfix
- 狀態：ready_for_tech
- 版本契約：本輪不升版，沿用目前 v20.0.14
- QA 分級建議：L1，但必須包含直接消費者一致性檢查與手機閱讀順序反證

## Owner 問題

上一輪 v20.0.14 盤後 phase / 行動一致性修復已達 QA conditional pass，但 QA 指出同一輪 formatTelegramMessages() message list 內存在 phase drift 風險：

- formatTelegramMessages() 先讀一次 phase，供持倉 / 未持倉卡使用。
- formatTelegramSummary() 內又自行讀一次 phase。
- 若生成過程剛好跨過盤中 / 盤後邊界，同一批 Telegram messages 可能同時出現：
- 未持倉卡：盤中語意，例如 可買｜10%倉 / 分批
- summary：盤後語意，例如 明日計畫

Owner 要修的是「同一輪 Telegram messages 只使用同一個 report_phase」，不是重開策略或報文大改。

## 使用者可見結果

Owner 手機打開 Telegram 時，同一批連續 messages 的盤中 / 盤後語意必須一致。

手機閱讀路徑：

1. 先看到 summary。
2. 再看今日交易 / 明日計畫 / 執行清單。
3. 再往下看持倉卡、未持倉卡、詳情索引與原因。
4. 全部區塊必須使用同一個 report_phase，不得 summary 是盤後、卡片是盤中，或反過來。

使用者可見行為：

- 同一輪報文中，summary、持倉卡、未持倉卡、execution/checklist/index/reason 類 phase-sensitive 區塊都採用同一個 phase。
- 若本輪決定為盤後，報文維持盤後語意：
- summary 顯示 明日計畫 N
- 今日交易紀錄無新增時不誤導為今日可執行
- 詳情索引不出現 交易執行 N
- 原因不寫 分批執行
- 若本輪決定為盤中，summary 與卡片也一致使用盤中語意，不得中途切成盤後。

## 非目標

- 不改策略 decision。
- 不改 DB schema / DB write payload。
- 不改 watchlist。
- 不改 live Telegram delivery。
- 不改 scheduler / cron。
- 不改行情來源與 market phase 判斷邏輯本身。
- 不重排整體報文架構。
- 不升版，保持 v20.0.14。
- 不處理本輪以外的新文案、分類或策略問題。

## 影響模組

- 主要模組：
- core/generator.py
- 相關測試：
- tests/test_generator_report.py
- tests/test_notifier.py

## 直接消費者

- formatTelegramMessages() 的完整 Telegram message list 產出。
- formatTelegramSummary() 的 summary message。
- 持倉卡 formatter。
- 未持倉卡 formatter。
- execution / checklist / index / reason helpers 中任何依賴 phase 的輸出。
- notifier 發送前取得的 message list contract。

## 輸出契約

- formatTelegramMessages() 在同一輪生成中只能決定一次 report_phase。
- 該 report_phase 必須傳入所有 phase-sensitive formatter / helper。
- formatTelegramSummary() 不得在同一輪 message list 生成中再次自行讀取不同 phase。
- 同一輪 messages 內不可混用盤中與盤後行動語意。
- Telegram message list 的整體結構不因本輪重排；只修正 phase 來源一致性。
- Header / version 字串維持 v20.0.14。
- 穩定盤後 fixture 的既有契約需保持：
- 今日交易紀錄無新增。
- summary 顯示 明日計畫 N。
- 詳情索引不含 交易執行 N。
- reason 不寫 分批執行。

## 驗收條件

1. 新增 phase drift fixture：
- mock get_market_phase 第一次回傳盤中。
- 第二次回傳盤後。
- 執行同一輪 formatTelegramMessages()。
- 驗證整批 messages 使用同一個 phase。
- 不得出現未持倉卡是盤中 可買｜10%倉 / 分批，summary 卻是盤後 明日計畫 的混合語意。
2. 驗證 formatTelegramSummary()：
- 在 formatTelegramMessages() 已決定 report_phase 的路徑中，不得自行重新讀取不同 phase。
- summary phase 必須來自同一輪 message list 的 report_phase。
3. 驗證 phase-sensitive helper 同步：
- position / unheld cards 使用同一個 report_phase。
- summary 使用同一個 report_phase。
- execution / checklist / index / reason helpers 如有 phase 依賴，也必須使用同一個 report_phase。
4. 穩定盤後 fixture 仍通過：
- 今日交易紀錄無新增。
- 明日計畫 N 仍存在。
- 詳情索引不含 交易執行 N。
- 原因不寫 分批執行。
5. 版本驗收：
- 使用者可見 header / version 仍為 v20.0.14。
- 不得升版或回退版本。
6. 測試命令：
- Tech 自檢至少跑：
- pytest tests/test_generator_report.py tests/test_notifier.py
- QA 需重跑：
- pytest tests/test_generator_report.py tests/test_notifier.py
- QA 另需補手機閱讀順序反證，檢查 summary、卡片、索引、原因沒有跨 phase 混合語意。

## 範例或 fixture

### phase drift fixture 形狀

- mock:
- 第一次 get_market_phase() -> intraday
- 第二次 get_market_phase() -> post_market
- 執行：
- formatTelegramMessages(...)
- 期望：
- 同一批 messages 只採用第一次決定的 report_phase，或產品邏輯指定的單一 report_phase。
- 不允許同批 messages 同時包含：

未持倉：
可買｜10%倉 / 分批

以及：

Summary：
明日計畫 3

除非兩者在同一個 phase 語意下被明確定義為可共存；本輪預設不可共存。

### 穩定盤後示例輸出形狀

Summary：
今日交易：無新增
明日計畫 3
新倉：盤後僅列明日追蹤，不提示今日分批執行

詳情索引：
持倉 ...
未持倉 ...

不得出現：

交易執行 3
分批執行
可買｜10%倉 / 分批

## 明確禁止事項

- 禁止改策略判斷。
- 禁止改 DB schema 或 DB 寫入。
- 禁止改 watchlist。
- 禁止 live Telegram delivery。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止改 scheduler / cron。
- 禁止擴大到其他報文重構。
- 禁止升版，必須保持 v20.0.14。
- 禁止用再次呼叫 get_market_phase() 讓 summary 自行決定不同 phase。
- 禁止只修測試不修直接消費者一致性風險。

## 阻塞條件

- 若現有 formatter 架構無法在不改 public contract 的情況下傳入單一 report_phase，Tech 必須 blocked 並說明需要 PM/Architect 重新定義輸出契約。
- 若發現 phase-sensitive helper 範圍超出本 TASK 列出的直接消費者，且會影響策略或 DB，Tech 必須 blocked，不得自行擴大。
- 若測試環境缺 pytest 或必要依賴，runner 應補環境；補完仍無法執行時，Tech/QA 必須 blocked 並列出實際錯誤。
- 若修復需要升版或改變使用者可見報文結構，Tech 必須 blocked，交回 PM 重新定義版本契約。
