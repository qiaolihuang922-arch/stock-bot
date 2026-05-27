# TASK: Telegram 報文持倉行動一致性與噪音收斂

## 任務狀態

- task_id: telegram_action_consistency_noise_budget_20260527
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 本輪不升版，沿用目前 core/generator.py 的 VERSION；Tech 必須確認 Telegram header 實際輸出仍與 VERSION 一致。
- QA 分級建議: L2
- QA 升級原因: 涉及 Telegram 使用者可見報文、持倉買賣/加減碼語意、message list 閱讀順序與直接消費者契約。

## Owner 問題

Owner 要修復 Telegram 報文的三個產品問題：

1. 小 bug 修復流程不得膨脹；本輪實作與驗證必須按 risk_patch 的必要範圍收斂，不可擴成 full project 重構或全量驗證。
2. 同一持倉標的在同一份報文中不得出現互斥行動，例如同時加碼、減碼、賣出、續抱；尤其 今日買入 後不能又像建議加碼，或無條件叫賣。
3. 降低報文重複噪音；summary、索引、詳情各自分工，避免不可買、淘汰、僅追蹤標的在高層反覆點名或重複長句。

## 使用者可見結果

Owner 在手機打開 Telegram 後應先看到：

1. Header 版本字串與目前 VERSION 一致。
2. Summary 直接回答：
- 今天能不能買。
- 持倉先處理什麼。
- 未持倉哪些只是追蹤。
- 哪些不可行動。
3. 每個持倉標的只會看到一個主行動。
4. 今日買入 標的不再被包裝成可加碼；預設顯示為 新倉風控觀察。
5. 若高分標的同時有風控條件，summary 與詳情都以風控為優先，不得重新包裝成買入或加碼。
6. 不可買、淘汰、僅追蹤標的不在 summary、索引、詳情重複點名；高層只保留決策必要資訊。

## 非目標

- 不改策略核心分數、選股條件、買賣判斷來源。
- 不改 DB schema、Supabase payload、Telegram live delivery 流程。
- 不新增股票清單，不改 watchlist。
- 不做 replay/backfill 正式寫入。
- 不重構整個 formatter 架構。
- 不擴大到非 Telegram 報文的產品 redesign。
- 不做 full pytest，除非 QA 發現直接契約風險並明確說明升級原因與停止條件。

## 影響模組

- 主要影響:
- core/generator.py: Telegram 報文 formatter、summary、持倉卡、索引、詳情輸出。
- 相關測試:
- Telegram formatter / snapshot / message list 相關測試。
- 持倉行動一致性與長報文 fixture 測試。
- 不應影響:
- services/analysis.py
- core/condition_engine.py
- services/stock_api.py
- services/signal_store.py
- services/daily_snapshot_store.py
- services/position_store.py
- core/watchlist.py
- replay/backfill scripts
- Supabase edge functions

## 直接消費者

- Telegram message list 產出流程。
- Owner 手機 Telegram 閱讀體驗。
- 既有 formatter snapshot tests。
- 任何直接呼叫 Telegram formatter 並依賴 message order、summary、持倉卡、索引、詳情文字的測試或 helper。

## 輸出契約

### Message List 閱讀順序

Telegram 報文應維持手機優先閱讀路徑：

1. Header / 版本 / 日期。
2. Summary 決策區。
3. 持倉行動區。
4. 未持倉執行或追蹤摘要。
5. 索引 / 漏斗數量。
6. 詳情。

### 持倉主行動契約

同一標的在同一份報文中只能有一個主行動：

- 停損
- 停利
- 減碼
- 新倉風控觀察
- 續抱
- 觀察
- 加碼
- 不動作

行動優先級由高到低：

1. 明確停損 / 停利 / 賣出觸發。
2. 明確減碼觸發。
3. 今日買入。
4. 風控警戒。
5. 續抱。
6. 加碼。
7. 觀察 / 不動作。

規則：

- 今日買入 標的主行動預設為 新倉風控觀察。
- 今日買入 標的不得出現 可加碼、加碼候選、明日加碼 或等價買入強化文案。
- 今日買入 後若訊號轉弱，可顯示 新倉風控觀察 或 停損警戒。
- 若要顯示 停損、賣出、減碼，同一行必須包含明確觸發條件，例如 跌破停損價、跌破警戒線、策略失效。
- 高分但觸發風控的標的，風控優先；summary 必須寫成 不加碼，先風控 或等價語意。
- Summary、持倉卡、明日清單、詳情不得對同一標的輸出互斥行動。

### 噪音預算契約

- Summary 只放決策，不放完整追溯。
- 索引只放分類與數量，不重複長理由。
- 詳情負責追溯分數、條件與原因。
- 同一未持倉股票若不可買，summary / 執行清單 / 索引三者合計最多點名一次。
- 淘汰股高層只顯示數量，不點名，除非詳情區需要追溯。
- 未持倉追蹤清單超過 3 檔時，summary 只列 1-3 檔或只列分類數量，剩餘用 另 N 檔見詳情。
- 不可把不同狀態混成同一個 另 N 檔。
- 不得跨 summary、索引、詳情複製同一長句。
- 可買、準備、僅追蹤、不可行動 必須分開呈現。

## 驗收條件

