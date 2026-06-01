# TASK: v20.4.17 第三則「資料依據」改為人話可靠度與用途說明

## 任務狀態

- task_id: telegram-evidence-human-readable-v20.4.17
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: v20.4.17
- QA 分級建議: L2
- 本輪主 bug: 第三則 Telegram「資料依據」仍輸出工程語、表名、欄位狀態與 raw timestamp，導致 Owner 手機閱讀時無法直接理解資料可靠度與策略用途。

## Owner 問題

Owner 指出 v20.4.16 第三則「資料依據」仍出現工程語與 raw metadata，例如：

- production DB
- classification backtest
- source-of-truth
- available
- derived
- as_of
- ISO timestamp

Owner 不需要表名、來源欄位狀態或工程語。第三則應改成人話回答：

- 證據源是否可靠。
- 資料對策略判斷是否有用。
- 可靠度與限制是什麼。
- 哪些資料只能作背景，不能當買點。
- 哪些樣本不足或缺來源時本輪不採用，必須 fail-closed。

## 使用者可見結果

Telegram 三則報文仍維持既有閱讀路徑；本輪只改第三則「資料依據」的人話內容與版本字串。

手機閱讀路徑：

1. Owner 在手機 Telegram 依序收到完整三則報文。
2. 第一則、第二則的策略決策、持倉、候選分類與行動語意不得因本任務改變。
3. 第三則標題仍是「資料依據」或既有等價標題。
4. 第三則不再顯示工程來源名、表名、欄位狀態、raw timestamp。
5. 第三則用簡短人話說明資料可靠度、用途與限制。

## 非目標

- 不改任何策略 decision。
- 不改買入、賣出、加碼、減碼、停損、停利、觀察等行動判斷。
- 不改候選分類邏輯。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path。
- 不新增或改 live Telegram delivery。
- 不做全量報文重設、策略重寫、資料管線重構。
- 不擴大清理其他報文區塊。
- 不把 market/theme 背景資訊升格成買點。
- 不因 strategy sample 不可用而補猜策略判斷。

## 影響模組

Tech 需在 repo 中定位實際第三則 Telegram「資料依據」生成位置後，只修改必要範圍。預期影響面：

- Telegram 三則報文的第三則內容 formatter / renderer。
- 報文版本字串或常量：升為 v20.4.17。
- 相關 sample / snapshot / fixture 測試。
- 必要時只更新對應測試 fixture，不改策略計算核心。

## 直接消費者

- Owner 手機 Telegram 閱讀者。
- Telegram report renderer 的三則訊息輸出。
- 現有 dry-run / sample generator / tests 中消費三則 Telegram message list 的測試或工具。
- QA 驗收用完整三則 Telegram sample。

## 已存在且不得回退的契約

- 維持完整三則 Telegram 報文輸出，不得合併、刪除或改變三則主體順序。
- 第三則仍承擔「資料依據」用途，不得移到第一則或第二則。
- 第一則、第二則既有策略決策、分組、排序、候選分類與行動文案不得因本任務回退。
- 無可買時不得出現像推薦的文案；既有「新倉無有效進場」類不可買語意不得回退。
- market/theme 資料只能作背景或環境說明，不得變成買點或推薦理由。
- strategy sample 缺來源或樣本不足時必須 fail-closed，不得進入策略判斷。
- 使用者可見版本不得停留在 v20.4.16；本輪需升為 v20.4.17。
- 不確定的既有契約不得自行假設；若會影響三則報文結構或策略 decision，Tech 必須 blocked 並回報 Architect 補充。

## 輸出契約

第三則「資料依據」輸出應包含三類人話說明，順序建議如下：

1. 市場 / 題材背景
- 說明近幾個交易證據日是否支持目前背景判斷。
- 說明可靠度。
- 明確說明用途限背景，不等於買點。
2. 策略樣本
- 若缺 source、樣本不足、資料不足或可信度不足，輸出「本輪不採用」。
- 說明可靠度低或不可用。
- 必須 fail-closed，不得暗示已納入判斷。
3. 持倉 / 價格 / 候選資料
- 若資料足夠，說明可支持風控、持倉檢查或候選分類。
- 若缺資料，說明限制與本輪如何保守處理。
- 不輸出 raw 狀態字、表名、來源名、欄位名或 timestamp。

第三則不得輸出以下 raw 語彙或等價工程語：

- production DB
- classification backtest
- source-of-truth
- available
- derived
- as_of
- ISO timestamp，例如 2026-06-01T...
- raw table name
- raw source/status field name

允許輸出的人話示例形狀：

📌 資料依據

