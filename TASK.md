# TASK: v20.4.37 06/04 generate() 手機閱讀一致性修復

## 任務狀態

- task_id: v20_4_37_0604_generate_mobile_consistency
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 升小版本到 v20.4.37
- QA 分級建議: L2
- 本輪判斷: 使用者可見 Telegram 報文 formatter / message-list / generator 修復；不是策略重設或全量清理。

## Owner 問題

Owner 要修復 2026-06-04 盤中真實 generate() 產出的完整 v20.4.36 報文在手機閱讀上的一致性錯誤。

failure specimen 是 Owner 貼出的完整 v20.4.36 generate() 報文，關鍵矛盾如下：

- 首屏寫「未持倉 8」，但只列「僅追蹤 5 / 淘汰 2」，漏掉「不可追高觀察 1」。
- 未持倉漏斗又有「不可追高觀察 1 / 僅追蹤 5 / 淘汰 2」，與首屏不一致。
- 「風控中 2」定義不可追溯，且與「執行動作 3 / 今日已買 3 / 持倉風控 4」造成閱讀混亂。
- 普通 observe 卡片仍逐卡出現「修復中 / 連續觀察1天 / 權重+1」歷史噪音。
- 回測摘要錯把建準、緯創聚合成同一行；既有契約要求「單檔 回測（建準）」不得回退。
- 詳情索引、首屏、漏斗、卡片分類需要一致。

## 使用者可見結果

v20.4.37 報文在手機上應能直接看出：

- 未持倉總數與子分類合計一致。
- 首屏、漏斗、詳情索引、卡片分類對同一檔股票給出同一分類。
- 「不可追高觀察 1」不再只出現在漏斗、卻從首屏消失。
- 持倉摘要不再讓「風控中 / 今日已買 / 執行動作 / 持倉風控」互相像不同口徑。
- 普通 observe 歷史權重噪音不再逐卡刷屏。
- 建準與緯創回測摘要保持單檔，不得聚合成同一行。

手機閱讀示例形狀：

未持倉 8
不可追高觀察 1
僅追蹤 5
淘汰 2

未持倉漏斗
不可追高觀察 1 / 僅追蹤 5 / 淘汰 2

實際文案可沿用現有報文風格，但數字、分類、索引與卡片狀態必須同源一致。

## 非目標

- 不改策略 decision。
- 不改 RR 公式。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不改 DB write path，不做 production DML 或 backfill。
- 不發 live Telegram。
- 不重設整份報文架構。
- 不做全量文案瘦身。
- 不處理本輪 failure specimen 以外的新策略爭議。

## 影響模組與直接消費者

影響模組：

- generate() 報文輸出層。
- official formatTelegramMessages final message-list 層。
- Telegram formatter / message-list 組裝。
- 版本常量與報文 header。
- 對應 replay fixture 與 regression tests。

直接消費者：

- Owner 手機 Telegram 閱讀路徑。
- generate() final message-list。
- official formatTelegramMessages final message-list。
- QA replay / regression 驗收。

## 輸出契約

v20.4.37 final message-list 必須滿足：

- 使用者可見版本顯示 v20.4.37。
- 首屏未持倉總數等於所有未持倉子分類合計。
- 未持倉首屏、漏斗、詳情索引、卡片分類使用同一份分類結果。
- 「不可追高觀察」數量為 1 時，首屏與漏斗都必須可見。
- 「不可追高觀察 1 / 僅追蹤 5 / 淘汰 2」合計必須對齊「未持倉 8」。
- 持倉摘要不得讓同一持倉在同一份報文中出現多個互相衝突主行動。
- 普通 observe 卡片不得輸出「修復中 / 連續觀察1天 / 權重+1」這類歷史權重噪音。
- 回測摘要保持單檔輸出，不得把建準、緯創聚合成同一行。
- 詳情索引的股票順序與分類必須能回溯到首屏與卡片分組。

已存在且不得回退的契約：

- 使用者可見版本必須與實際版本常量同步。
- 「單檔 回測（建準）」契約不得回退。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 無可買時不得使用像推薦的文案。
- 空區塊、0-count、無新增下單占位預設不顯示，除非既有契約明確要求保留。
- Owner 啟動語不得解讀為跳過 Tech / QA。

## 版本契約

- 本輪必須升小版本到 v20.4.37。
- 報文 header、版本常量、測試預期若引用版本，必須同步。
- 不得仍顯示 v20.4.36 或回退到更舊版本。

## 驗收條件

- 必須使用 Owner 完整 v20.4.36 generate() 報文的等價 replay artifact 作 failure specimen。
- 驗收必須打到 actual generate() 或 official formatTelegramMessages final message-list 層。
- 不接受 helper-only 驗收；若只能驗 helper，Tech/QA 結論只能是 partial、conditional pass 或 blocked。
- replay 後 final message-list 必須顯示 v20.4.37。
- replay 後首屏 / 漏斗 / 詳情索引 / 卡片分類必須對齊「未持倉 8 = 不可追高觀察 1 + 僅追蹤 5 + 淘汰 2」。
- replay 後不得再出現普通 observe 卡片的「修復中 / 連續觀察1天 / 權重+1」逐卡歷史噪音。
- replay 後建準、緯創不得被聚合成同一回測行，且「回測（建準）」契約仍存在。
- QA 必須補一個 Tech 未覆蓋的反證路徑，例如手機首屏閱讀順序、final message-list 分類合計、或「不可追高觀察 = 1」不得漏列的負面案例。

## 範例或 Fixture

必要 fixture：

- failure_specimen_2026_06_04_v20_4_36_generate
- 來源: Owner 貼出的完整真實 v20.4.36 generate() 報文，或 Architect 提供的等價 replay payload。
- 層級: 必須能產出 official final message-list。

最小可驗形狀：

首屏:
未持倉 8
不可追高觀察 1
僅追蹤 5
淘汰 2

漏斗:
不可追高觀察 1 / 僅追蹤 5 / 淘汰 2

詳情:
同一檔股票分類不得與首屏或漏斗不同。

## 明確禁止事項

- 禁止改策略 decision。
- 禁止改 RR 公式。
- 禁止改 DB schema 或 DB write path。
- 禁止 production DML、backfill、live Telegram delivery。
- 禁止只用 helper fixture 宣告完成。
- 禁止把本輪擴成全量報文重構。
- 禁止合併不同股票的單檔回測摘要。
- 禁止用「看起來一致」取代 replay evidence。
- 禁止把 Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 直接來」解讀成跳過 Tech / QA。

## 阻塞條件

- 找不到 Owner 完整 v20.4.36 generate() 報文，且無法建立等價 replay artifact。
- 無法打到 actual generate() 或 official formatTelegramMessages final message-list 層。
- 版本來源不明，無法可靠同步 v20.4.37。
- 修復需要改策略 decision、RR、DB schema/write 或 live Telegram。
- replay artifact 無法保留首屏、漏斗、詳情索引、卡片分類與回測摘要的同層輸出。

## 本輪停止條件

完成條件：

- v20.4.37 版本同步完成。
- failure specimen replay 在 final message-list 層通過。
- 首屏 / 漏斗 / 詳情索引 / 卡片分類一致性通過。
- 普通 observe 歷史噪音移除通過。
- 單檔回測契約未回退通過。
- QA 完成 L2 反證並輸出 QA_REPORT.md。
- Architect 後續完成 commit / push / git completion gate。

不納入本輪，只記待辦：

- 新策略分數或買賣建議爭議。
- RR 公式調整。
- DB 持久化或跨日狀態補強。
- 報文全量文案瘦身。
- production runner / live Telegram delivery 驗證。
