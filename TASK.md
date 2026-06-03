# TASK: Telegram/report presentation/message list 降噪與簡報重構

## 任務狀態

- task_id: presentation_noise_reduction_v20_4_31
- 任務類型: normal_patch
- 狀態: done
- 版本建議: 優先保持 VERSION v20.4.31，不得因本輪調試期文案降噪自動 bump；若 Tech 判定使用者可見報文結構已超出既有版本契約，必須回報 Architect/Owner 決策後才可升版。
- QA 分級建議: L2
- 本輪主問題: Telegram/report presentation/message list 的重複、矛盾、偽推薦與手機閱讀噪音。

## Owner 問題

Owner 要解決的是：目前 Telegram/report 報文在盤中與盤後存在重複行、重複風控句、偽「追蹤最強」、逐卡無效歷史/回測資訊、資料依據過度展示，以及漏斗 B5 分類與卡片不一致，導致手機閱讀時誤以為有可買標的、同一資訊被多次提示，
或策略樣本狀態與卡片狀態矛盾。

本輪只收斂 presentation/message list 層的報文結構與降噪，不重設策略、不改交易決策。

## 使用者可見結果

手機閱讀 Telegram/report 時應看到：

- 第 1/2/3/4/5 項不再各自印出重複結論行。
- 市場與結論合併呈現；原因與風險合併呈現。
- 盤中與盤後共用同一個降噪函式，避免同樣內容在兩種報文漂移。
- 無有效進場時，不再出現像推薦的「追蹤最強」清單。
- 交易執行區不再重複完整風控檢查句，改為短文案。
- 卡片回測/歷史不可用時，不逐卡印不可用行。
- 資料依據正常時不顯示；盤中預設隱藏；完整版僅盤後顯示。
- 資料依據中的策略樣本狀態與卡片狀態一致。
- 漏斗 B5 的計數、拆分與卡片分類一致；「隔日確認」不得被合併進等冷卻。

## 非目標

- 不改 strategy decision。
- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path 或新增 production 寫入。
- 不做 live Telegram delivery。
- 不新增跨日持久化邏輯。
- 不改買賣、加減碼、停損停利決策。
- 不把本輪擴成全量報文重設或策略重構。
- 不清理無關模組與歷史檔案。

## 影響模組與直接消費者

影響模組：

- Telegram/report presentation renderer。
- message list builder。
- 盤中報文 formatter。
- 盤後報文 formatter。
- 卡片歷史/回測行 formatter。
- 資料依據 section renderer。
- 漏斗 B5 presentation/count mapper。
- 與上述 formatter 對應的可重跑 probe/test。

直接消費者：

- Owner 手機上的 Telegram 報文閱讀路徑。
- 盤中 report rendered message。
- 盤後 report rendered message。
- QA 使用的 rendered message snapshot/probe。
- 依賴 message list 順序與 section visibility 的既有 tests/probes。

## 輸出契約

### 報文整體契約

- 保持 VERSION v20.4.31，除非 Architect/Owner 另行批准升版。
- 盤中與盤後對重複 token、重複句、不可用歷史/回測行，必須使用同一個降噪函式或同一套 shared presentation helper。
- 降噪只能作用於 presentation/message text，不得改變 strategy decision payload 的原始判斷。
- 報文 section 順序可按 Owner 目標樣式重構，但不得製造新的推薦語意。

### 簡報第 1/2/3/4/5 項契約

- 刪除各項內重複結論行。
- 市場與結論合併為同一資訊單位。
- 原因與風險合併為同一資訊單位。
- 不同 section 不得重複同一句長文案。

示例形狀：

市場/結論：新倉無有效進場；持倉先依風控觀察。
原因/風險：量價未完成確認，隔日確認標的不列入等冷卻。

### 「追蹤最強」契約

- 無有效進場時，不顯示「追蹤最強」或任何像推薦第一名的清單。
- 若僅追蹤，必須明確標成「僅追蹤」或等價不可行動語意。
- 區塊內不得逐行重複 cross-day 提醒句；同一提醒最多集中顯示一次。

示例形狀：

新倉：無有效進場
僅追蹤：2330、2317（未達進場條件）

不得輸出：

追蹤最強：2330
2330：跨日追蹤，尚未進場
2317：跨日追蹤，尚未進場

### 交易執行契約

- 不重複完整風控檢查整句。
- 同一份報文中，同一風控意義使用短文案表示。
- 不改變任何交易行動主結論。

示例形狀：

交易執行：無新增下單；持倉照警戒價觀察。
風控：已檢查

### 卡片回測/歷史行契約

- 回測/歷史不可用時，不得逐卡印 不可用、無資料、N/A 類行。
- 歷史行需去除重複 token。
- 盤中卡片也套用盤後相同降噪規則。
- 若歷史/回測可用，仍可保留精簡後的單行資訊。

示例形狀：

2330｜狀態：僅追蹤｜原因/風險：量能未確認

不得輸出：

2330｜回測：不可用｜歷史：不可用｜歷史：不可用

### 資料依據契約

- 正常資料源不顯示資料依據 section。
- 盤中預設隱藏資料依據。
- 完整版資料依據僅盤後顯示。
- 僅在資料異常、source-error、missing-source、insufficient-data 或等價異常狀態時觸發顯示。
- 資料依據中的策略樣本狀態必須與卡片狀態一致；依賴 version filter 修復 M1 後的結構狀態，不得自行推導另一套狀態。

示例形狀：

資料依據：source-error，部分策略樣本未納入行動判斷。

### 漏斗 B5 契約

