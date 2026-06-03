# TASK: Telegram 簡報/卡片降噪與一致性修復

## 任務狀態

- task_id：telegram_message_noise_consistency_20260603
- 任務類型：normal_patch
- 狀態：done
- 版本建議：使用者可見 Telegram 報文有文案與顯示契約變更，需同步檢查/更新報文版本字串；不得回退既有版本。
- QA 分級建議：L2

## Owner 問題

Telegram 簡報與未持倉/持倉卡片目前存在重複、計數不一致、不可行動標的仍露 RR、部分回測/證據文案時有時無等問題，造成手機首屏誤讀與噪音。Owner 要一次修復 9 個已點名的報文顯示問題，但不得改策略 decision、RR 公式、DB
schema/write 或 live Telegram。

## 使用者可見結果

手機閱讀 Telegram 報文時：

- 首屏「市場」行只出現一次市場狀態與 R 值，並同時列出交易執行、持倉風控、未持倉總數與拆分。
- 簡報刪除已由其他區塊表達的冗餘行。
- 交易執行只顯示短動作摘要，不重複風控檢查完整句。
- 僅追蹤區塊不逐行重複「修復中｜連續觀察 1 天」等歷史 token。
- 淘汰或結構弱的不可行動卡片 RR 顯示 -（不可行動）。
- 未持倉回測顯示口徑一致；樣本不足/不可用不逐卡製造噪音。
- partial 且 modifier=1.0 時，證據段顯示 僅輔助參考，不顯示 +0%。

## 非目標

- 不改策略 decision、買賣/加減碼判斷、停損停利邏輯。
- 不改 RR 計算公式，只改不可行動時的顯示。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不新增 production write/backfill，不做 live Telegram delivery。
- 不重設整份 Telegram 報文架構，不引入新策略分類。
- 不處理本輪 9 點以外的文案偏好或排序需求；旁支問題記待辦。

## 影響模組與直接消費者

- 影響模組：
- Telegram 報文 generator/rendering path。
- 簡報首屏 summary/market line formatter。
- 交易執行區塊 formatter。
- 未持倉僅追蹤/淘汰卡片 formatter。
- cross_day_detail_line 附近歷史行 formatter。
- 回測/證據顯示 formatter。
- rendered-message probe / snapshot 類測試。
- 直接消費者：
- Owner 手機閱讀 Telegram 簡報。
- Telegram rendered message 測試/probe。
- 盤中與盤後共用報文降噪輸出。
- QA 驗收腳本與人工手機閱讀路徑。

## 輸出契約

- 首屏市場行目標形狀：
- 市場：進攻偏熱 R3｜交易執行 1｜持倉風控 4｜未持倉 8（僅追蹤7/淘汰1）
- 首屏市場行不得同時出現：
- 進攻偏熱｜R3
- R3 進攻偏熱
- 同一市場狀態/R 值只能保留一次。
- 簡報中刪除下列獨立冗餘行：
- 新倉：目前沒有可行動候選
- 背景：...
- 📌 持倉：...
- 未持倉 7 檔只等觸發...
- 交易執行區塊：
- 使用短文案，例如 旺宏 減碼（續降優先級）
- 不得重複風控檢查中的完整句。
- 僅追蹤區塊：
- 不逐行印出與卡片歷史行重複的 修復中｜連續觀察 1 天。
- 無有效進場時，只列名稱或併入漏斗；不得讓區塊看起來像推薦。
- 歷史行：
- cross_day_detail_line 不得讓 repair_label 與 reason 重複顯示同義 token。
- 修復中、連續失效 等狀態 token 同一卡片同一行只出現一次。
- 未持倉計數：
- 簡報結論行用總數口徑，例如 未持倉 8（僅追蹤7/淘汰1）。
- 必須與漏斗總數一致，不得只寫 7 檔僅追蹤 而漏掉淘汰。
- RR 顯示：
- 若卡片 decision/分類為淘汰，或結構弱且不可行動，RR 顯示 -（不可行動）。
- 不得露出具體 RR 數值，例如光寶科不可再顯示 RR 3.06。
- 回測行：
- 未持倉回測行要全顯示或全不顯示，不得部分卡片缺失造成誤讀。
- 樣本不足/不可用 不逐卡印；可用時歸一處或精簡顯示。
- 盤中與盤後必須套用同一降噪函式。
- partial 證據：
- partial 且 modifier=1.0 時，證據段顯示 僅輔助參考。
- 不顯示 +0%。
- 依賴 M1 version 過濾修復，讓 strategy_sample 穩定，不得時有時無。

