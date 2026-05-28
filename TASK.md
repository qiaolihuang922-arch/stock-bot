# TASK: v20.0.12 市場方向與執行態度語意拆分

## 任務狀態

- task_id: telegram_semantics_market_direction_vs_execution_v20_0_12
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 本輪修改使用者可見 Telegram 報文，必須升版到 v20.0.12，並同步 formatter header / VERSION / 相關測試期望。
- QA 分級建議: L1+
- 以 Telegram formatter / snapshot / 直接消費者 smoke 為主。
- 因涉及 summary、持倉語意、未持倉分類語意，QA 必須補手機閱讀順序與跨區塊語意一致性檢查。
- 不需要 full pytest、replay、正式 backfill、live delivery。

## Owner 問題

05/28 盤中 v20.0.11 報文在市場 / AI 主線偏多、但策略尚未給出新增買點時，容易讓 Owner 把兩件事混在一起：

- 「市場方向 / 產業題材仍偏多」。
- 「當前交易執行上不能追高，新增倉位要等回測或觸發」。

本輪要優化 Telegram 報文語意，讓 Owner 手機打開後能立刻理解：主線仍在，不代表現在可買；等回測 / 淘汰是技術觸發狀態，不是看空 AI 或電子供應鏈產業。

## 使用者可見結果

Owner 在 Telegram 報文中會看到更清楚的短句：

- Summary 明確拆開「主線偏多」與「執行等待」。
- 持倉 AI / 電子供應鏈標的表達為「主線持倉保留 / 先按風控續抱」，不暗示可加碼。
- 未持倉等回測 / 淘汰標的表達為「產業方向不等於當前可買」，原因是技術觸發未成立、已失效或不符合策略門檻。
- Header / 版本字串顯示 v20.0.12。

## 非目標

- 不改交易決策。
- 不改策略核心、分數、門檻、排序、買賣條件。
- 不改 DB schema、DB write payload、Telegram payload shape。
- 不改 watchlist。
- 不新增外部即時新聞依賴。
- 不新增 market regime 判斷資料源。
- 不做 live Telegram delivery。
- 不做 live Supabase write。
- 不做正式 backfill。
- 不重構 formatter 架構。
- 不把「AI 主線偏多」轉成任何自動買入或加碼訊號。

## 影響模組

- 直接模組:
- core/generator.py 或等價 Telegram 報文 formatter。
- formatter 相關 snapshot / unit tests。
- 可能同步檢查:
- 產生 Telegram message list 的直接入口。
- 報文 header 版本常量，例如 VERSION。
- 不應影響:
- services/analysis.py 策略判斷。
- core/condition_engine.py 條件映射。
- services/stock_api.py 行情來源。
- DB 寫入流程。
- watchlist。
- replay / backfill 寫庫流程。

## 直接消費者

- Owner 手機上的 Telegram 盤中報文。
- Telegram message list 產生器的直接呼叫方。
- formatter snapshot / regression tests。
- 任何依賴 formatter header 版本字串的測試或驗收腳本。

## 輸出契約

### Header / 版本

- Telegram 報文 header 必須顯示 v20.0.12。
- 不得只更新文件版本而漏改實際 formatter 輸出版本。

### Summary 語意

Summary 必須在 Owner 手機閱讀最前段，用短句拆清楚：

- 市場 / AI 主線仍偏多或題材仍在。
- 新增買點未成立。
- 執行態度是等回測 / 等觸發 / 不追高。
- 不得把「主線偏多」寫成「今日可買」。
- 不得把「無新增下單」寫成「看空產業」。

### 持倉語意

對 AI / 電子供應鏈相關持倉：

- 可表達「主線持倉保留」「既有倉位按風控續抱」。
- 新增倉位必須表達為「等觸發」或「等回測」。
- 不得出現「可加碼」「追主線」「補倉」等會讓 Owner 誤讀為加碼的暗示，除非既有策略已明確產生加碼決策。
- 同一檔持倉在 summary、持倉卡、執行清單、詳情中的主行動必須一致。

### 未持倉等回測 / 淘汰語意

對未持倉標的：

- 等回測 應表達為：題材或方向仍可追蹤，但策略買點尚未成立。
- 淘汰 應表達為：本輪技術觸發失效、條件未達或風險報酬不合格，不代表看空產業。
- 不得把淘汰股描述成產業基本面看空。
- 不得讓等回測或淘汰標的在 summary 中像推薦買入。