- B5 拆分計數與卡片分類必須一致。
- 「隔日確認」必須獨立呈現或歸入正確分類，不得併入「等冷卻」。
- 漏斗 count 與實際卡片列表數量需可由 probe 驗證。

示例形狀：

B5：等冷卻 2｜隔日確認 1
卡片分類：等冷卻 2 張；隔日確認 1 張

## 版本契約

已存在且不得回退的契約：

- VERSION v20.4.31 預設保持不變。
- 無可買時不得使用像推薦的文案；只能寫「新倉：無有效進場」或等價不可買表述。
- 可買、可準備、僅追蹤、淘汰/不可行動必須分開。
- 同一持倉在同一份報文只能有一個主行動。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 使用者可見版本與實際 header/常量必須一致。
- 盤中與盤後都需經 rendered message 手機閱讀路徑檢查。

不確定但需 Tech 先盤點後遵守：

- 現有 message list 的完整 section 順序。
- 既有 renderer 對「完整版」與「盤後」的觸發條件。
- M1 version filter 修復後暴露的策略樣本狀態欄位名稱與來源。

若上述不確定項無法從 repo 現有 contract/probe 確認，Tech 必須 blocked，不得猜測。

## 驗收條件

- 每一項 Owner 指定修正都先補可重跑 probe/test，再實作。
- 盤中 rendered message 通過手機閱讀檢查：無偽推薦、無重複長句、資料依據預設隱藏、卡片無逐卡不可用歷史/回測行。
- 盤後 rendered message 通過手機閱讀檢查：完整版資料依據只在盤後且符合異常觸發規則；正常源不顯示。
- 無有效進場 fixture 中，不得出現「追蹤最強」或等價偽推薦標題。
- 交易執行 fixture 中，完整風控檢查句不得重複出現；短文案可出現一次。
- 卡片歷史/回測不可用 fixture 中，不得逐卡印不可用行，且歷史 token 去重。
- 資料依據策略樣本狀態與同標的卡片狀態一致。
- B5 fixture 中，等冷卻與隔日確認 count 與卡片分類一致，隔日確認不併入等冷卻。
- VERSION v20.4.31 header/constant/rendered message 三者一致。
- QA 必須補至少一個 Tech 未覆蓋的反證案例，且同時覆蓋盤中與盤後 rendered message。

## 範例或 Fixture

Tech 至少建立或更新以下可重跑 fixtures/probes：

- intraday_no_valid_entry: 盤中，無有效進場，有追蹤標的；預期不顯示「追蹤最強」，資料依據隱藏。
- afterhours_no_valid_entry_full: 盤後完整版，無有效進場；正常源不顯示資料依據。
- afterhours_source_error: 盤後完整版，source-error 或 missing-source；預期顯示資料依據異常短訊。
- execution_risk_dedupe: 有交易執行區與風控檢查；預期完整風控句不重複。
- card_history_unavailable: 多張卡片回測/歷史不可用；預期不逐卡印不可用行，歷史 token 去重。
- b5_split_counts: 等冷卻與隔日確認同時存在；預期 count 與卡片分類一致。
- sample_status_consistency: 資料依據策略樣本狀態與同標的卡片狀態一致。

手機閱讀示例輸出形狀：

v20.4.31

市場/結論：新倉無有效進場；持倉先依風控觀察。
原因/風險：量價未確認，隔日確認不列入等冷卻。

新倉：無有效進場
僅追蹤：2330、2317

交易執行：無新增下單；持倉照警戒價觀察。
風控：已檢查

B5：等冷卻 2｜隔日確認 1

## 明確禁止事項

- 禁止改 strategy decision。
- 禁止改 RR 公式。
- 禁止改 DB schema/write path。
- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 禁止用 local cache、runtime dict、agent 對話當跨日 source-of-truth。
- 禁止把無有效進場標的包裝成「追蹤最強」或任何像推薦的排名。
- 禁止只改文案不補 probe/test。
- 禁止只驗單一路徑後宣告盤中/盤後都完成。
- 禁止 bump version，除非 Architect/Owner 明確批准。
- 禁止讓盤中與盤後各自維護不同降噪規則。
- 禁止將隔日確認併入等冷卻。
- 禁止 QA 只重跑 Tech 命令而不做手機閱讀與反證檢查。

## 阻塞條件

- 找不到現有 rendered message 產生路徑，無法建立盤中/盤後 probe。
- 找不到 VERSION v20.4.31 的 header/constant/rendered message 對應關係。
- 找不到 M1 version filter 修復後的策略樣本狀態來源，無法保證資料依據與卡片一致。
- 現有 report renderer 無法區分盤中、盤後、完整版或資料異常狀態。
- 需求需要 DB schema/write、策略 decision 或 RR 公式改動才可完成。
- 測試環境缺失且補環境後仍無法重跑 probe/test。
- 任一資料來源缺失卻仍要求顯示正常結論。

## 本輪停止條件

完成範圍到以下為止：

- presentation/message list 層完成 Owner 七項降噪與矛盾修正。
- 盤中與盤後 rendered message 均有可重跑 probe/test 覆蓋。
- QA L2 通過，且至少補一個直接消費者或手機閱讀反證案例。
- VERSION v20.4.31 未回退且未擅自升版。
- 無 strategy decision、RR、DB schema/write、live Telegram 變更。

以下旁支問題只記待辦，不納入本輪：

- 新策略分類或買賣規則調整。
- RR 公式品質問題。
- DB source-of-truth 補欄位或 backfill。
- 全量 Telegram template 重設。
- 歷史 fixtures 大規模清理。
- live Telegram 發送驗證。