## 版本契約

- 已存在且不得回退的契約：
- Telegram 報文仍維持既有盤中/盤後入口與 message list 輸出方式。
- 既有策略 decision、RR raw value、DB payload 不因本任務改變。
- 持倉與未持倉分組仍需可被直接閱讀，不得合併到無法判斷行動狀態。
- 無可買時不得使用像推薦的文案。
- 使用者可見報文版本字串不得回退；若現有版本契約不明，Tech 必須先 blocked 並請 Architect 補充。

## 驗收條件

- Tech 必須先補 rendered-message probe，覆蓋本任務 9 點，才能改 formatter。
- 盤中與盤後 fixture 均通過同一降噪函式，不得維護兩套漂移邏輯。
- 手機閱讀首屏驗收：
- 市場行符合目標形狀。
- 首屏不再出現被刪除的四類冗餘行。
- 未持倉總數與漏斗一致。
- 交易執行驗收：
- 交易執行只出現短摘要。
- 風控檢查可保留完整說明，但同一句不得在交易執行重複。
- 僅追蹤/歷史行驗收：
- 僅追蹤區塊不逐行重複 修復中｜連續觀察 1 天。
- 歷史行中 修復中、連續失效 不重複。
- RR 驗收：
- 淘汰或結構弱不可行動卡片 RR 顯示 -（不可行動）。
- fixture 中光寶科不得出現 RR 3.06。
- 回測/證據驗收：
- 未持倉回測行顯示口徑一致。
- 樣本不足/不可用不逐卡印。
- partial + modifier=1.0 顯示 僅輔助參考，不得顯示 +0%。
- strategy_sample 在 M1 version 過濾後穩定出現或穩定不出現，不得同 fixture 多次 render 時有時無。
- QA 必須至少補一個 Tech 未覆蓋的直接消費者或負面案例，並檢查：
- 手機閱讀路徑。
- 首屏計數。
- 交易執行去重。
- RR 隱藏。
- 證據 +0% 文案。

## 範例或 Fixture

- 首屏示例：

市場：進攻偏熱 R3｜交易執行 1｜持倉風控 4｜未持倉 8（僅追蹤7/淘汰1）

- 交易執行示例：

交易執行
旺宏 減碼（續降優先級）

- 不可行動 RR 示例：

光寶科｜淘汰
RR：-（不可行動）

- partial 證據示例：

證據：partial｜僅輔助參考

- rendered-message probe 至少包含：
- 盤後報文 fixture。
- 盤中報文 fixture。
- 淘汰/結構弱且原始 RR 有數值的 fixture。
- partial + modifier=1.0 fixture。
- M1 version 過濾後 strategy_sample 穩定性的 fixture。

## 明確禁止事項

- 禁止改 strategy decision。
- 禁止改 RR 公式或 raw RR 計算。
- 禁止改 DB schema/write path。
- 禁止 production write/backfill。
- 禁止 live Telegram delivery。
- 禁止只改盤後、不改盤中，或盤中/盤後各自做不同降噪邏輯。
- 禁止用刪除整個未持倉/持倉卡片來規避重複問題。
- 禁止把 +0% 換成其他數字文案；本條目標是 僅輔助參考。
- 禁止把「無可買」寫成推薦語氣。

## 阻塞條件

- 若找不到盤中與盤後共用 formatter 或無法建立共用降噪函式，Tech 必須 blocked。
- 若 rendered-message probe 無法穩定重現 Owner 9 點中的任一點，Tech 必須標明缺哪個 fixture，不得宣告完成。
- 若現有報文版本字串/版本契約無法定位，Tech 必須 blocked 請 Architect 補充。
- 若修復需要改 DB schema/write、策略 decision 或 RR 公式，必須 blocked，不能在本任務內擴權。
- 若 QA 無法執行手機閱讀路徑或 rendered-message 驗收，QA 結論不得為通過。

## 本輪停止條件

- 完成條件：9 點均有 rendered-message probe 覆蓋，盤中/盤後共用降噪函式，Tech 自檢通過，QA L2 驗收通過且確認手機閱讀首屏無誤讀。
- 不納入本輪：策略排序優化、新增推薦邏輯、DB 持久化補丁、live delivery、全量 Telegram 重構、未被 9 點點名的文案偏好。
- 若發現旁支問題但不阻塞上述驗收，只記入後續待辦，不擴大本輪任務。