1. 同一持倉標的在完整 Telegram 報文中只出現一個主行動。
2. 今日買入 標的不會出現加碼語意；若轉弱，只能是風控觀察或帶觸發條件的停損/減碼。
3. 高分但風控優先的標的，在 summary、持倉卡、詳情中都不得被包裝成可買或可加碼。
4. 不可買、淘汰、僅追蹤標的不在高層重複點名；summary、索引、詳情分工清楚。
5. 長報文 fixture 在手機閱讀順序下，Owner 不需要從多段重複文字中尋找真正行動。
6. 報文 header 實際輸出的版本字串與目前 VERSION 一致。
7. Tech 只修改 formatter 與直接相關測試；不得改策略、DB、watchlist、live delivery、replay/backfill。
8. Tech 自檢限於直接 formatter / snapshot / consumer smoke。
9. QA 必須額外驗證：
- 剛買入後轉弱。
- 高分但風控優先。
- 不可買 / 淘汰重複曝光。
- 長報文手機閱讀路徑。
10. QA 不得只重跑 Tech 自檢；必須補使用者誤讀與跨區塊語意一致性檢查。

## 範例或 fixture

### Fixture A: 剛買入後轉弱

輸入情境：

- 2330 今日已買入。
- 盤後分數仍高，但短線轉弱。
- 尚未跌破停損價。

期望輸出形狀：

[Header]
Stock Bot v目前VERSION｜2026-05-27

[Summary]
今天新倉：無追加買點。
持倉先處理：2330 新倉風控觀察。
未持倉：僅追蹤，無有效進場。
不可行動：淘汰 4 檔見詳情。

[持倉]
2330 台積電｜主行動：新倉風控觀察
原因：今日已買入，短線轉弱但未跌破停損。
下一步：不加碼；跌破 000.0 才啟動停損檢查。

[索引]
持倉：新倉風控觀察 1
未持倉：僅追蹤 2｜不可行動 4

[詳情]
2330｜分數 86｜狀態：新倉風控觀察｜觸發：今日買入 + 短線轉弱

不得出現：

2330 可加碼
2330 明日加碼
2330 賣出
2330 減碼

除非同一行明確寫出已跌破停損或減碼觸發條件。

### Fixture B: 高分但風控優先

輸入情境：

- 2317 分數最高。
- 同時觸發風控警戒。
- 非今日買入。

期望輸出形狀：

[Summary]
今天可買：無。
持倉先處理：2317 不加碼，先風控。
追蹤最強：2454、2308；不可買。

[持倉]
2317 鴻海｜主行動：觀察
原因：分數高但觸發風控警戒。
下一步：不加碼；收復 00.0 後再評估。

[詳情]
2317｜分數 91｜狀態：風控優先｜不可加碼

不得在其他區塊重新寫成：

2317 最強可買
2317 加碼候選
2317 明日優先買

### Fixture C: 不可買 / 淘汰噪音收斂

輸入情境：

- 未持倉 8 檔。
- 可買 0。
- 準備 1。
- 僅追蹤 3。
- 淘汰 4。

期望輸出形狀：

[Summary]
今天可買：無。
準備：1101，等回測。
僅追蹤：3 檔見詳情。
不可行動：淘汰 4 檔。

[未持倉索引]
準備 1｜僅追蹤 3｜淘汰 4

[詳情]
1101｜等回測｜不可買
2454｜僅追蹤｜等量能
2308｜僅追蹤｜等冷卻
...
淘汰：4 檔

不得出現：

Summary 點名 4 檔淘汰股
索引再次點名同一批淘汰股
詳情第三次重複同一長理由
不可買候選寫成追蹤最強且未標示不可買

### Fixture D: 長報文手機閱讀路徑

QA 應使用接近真實長報文 fixture，至少包含：

- 持倉 2 檔。
- 今日買入 1 檔。
- 高分風控 1 檔。
- 未持倉 8 檔以上。
- 淘汰至少 4 檔。
- Summary、持倉、索引、詳情皆有內容。

手機閱讀驗收：

- 第一屏能看懂今天沒有追加買點或有哪些可買。
- 第一屏能看懂持倉先處理哪一檔。
- 不需要滑到詳情才能知道 今日買入 不可加碼。
- 不可買 / 淘汰不在高層重複點名造成誤讀。

## 明確禁止事項

- 禁止 live Telegram delivery。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止改 DB schema。
- 禁止改策略核心分數與買賣判斷來源。
- 禁止改 watchlist。
- 禁止新增或移除股票清單。
- 禁止大範圍重構 formatter。
- 禁止 full pytest / replay / backfill dry-run 作為預設驗證。
- 禁止把 等冷卻、等回測、等RR修復、等量能、淘汰 混入錯誤分組。
- 禁止讓同一標的在 summary、持倉卡、明日清單、詳情出現互斥行動。
- 禁止為了數字可追溯而犧牲手機 summary 的決策清楚度。

## 阻塞條件

若 Tech 發現以下情況，必須 blocked，不得自行補產品決策：

- 目前 formatter 無法判斷 今日買入 狀態來源。
- 目前資料結構無法區分持倉主行動與輔助提示。
- 同一標的行動來源在上游已互相矛盾，formatter 無法只靠呈現層修正。
- 需要改策略 decision、DB payload、position store 或 watchlist 才能完成。
- 現有測試無法建立接近真實長報文 fixture，且缺少可替代的直接 consumer smoke。
- 版本 header 來源不明，無法核對實際 Telegram 輸出與 VERSION。