市場 / 題材背景：
近幾個交易證據日仍支持目前的背景觀察，可靠度中等；這只用來理解環境，不等於買點。

策略樣本：
本輪樣本來源不足，可靠度低，未納入買賣判斷。

持倉 / 價格 / 候選資料：
持倉與價格資料可支持風控檢查；候選資料可支持分類，但缺資料的標的會保守處理，不作有效進場。

若資料不足的人話示例形狀：

📌 資料依據

市場 / 題材背景：
近幾個交易證據日不足以形成可靠背景，只作觀察，不作買點。

策略樣本：
本輪缺少可驗證樣本，可靠度低，未納入判斷。

持倉 / 價格 / 候選資料：
部分持倉或候選資料不足，只能支持有限風控檢查；缺資料標的本輪不給進場結論。

## 驗收條件

1. 版本與三則報文
- 完整三則 Telegram sample 可產生。
- 使用者可見版本為 v20.4.17。
- 第三則仍是「資料依據」用途。
- 第一則、第二則策略 decision、持倉行動與候選分類不因本任務改變。
2. 第三則禁用 raw 語彙
- QA 必須用完整三則 Telegram sample 檢查第三則。
- 第三則不得包含：
- production DB
- classification backtest
- source-of-truth
- available
- derived
- as_of
- ISO timestamp
- raw table/source/status/timestamp 類工程語
3. market/theme 語意
- 第三則需說明近幾個交易證據日是否支持背景。
- 需說明可靠度與限制。
- 需明確呈現用途限背景，不等於買點。
- 不得讓 market/theme 看起來像推薦理由或有效進場條件。
4. strategy sample fail-closed
- 缺 source、樣本不足或不可驗證時，第三則需說明「本輪不採用」或等價語意。
- 需說明可靠度低 / 不可用。
- 第一則、第二則不得因不可用 strategy sample 產生買賣判斷。
5. 持倉 / 候選資料
- 資料可用時，第三則需說明可支持風控 / 候選分類。
- 資料不足時，需說明限制與保守處理。
- 不得輸出 available、derived、source-of-truth 或 raw source/status。

## 範例或 fixture

Tech 至少提供 1 個完整三則 Telegram sample fixture，覆蓋：

- market/theme 有近幾個交易證據日支持，但只作背景。
- strategy sample 缺 source 或樣本不足，第三則顯示本輪不採用。
- 持倉 / 價格 / 候選資料可支持風控或分類。
- 第三則不含 raw 工程語。

QA 需另補一個負面檢查或反證路徑：

- 對第三則做 forbidden-term scan。
- 檢查 ISO timestamp pattern。
- 檢查 strategy sample 不可用時不進入買賣判斷。
- 檢查 market/theme 沒被寫成買點。

## 明確禁止事項

- 禁止改策略 decision。
- 禁止改 DB schema / write path。
- 禁止 live Telegram delivery。
- 禁止把 raw table name、source/status 欄位、timestamp 搬到別的區塊。
- 禁止只改英文詞為中文工程詞，仍讓 Owner 看到資料庫、表名、欄位狀態。
- 禁止把資料不足寫成可用。
- 禁止把 market/theme 背景寫成可買理由。
- 禁止 strategy sample 不可靠時仍納入判斷。
- 禁止擴大成全報文重構或策略重設。

## 阻塞條件

Tech 必須 blocked 並回報 Architect，如果出現以下情況：

- 無法定位第三則「資料依據」生成位置。
- 版本字串來源不明，可能造成 v20.4.16 / v20.4.17 不一致。
- 修改第三則必須同步改策略 decision 才能通過測試。
- 現有 sample generator 無法產生完整三則 Telegram sample，且無可替代 fixture。
- 無法判斷某些 raw 欄位是否仍被下游直接消費。
- 測試環境缺依賴且無法補齊，導致不能驗完整 sample。

## 本輪停止條件

驗到以下範圍即算本輪完成：

- 完整三則 Telegram sample 可產生。
- 第三則「資料依據」已改為人話可靠度與用途說明。
- 第三則 forbidden raw 語彙與 ISO timestamp scan 通過。
- v20.4.17 版本可見。
- market/theme 只作背景、strategy sample 不可用 fail-closed、持倉 / 候選資料用途說明成立。
- QA L2 針對完整三則 sample 做至少一個 Tech 未覆蓋的反證檢查。

以下旁支問題不納入本輪，若發現只記入後續待辦：

- 其他報文區塊文案優化。
- 候選分類策略調整。
- 歷史資料補齊。
- DB source-of-truth 設計。
- Telegram delivery runner 改造。
- 全量 snapshot 重建。
