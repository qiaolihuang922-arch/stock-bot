# TASK: Telegram Report Clarity And Query Performance

## 任務狀態

- task_id：telegram-report-clarity-performance
- 任務類型：formatter / performance patch / Telegram 手機閱讀修正
- 狀態：done
- 版本建議：v20.0.6
- QA 分級建議：L2
- Owner 任務來源：修復 v20.0.5 Telegram 報文與查詢耗時回歸
- 優先級：高，因為影響每日 Telegram 可讀性與執行等待時間

## Owner 問題

Owner 在 v20.0.5 報文中看到三個實際問題：

1. 查詢資料耗時變長：原本約 1.9s，現在又變慢，疑似查詢路徑或重複查詢造成效能回歸。
2. 旺宏 作為淘汰標的，在明細、索引、summary 中反覆出現，造成手機閱讀噪音；Owner 需要能追溯淘汰原因，但不需要在每個高層區塊重複看
到同一檔淘汰標的。
3. 明日執行清單 下方出現 今日可執行：持倉 5，時間語意衝突。Owner 打開手機時會不知道這是今天盤中行動、盤後檢視，還是明日盤前準備。

本輪目標是修復可讀性與查詢效能，不改變任何策略判斷。

## 使用者可見結果

Owner 手機打開 Telegram 後應看到：

1. Summary 先給明確盤後 / 明日語境，不再出現 明日執行清單 搭配 今日可執行 的矛盾文案。
2. 淘汰標的如 旺宏 不再於 summary、索引、明細高頻重複曝光；高層只保留淘汰數量或最多一個可追溯入口。
3. 詳情仍能追到 旺宏 的淘汰狀態與原因，避免為了降噪而失去可查性。
4. 報文生成或查詢階段耗時回到接近 v20.0.5 前的水準；若本地測試使用 mock / fixture，需證明重複查詢已消除或明顯下降。

手機閱讀路徑：

1. 第一眼：Summary 決策區，回答持倉先看什麼、新倉能不能買、哪些只是追蹤、哪些不可行動。
2. 第二眼：明日 / 盤後執行清單，只使用同一時間語境。
3. 第三眼：詳情索引，快速看到可買、準備、追蹤、不可行動與淘汰數量。
4. 第四眼：需要追溯時才進入未持倉明細中的淘汰分組。

## 非目標

- 不改策略 decision、分數、買賣判斷、淘汰判定邏輯。
- 不改 DB schema、DB payload、Supabase 寫入格式。
- 不改 core/watchlist.py 或 12 檔股票清單。
- 不新增 live Telegram delivery。
- 不執行 live Supabase write。
- 不做正式 replay / backfill write。
- 不把淘汰標的完全隱藏；本輪只降低重複曝光，仍保留追溯入口。

## 影響模組

預期直接影響：

- core/generator.py：Telegram 報文 summary、明日執行清單、詳情索引、未持倉明細分組與重複曝光控制。
- services/strategy_evidence.py 或相關查詢 helper：若耗時來源在 evidence summary / DB 查詢路徑，需優化重複查詢、排序或資料共用。
- services/stock_api.py 或行情讀取路徑：若耗時來源是行情 / history 重複查詢，需避免同一 run 內重複讀取。
- formatter / notifier 相關測試：需補手機長報文 fixture、淘汰降噪、時間語意與查詢次數測試。

不得影響：

- services/analysis.py 的策略 decision 語意。
- services/signal_store.py、services/daily_snapshot_store.py 的 DB payload。
- core/watchlist.py。
- live Telegram / live Supabase 外部副作用。

## 直接消費者

- Owner 手機 Telegram 報文。
- services/notifier.py 或 Telegram 發送入口，消費 formatter 產生的 message list / text。
- main.py / GitHub Actions 每日報文流程，消費報文生成結果與查詢耗時。
- formatter snapshot / contract tests，消費 summary、明日執行清單、索引、詳情文字。
- evidence / stock data query helpers 的呼叫方，消費同一 run 內的查詢結果。

## 輸出契約

### Telegram 報文契約

- 報文版本建議升至 v20.0.6。
- 明日執行清單 區塊內不得再出現 今日可執行。
- 若要表達持倉檢視，使用盤後 / 明日語境，例如：
- 盤後持倉檢視：5 檔
- 明日先看持倉：5 檔
- 明日盤前準備：N 檔
- 可買、準備、僅追蹤、不可行動 必須維持分開，不得混在同一行。
- 淘汰標的高層曝光規則：
- Summary 可顯示淘汰數量，但不應逐檔重複列淘汰標的。
- 詳情索引可保留 淘汰 N 或最多一個追溯入口。
- 未持倉明細的 淘汰 分組保留完整追溯。
- 同一淘汰標的不得同時在 summary、明日執行清單、索引、明細中以行動候選語氣重複出現。
- 旺宏 若為淘汰標的，不能出現在 可買、準備、僅追蹤 的行動清單中。