### 分組與 payload

- 不改 message list contract。
- 不改 Telegram payload shape。
- 不改股票分類結果，只改使用者可見文案。
- 分組標題與卡片狀態必須一致：
- 等回測 卡片仍在 等回測 分組。
- 淘汰 卡片仍在 淘汰 分組。
- 不得為了文案優化改動分類歸屬。

## 手機閱讀路徑

QA 必須按 Owner 手機打開 Telegram 後的閱讀順序檢查：

1. 先看 header，確認版本為 v20.0.12。
2. 先讀 summary 最後決策區，確認第一眼能看懂：
- 主線仍偏多。
- 但新增買點未成立。
- 今日不追高 / 先等回測。
3. 再看持倉區，確認 AI / 電子供應鏈持倉是「保留 / 續抱 / 風控」，不是加碼暗示。
4. 再看未持倉區，確認等回測 / 淘汰只是技術狀態，不是產業看空。
5. 最後看詳情，確認 summary、索引、卡片、詳情的分類名稱與行動語意一致。

## 驗收條件

- Header 實際輸出包含 v20.0.12。
- Summary 有短句明確拆分「主線偏多」與「買點未成立 / 不追高 / 等回測」。
- 無新增下單時，summary 不得出現像推薦買入的文案。
- AI / 電子供應鏈持倉不出現未經策略決策支持的加碼暗示。
- 未持倉 等回測 標的不被描述成可立即買入。
- 未持倉 淘汰 標的不被描述成產業看空，只能是本輪策略 / 技術條件未通過。
- 不改任何策略 decision、分類結果、DB payload、Telegram payload shape。
- formatter 直接測試或 snapshot 必須覆蓋：
- 市場 / AI 主線偏多但無新增買點。
- 既有 AI / 電子供應鏈持倉保留但不加碼。
- 未持倉等回測。
- 未持倉淘汰。
- QA 必須補一個 Tech 未覆蓋的手機誤讀檢查：確認 Owner 不會把「主線偏多」誤讀成「今天可買」，也不會把「淘汰」誤讀成「看空產業」。

## 範例或 fixture

### 範例輸出形狀

[盤中掃描 v20.0.12]

今日結論
主線：AI / 電子供應鏈仍偏多。
執行：新增買點未成立，先等回測，不追高。
新倉：無有效進場。

持倉
- 2330 台積電：主線持倉保留，按既有風控續抱；新增倉位等觸發。
- 2308 台達電：電子供應鏈仍在主線內，先持有觀察；不追價加碼。

未持倉追蹤
等回測
- 3661 世芯-KY：題材仍可追蹤，但買點未成立；等回測確認。

淘汰
- 0000 範例股：本輪技術觸發失效，暫不行動；不代表看空產業。

### 負面示例，不可出現

AI 主線偏多，今天可進場追。

2330 主線強，可加碼。

淘汰：AI 產業轉空。

等回測：最強候選，立即關注買入。

## 明確禁止事項

- 禁止修改策略核心、交易門檻、分數、排序、決策邏輯。
- 禁止修改 DB schema、DB write payload、Telegram payload shape。
- 禁止修改 watchlist。
- 禁止新增外部即時新聞依賴。
- 禁止 live Telegram delivery。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止把市場方向偏多轉成買入、加碼或補倉訊號。
- 禁止把淘汰 / 等回測文案寫成產業基本面看空。
- 禁止刪除固定 8 份 Markdown。
- 禁止順手重構無關 formatter 或策略模組。

## 阻塞條件

Tech 必須 blocked 的情況：

- 無法定位實際 Telegram formatter header 版本常量。
- 現有 formatter 無法只改文案而不碰策略 decision。
- 需要改 message list contract 或 payload shape 才能完成文案。
- TASK.md 範圍外需要新增市場資料源或即時新聞依賴。
- 測試環境無法執行最小 formatter / snapshot 測試，且 runner 無法補齊依賴。

QA 必須 blocked 或 conditional pass 的情況：

- 實際 Telegram 輸出版本不是 v20.0.12。
- Summary 仍可能讓 Owner 把主線偏多誤讀成今日可買。
- 持倉區仍出現無策略支持的加碼暗示。
- 淘汰 / 等回測仍可能被誤讀成產業看空。
- Tech 改動超出文案 / formatter 範圍，碰到策略、DB、watchlist 或 payload shape。
- QA 未能取得接近真實長報文 fixture 進行手機閱讀順序檢查。
