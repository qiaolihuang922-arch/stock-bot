# TASK: v20.4.12 Telegram message list delivery order fix

## 任務狀態

- task_id: tg-message-order-v20.4.12
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: v20.4.12
- QA 分級建議: L1
- 主 bug: Telegram 手機收訊順序錯誤，v20.4.11 先送 summary、後送 action body，不符合 Owner 指定閱讀順序。

## Owner 問題

Owner 拒收 v20.4.11 intraday Telegram delivery order。

要求 Telegram message list 的送出順序固定為：

1. 持倉
2. 非持倉
3. 報文短訊 / summary / evidence / strategy / source summary 最後

目前 v20.4.11 是 summary first、action body second，造成手機閱讀時先看到結論摘要，後看到持倉與非持倉主體，順序不符合 Owner 指定。

## 使用者可見結果

Telegram 手機收到多則訊息時，第一則必須先看到持倉處理，第二則看到非持倉候選，最後才看到報文短訊 / summary / evidence / strategy / source summary。

策略判斷、候選排序、持倉行動、文案語意不應改變；本輪只改 message list order。

## 非目標

- 不重設策略邏輯。
- 不改持倉 / 非持倉判斷。
- 不改買賣、加減碼、停損停利決策。
- 不改 DB schema、RLS、grant、policy、role、index / constraint。
- 不新增 DB write path。
- 不做 live Telegram delivery。
- 不清理全量報文 formatter。
- 不重構 Telegram pipeline。
- 不改 unrelated message content，除非版本字串需要同步到 v20.4.12。

## 影響模組

Tech 應只檢查並最小修改下列範圍：

- Telegram report formatter / message list builder。
- formatTelegramMessages 或等價產生 Telegram messages array 的函式。
- Telegram consumer 若目前依賴 message list index / type，需確認順序改動不破壞送出。
- 使用者可見版本字串 / report header 常量若存在，需同步為 v20.4.12。

不得擴大到策略 engine、DB persistence、production writer、live sender。

## 直接消費者

- Owner 手機 Telegram 閱讀路徑。
- Telegram message sender / consumer：依 formatter 產生的 messages list 逐則送出。
- QA fixture / test：可讀取完整 message list 並驗證 index order。

## 已存在且不得回退的契約

- v20.4.11 已能產生 intraday Telegram output。
- Message list 仍應包含原有持倉內容、非持倉內容、summary / evidence / strategy / source summary 內容。
- 每一檔股票的策略決策、狀態、理由與 evidence 不得因本輪排序修正改變。
- 無可買時仍不得用像推薦的文案；應維持既有「新倉：無有效進場」或等價不可買表述。
- 同一持倉在同一份報文仍只能有一個主行動。
- 不得新增假 evidence、假 source、假策略理由。
- 不得把 summary 拆到第一則或插在持倉與非持倉中間。

若 Tech 發現現有 message list 沒有可穩定區分「持倉 / 非持倉 / summary-evidence」的 type、section marker 或 content contract，應 blocked，要求 Architect 補充既有 formatter 契約，不得自行重設報文架構。

## 輸出契約

formatTelegramMessages 或等價函式回傳的 Telegram messages list 必須符合：

- 回傳型別維持既有型別，不因本輪改 shape。
- message payload 欄位維持既有欄位，不新增必填欄位。
- list order 固定為：
1. holdings message：包含持倉區塊 / 持倉處理 / current positions。
2. unheld message：包含非持倉 / 未持倉候選 / 新倉候選 / 僅追蹤 / 淘汰等非持倉內容。
3. summary evidence message：包含報文短訊、summary、evidence、strategy、source summary 或資料來源摘要。
- 若既有實作產生多於 3 則 message，所有 action body 類 message 必須在 summary / evidence 類 message 之前；summary / evidence / source 類 message 必須位於最後一組。
- Telegram consumer 應照 list order 送出，不得在 consumer 端重新把 summary 排到第一則。
- 使用者可見版本需同步為 v20.4.12，不得仍顯示 v20.4.11。

## 手機閱讀路徑

Owner 在 Telegram 手機端由上往下閱讀時，應看到：

[Message 1]
v20.4.12 ...
持倉 ...
- <持倉股票 A>：<主行動> ...
- <持倉股票 B>：<主行動> ...

[Message 2]
v20.4.12 ...
非持倉 ...
新倉：...
僅追蹤：...
淘汰 / 不可行動：...

[Message 3]
v20.4.12 ...
報文短訊 / Summary ...
Evidence ...
Strategy ...
Source summary ...

重點是 message order，不要求本輪改標題文案。

## 驗收條件

1. 使用同一個含「至少一個持倉」與「至少一個非持倉候選」的 sample / fixture 產生完整 Telegram message list，list 第一則為持倉 message，第二則為非持倉 message，最後一則為報文短訊 / summary / evidence / strategy / source
summary。
2. 驗證排序修正後，同一 sample 的策略決策內容不變：持倉主行動不新增、不消失、不互相衝突；非持倉候選不因排序修正變成可買 / 不可買相反結論。
3. 驗證使用者可見版本為 v20.4.12，且沒有仍顯示 v20.4.11 的 Telegram header / report version。
4. 驗證沒有 live Telegram delivery、沒有 DB schema/write、沒有 production write。

## 範例或 fixture

最小 fixture 形狀：

{
"version": "v20.4.12",
"holdings": [
{
"symbol": "HOLD1",
"action": "續抱",
"reason": "既有策略理由"
}
],
"unheld_candidates": [
{
"symbol": "NEW1",
"status": "僅追蹤",
"reason": "既有策略理由"
}
],
"summary": {
"short_message": "新倉：無有效進場；持倉先依既有主行動處理",
"evidence": ["既有 evidence"],
"strategy": "既有 strategy summary",
"source_summary": "既有 source summary"
}
}

預期 message list shape：

messages[0] => 持倉 / HOLD1 / 續抱
messages[1] => 非持倉 / NEW1 / 僅追蹤
messages[last] => 報文短訊或 Summary / Evidence / Strategy / Source summary

## 明確禁止事項

- 禁止改策略 decision。
- 禁止改 DB schema 或新增 DB write。
- 禁止 live Telegram send。
- 禁止用 mock summary 或假 evidence 補過測試。
- 禁止只驗單一 string 而不驗完整 message list order。
- 禁止把本輪擴成 formatter 全量重構。
- 禁止把 summary 保留在第一則。
- 禁止 Tech 直接宣告 QA 通過。

## 阻塞條件

- 找不到產生 Telegram message list 的穩定入口。
- 現有 formatter 無法區分 holdings / unheld / summary-evidence 類 message，且沒有可靠既有 marker 可用。
- 版本字串來源不明，無法確認 v20.4.12 是否會出現在實際 Telegram output。
- 測試環境無法產生含 holdings + unheld candidates 的完整 sample。
- 任何驗證需要 live Telegram 或 production write 才能完成。

## 本輪停止條件

完成到以下範圍即停止：

- v20.4.12 message list order 修正並有可重跑測試證明。
- sample 同時含持倉與非持倉，且完整 list order 符合 Owner 指定。
- QA 補充驗證無策略 / 顯示衝突、無假 evidence、無 live delivery / DB write。

以下旁支問題不納入本輪，若發現只記待辦：

- 報文文案是否要重新命名區塊。
- summary 內容是否要縮短。
- 候選策略是否合理。
- evidence source 是否要補強。
- Telegram 多訊息拆分規則是否要全面改版。