### 查詢效能契約

- 同一報文生成 run 內，對同一資料來源、同一股票、同一日期區間的查詢不得無理由重複執行。
- Tech 可用快取、資料預取、結果傳遞、批次查詢或移除 formatter 內重複呼叫達成，但不得改變輸出資料語意。
- 若查詢耗時 log 已存在，需保留或補足可觀測結果，讓 QA 能比較優化前後耗時或查詢次數。
- 若本地無法穩定量測真實秒數，至少需用 fake / mock query provider 驗證查詢呼叫次數下降，並用本地 fixture 報告生成時間不得明顯回
歸。

## 驗收條件

- 報文版本顯示為 v20.0.6 或 Tech 在 CHANGELOG.md 說明不升版原因。
- 手機長報文 fixture 中，明日執行清單 下方不再出現 今日可執行。
- 手機長報文 fixture 中，持倉 5 檔的描述改為盤後 / 明日語境，且 Owner 不會誤讀成今天盤中可立即操作。
- 旺宏 作為淘汰標的時：
- 不出現在 summary 的推薦 / 追蹤主句中。
- 不出現在明日執行清單的行動項中。
- 可在詳情索引或淘汰明細中追溯。
- 全報文中高層重複曝光明顯降低；QA 需用同一 fixture 計算或列舉出現位置。
- 淘汰數量仍可追溯到明細，不得因降噪造成 summary / 索引 / 明細數量矛盾。
- 查詢效能驗收至少滿足其一：
- 本地可量測情境下，查詢資料耗時回到約 1.9s 附近，允收上限建議 <= 2.2s。
- 若環境波動無法用秒數判定，需用測試證明同一 run 內重複查詢次數下降，且長報文 formatter 測試未變慢。
- L2 QA 需覆蓋：
- formatter 長報文 snapshot / contract。
- 淘汰標的降噪與追溯。
- 明日 / 盤後時間語意一致性。
- 策略 decision 不變性。
- 查詢次數或耗時優化證據。
- 直接消費者 message list / notifier contract。

## 範例或 fixture

### 輸入 fixture 形狀

- 持倉：5 檔。
- 未持倉：
- 可買：0 檔。
- 準備：1 檔。
- 冷卻：2 檔。
- 回測：1 檔。
- RR：1 檔。
- 量能：1 檔。
- 淘汰：旺宏 1 檔。
- 旺宏 狀態：淘汰，不可買，不可列入明日行動候選。

### 期望 Telegram 輸出形狀

📌 v20.0.6 盤後摘要

持倉：5 檔先檢視
新倉：無有效進場
準備：1 檔
僅追蹤：冷卻 2／回測 1／RR 1／量能 1
不可行動：淘汰 1

🗓 明日執行清單

盤後持倉檢視：5 檔
明日盤前準備：1 檔
僅追蹤：冷卻 2／回測 1／RR 1／量能 1
不可行動：淘汰 1，見詳情

📇 詳情索引

準備 1
冷卻 2
回測 1
RR 1
量能 1
淘汰 1

【淘汰 1｜不可行動】
旺宏｜淘汰｜原因：<保留既有原因文字>

### 不可接受輸出

明日執行清單
今日可執行：持倉 5

追蹤最強：旺宏｜淘汰｜不可買
...
索引：旺宏 淘汰
...
summary：旺宏 淘汰
...
【淘汰】
旺宏｜淘汰

以上第二段不可接受的原因是 旺宏 作為淘汰標的被重複放大，且出現在高層追蹤語氣中，造成手機閱讀噪音。

## 明確禁止事項

- 禁止修改策略 decision、評分、買賣分類、淘汰判定條件。
- 禁止修改 DB payload、Supabase schema、資料表欄位或正式寫入流程。
- 禁止修改 core/watchlist.py。
- 禁止 live Telegram delivery。
- 禁止 live Supabase write。
- 禁止正式 backfill / replay write。
- 禁止為了效能移除必要風控、持倉、淘汰原因或 evidence fallback。
- 禁止把 淘汰 混入 可買、準備、僅追蹤。
- 禁止只用單一短 fixture 驗證；報文任務必須用接近真實手機長報文檢查。
- 禁止 Tech 自行擴大為架構重寫或資料模型改版。

## 阻塞條件

若遇到以下情況，Tech 或 QA 必須標記 blocked，不得自行決策：

- 無法重現或定位查詢耗時來源，且沒有任何查詢次數 / 耗時 evidence。
- 現有報文資料結構無法區分 淘汰 與其他不可行動狀態。
- 降低淘汰曝光會導致淘汰數量無法追溯到明細。
- 修正時間語意需要 Owner 決定到底採用 盤後持倉檢視 或 明日先看持倉，而現有上下文不足以選擇。
- 測試環境缺 .venv、pytest 或必要依賴且 runner 補環境後仍不可執行。
- 任何修法必須改策略 decision、DB payload、watchlist、live Telegram 或 live Supabase 才能完成。
